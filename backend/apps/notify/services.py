"""
Servicii pentru crearea evenimentelor de notificare și adăugarea lor în outbox.

Aceste funcții sunt apelate din logica de business (ex: când se creează un Appointment)
pentru a declanșa notificările prin email.
"""
import hashlib
from django.utils import timezone
from django.db import transaction

from .models import (
    NotificationEvent,
    EmailOutbox,
    NotificationType,
    UserEmailPreference,
)


def _idempotency(event_id: str, to: str, template: str) -> str:
    """
    Generează o cheie unică pentru a preveni duplicate-urile.
    
    Dacă apelăm aceeași funcție de 2 ori cu aceiași parametri,
    idempotency_key va fi același, deci get_or_create nu va crea
    un al doilea mesaj în outbox.
    
    Ex: dacă creăm Appointment și apoi din greșeală apelăm din nou
    notify_appointment_summary, nu vom trimite email-ul de 2 ori.
    """
    key_string = f"{event_id}:{to}:{template}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def _want(user, field_name: str) -> bool:
    """
    Verifică dacă user-ul vrea să primească acest tip de notificare.
    
    Dacă user-ul nu are preferințe setate, returnăm True (implicit on).
    Dacă are preferințe, verificăm câmpul specific (ex: appointment_summary).
    """
    try:
        prefs = user.email_prefs
    except UserEmailPreference.DoesNotExist:
        # Dacă nu are preferințe, implicit vrea notificări
        return True
    
    return getattr(prefs, field_name, True)


@transaction.atomic
def notify_appointment_summary(appointment):
    """
    Creează un eveniment și un mesaj în outbox pentru rezumatul unei programări.
    
    Apelat după ce se creează un Appointment cu succes.
    
    Args:
        appointment: instanță Appointment (trebuie să aibă user, item, item.room)
    """
    user = appointment.user
    
    # Verifică dacă user-ul vrea acest tip de notificare
    if not _want(user, "appointment_summary"):
        return  # User-ul a dezactivat notificările pentru appointment summary
    
    # Creează evenimentul (immutable, pentru audit)
    event = NotificationEvent.objects.create(
        type=NotificationType.APPOINTMENT_SUMMARY,
        actor=None,  # Nu există un actor care să declanșeze (e automat)
        subject_user=user,
        payload={
            "appointment_id": appointment.id,
            "item_id": appointment.item.id,
            "room_id": appointment.item.room.id,
        }
    )
    
    # Pregătește context-ul pentru template
    # Aceste variabile vor fi disponibile în template ca {{ user.first_name }}, etc.
    context = {
        "user": {
            "first_name": user.first_name or user.username,
            "last_name": user.last_name or "",
        },
        "item": {
            "name": appointment.item.name,
            "category": appointment.item.category.name if appointment.item.category else "",
        },
        "room": {
            "code": appointment.item.room.code,
            "name": appointment.item.room.name,
        },
        "start_at": appointment.start_at.strftime('%d.%m.%Y %H:%M'),
        "end_at": appointment.end_at.strftime('%d.%m.%Y %H:%M'),
        "start_at_iso": appointment.start_at.isoformat(),  # Pentru compatibilitate
        "end_at_iso": appointment.end_at.isoformat(),  # Pentru compatibilitate
    }
    
    # Creează mesajul în outbox (sau îl găsește dacă există deja - idempotency)
    EmailOutbox.objects.get_or_create(
        idempotency_key=_idempotency(str(event.id), user.email, "appointment_summary"),
        defaults={
            "event": event,
            "to": user.email,
            "template": "appointment_summary",
            "locale": "ro",
            "context": context,
            "scheduled_at": timezone.now(),
        }
    )


@transaction.atomic
def notify_request_status(request_obj):
    """
    Creează un eveniment și un mesaj în outbox când se schimbă statusul unei cereri.
    
    Apelat când o Request trece din WAITING în APPROVED sau DISMISSED.
    
    Args:
        request_obj: instanță Request (trebuie să aibă user, room, status, decided_by)
    """
    user = request_obj.user
    
    # Verifică preferințele
    if not _want(user, "request_status"):
        return
    
    # Actor = cine a aprobat/respins cererea (ex: SUPERADMIN)
    actor = request_obj.decided_by if request_obj.decided_by else None
    
    # Creează evenimentul
    event = NotificationEvent.objects.create(
        type=NotificationType.REQUEST_STATUS,
        actor=actor,
        subject_user=user,
        payload={
            "request_id": request_obj.id,
            "status": request_obj.status,
            "room_id": request_obj.room.id,
        }
    )
    
    # Context pentru template
    context = {
        "user": {
            "first_name": user.first_name or user.username,
            "last_name": user.last_name or "",
        },
        "room": {
            "code": request_obj.room.code,
            "name": request_obj.room.name,
        },
        "status": request_obj.status,
        "status_display": request_obj.get_status_display() if hasattr(request_obj, 'get_status_display') else request_obj.status,
        "note": request_obj.note or "",
        "decided_by": actor.get_full_name() if actor else "Sistem",
    }
    
    # Creează mesajul în outbox
    EmailOutbox.objects.get_or_create(
        idempotency_key=_idempotency(str(event.id), user.email, "request_status"),
        defaults={
            "event": event,
            "to": user.email,
            "template": "request_status",
            "locale": "ro",
            "context": context,
            "scheduled_at": timezone.now(),
        }
    )


@transaction.atomic
def notify_desk_release_batch(date_obj, overquota_users, requester_user):
    """
    Creează evenimente și mesaje în outbox pentru cererea de eliberare birou.
    
    Apelat după ce se calculează lista de utilizatori over-quota.
    Trimite email fiecărui user care are birou rezervat și a atins deja norma.
    
    Args:
        date_obj: date object - data pentru care se cere eliberarea
        overquota_users: list de dict-uri cu informații despre useri (din desk_overquota)
        requester_user: User - user-ul care cere eliberarea (cel care nu găsește birou)
    """
    for user_data in overquota_users:
        user_id = user_data.get('user_id')
        if not user_id:
            continue
        
        # Importăm aici pentru a evita circular imports
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            continue
        
        # Verifică preferințele
        if not _want(user, "desk_release_ask"):
            continue  # User-ul nu vrea notificări pentru eliberare birou
        
        # Creează evenimentul
        event = NotificationEvent.objects.create(
            type=NotificationType.DESK_RELEASE_ASK,
            actor=requester_user,  # Cine cere eliberarea
            subject_user=user,  # Cine trebuie să elibereze
            payload={
                "date": date_obj.isoformat(),
                "requester_id": requester_user.id,
            }
        )
        
        # Context pentru template
        context = {
            "user": {
                "first_name": user.first_name or user.username,
                "last_name": user.last_name or "",
            },
            "date": date_obj.strftime('%d.%m.%Y'),  # Format mai prietenos: 15.01.2024
            "requester": {
                "first_name": requester_user.first_name or requester_user.username,
                "last_name": requester_user.last_name or "",
                "email": requester_user.email,
            },
            "appointments": user_data.get('appointments_on_date', []),
        }
        
        # Creează mesajul în outbox
        EmailOutbox.objects.get_or_create(
            idempotency_key=_idempotency(str(event.id), user.email, "desk_release_ask"),
            defaults={
                "event": event,
                "to": user.email,
                "template": "desk_release_ask",
                "locale": "ro",
                "context": context,
                "scheduled_at": timezone.now(),
            }
        )

