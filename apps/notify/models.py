"""
Modele pentru sistemul de notificări prin email.

Arhitectură:
1. NotificationEvent - evenimentul brut produs de business (immutable)
2. EmailOutbox - coadă tranzacțională pentru email-uri de trimis
3. EmailDelivery - audit final pentru livrare
4. UserEmailPreference - preferințe per user (on/off per tip + frecvență)
"""
import uuid
import hashlib
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NotificationType(models.TextChoices):
    """
    Tipurile de notificări disponibile în sistem.
    
    APPOINTMENT_SUMMARY: Email trimis când se creează o programare nouă
    REQUEST_STATUS: Email trimis când se schimbă statusul unei cereri
    DESK_RELEASE_ASK: Email trimis când se cere eliberarea unui birou
    """
    APPOINTMENT_SUMMARY = "APPOINTMENT_SUMMARY", "Appointment summary"
    REQUEST_STATUS = "REQUEST_STATUS", "Request status changed"
    DESK_RELEASE_ASK = "DESK_RELEASE_ASK", "Ask to release desk"


class NotificationEvent(models.Model):
    """
    Evenimentul brut produs de business logic (immutable).
    
    Acest model stochează ce s-a întâmplat în sistem (ex: s-a creat o programare).
    Este immutable - odată creat, nu se modifică. Servește ca sursă de adevăr
    pentru audit și pentru a regenera email-uri dacă e nevoie.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=64, choices=NotificationType.choices)
    
    # Actor = cine a declanșat evenimentul (ex: SUPERADMIN care aprobă cererea)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events_actor",
        help_text="Utilizatorul care a declanșat evenimentul"
    )
    
    # Subject = pentru cine este notificarea (ex: user-ul care a creat programarea)
    subject_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events_subject",
        help_text="Utilizatorul pentru care este notificarea"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    
    # JSON minimal cu datele necesare pentru template
    # Ex: {"appointment_id": 123, "room_code": "A101"}
    payload = models.JSONField(default=dict)

    class Meta:
        db_table = 'notify_notification_event'
        verbose_name = 'Notification Event'
        verbose_name_plural = 'Notification Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['subject_user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.type} for {self.subject_user} at {self.created_at}"


class EmailOutbox(models.Model):
    """
    Mesaje programate de trimis (transactional outbox pattern).
    
    Acest model este coada noastră de email-uri. Când vrem să trimitem un email,
    creăm un rând aici. Un worker (Celery) procesează periodic aceste mesaje
    și le trimite efectiv.
    
    Pattern-ul "transactional outbox" asigură că:
    - Dacă creăm un NotificationEvent în aceeași tranzacție cu un Appointment,
      și creăm și EmailOutbox, ambele se salvează sau niciunul (ACID)
    - Dacă aplicația cade după ce salvăm Event dar înainte de a trimite email,
      worker-ul va prelua mesajul când pornește din nou
    """
    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        NotificationEvent,
        on_delete=models.CASCADE,
        related_name="outbox",
        help_text="Evenimentul care a generat acest email"
    )
    
    to = models.EmailField(help_text="Adresa de email destinatar")
    template = models.CharField(
        max_length=64,
        help_text="Numele template-ului (ex: 'appointment_summary')"
    )
    locale = models.CharField(
        max_length=8,
        default="ro",
        help_text="Limba pentru template (ex: 'ro', 'en')"
    )
    
    # Context-ul pentru template (variabilele care se înlocuiesc în template)
    # Ex: {"user": {"first_name": "Ion"}, "item": {"name": "DESK-001"}}
    context = models.JSONField(default=dict)
    
    # Cheie unică pentru a preveni duplicate-urile (idempotency)
    # Calculată ca hash(event_id + to + template)
    idempotency_key = models.CharField(
        max_length=64,
        db_index=True,
        unique=True,
        help_text="Cheie unică pentru a preveni trimiterea duplicată"
    )
    
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        help_text="Când ar trebui trimis email-ul"
    )
    
    attempts = models.PositiveSmallIntegerField(
        default=0,
        help_text="Numărul de încercări de trimitere"
    )
    
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Când a fost blocat pentru procesare (pentru a evita procesarea paralelă)"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Când a fost trimis cu succes (null = încă neprocesat)"
    )
    
    error = models.TextField(
        blank=True,
        default="",
        help_text="Mesaj de eroare dacă trimiterea a eșuat"
    )

    class Meta:
        db_table = 'notify_email_outbox'
        verbose_name = 'Email Outbox'
        verbose_name_plural = 'Email Outbox'
        ordering = ['scheduled_at', 'id']
        indexes = [
            models.Index(fields=['sent_at', 'scheduled_at']),
            models.Index(fields=['idempotency_key']),
        ]

    def __str__(self):
        return f"Email to {self.to} ({self.template}) - {'Sent' if self.sent_at else 'Pending'}"


class EmailDelivery(models.Model):
    """
    Audit final pentru livrare (pentru trasabilitate și debugging).
    
    După ce un email este trimis cu succes sau eșuează definitiv,
    creăm un rând aici pentru a ține evidența. Acest model ne permite să:
    - Vedem istoricul complet al trimiterilor
    - Debugăm probleme (ce mesaj a returnat provider-ul?)
    - Raportăm statistici (câte email-uri au fost trimise?)
    """
    outbox = models.OneToOneField(
        EmailOutbox,
        on_delete=models.CASCADE,
        related_name="delivery",
        help_text="Mesajul din outbox pentru care este această livrare"
    )
    
    provider_message_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="ID-ul mesajului de la provider (ex: SendGrid message_id)"
    )
    
    status = models.CharField(
        max_length=16,
        default="SENT",
        help_text="Status: SENT sau FAILED"
    )
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notify_email_delivery'
        verbose_name = 'Email Delivery'
        verbose_name_plural = 'Email Deliveries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Delivery for {self.outbox.to} - {self.status}"


class UserEmailPreference(models.Model):
    """
    Preferințe per user pentru notificări (on/off per tip + frecvență).
    
    Permite fiecărui user să controleze ce notificări primește și când.
    """
    INSTANT = "instant"
    DAILY = "daily"
    FREQ_CHOICES = [
        (INSTANT, "Instant"),
        (DAILY, "Daily digest"),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="email_prefs",
        help_text="Utilizatorul pentru care sunt aceste preferințe"
    )
    
    # On/off per tip de notificare
    appointment_summary = models.BooleanField(
        default=True,
        help_text="Primește email când creează o programare?"
    )
    request_status = models.BooleanField(
        default=True,
        help_text="Primește email când se schimbă statusul unei cereri?"
    )
    desk_release_ask = models.BooleanField(
        default=True,
        help_text="Primește email când i se cere să elibereze biroul?"
    )
    
    # Frecvența: instant (imediat) sau daily (digest zilnic la ora 18:00)
    frequency = models.CharField(
        max_length=16,
        choices=FREQ_CHOICES,
        default=INSTANT,
        help_text="Frecvența notificărilor"
    )

    class Meta:
        db_table = 'notify_user_email_preference'
        verbose_name = 'User Email Preference'
        verbose_name_plural = 'User Email Preferences'

    def __str__(self):
        return f"Email prefs for {self.user.username}"
