"""
Funcții pentru renderizarea și trimiterea email-urilor din EmailOutbox.

Acest modul procesează mesajele din coada EmailOutbox și le trimite efectiv.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import EmailOutbox, EmailDelivery

logger = logging.getLogger(__name__)


def render_email_template(outbox: EmailOutbox) -> tuple[str, str]:
    """
    Renderizează template-ul HTML și text pentru un mesaj din outbox.
    
    Args:
        outbox: instanță EmailOutbox cu template, locale și context
        
    Returns:
        tuple: (html_content, text_content) - conținutul renderizat
        
    Raises:
        Exception: dacă template-ul nu poate fi găsit sau renderizat
    """
    template_name = outbox.template
    locale = outbox.locale
    context = outbox.context
    
    # Căutăm template-urile în: templates/emails/{locale}/{template_name}.html și .txt
    html_template_path = f"emails/{locale}/{template_name}.html"
    text_template_path = f"emails/{locale}/{template_name}.txt"
    
    try:
        html_content = render_to_string(html_template_path, context)
        text_content = render_to_string(text_template_path, context)
        return html_content, text_content
    except Exception as e:
        logger.error(
            f"Eroare la renderizarea template-ului pentru outbox {outbox.id}: {e}",
            exc_info=True
        )
        raise


def send_email_from_outbox(outbox: EmailOutbox) -> bool:
    """
    Trimite un email din outbox folosind Django's email backend.
    
    Args:
        outbox: instanță EmailOutbox de procesat
        
    Returns:
        bool: True dacă email-ul a fost trimis cu succes, False altfel
    """
    try:
        # Renderizează template-urile
        html_content, text_content = render_email_template(outbox)
        
        # Creează mesajul email
        subject = _get_email_subject(outbox.template)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # Versiunea text (pentru clienți care nu suportă HTML)
            from_email=from_email,
            to=[outbox.to],
        )
        msg.attach_alternative(html_content, "text/html")  # Versiunea HTML
        
        # Trimite email-ul
        msg.send()
        
        logger.info(f"Email trimis cu succes către {outbox.to} (outbox_id={outbox.id})")
        return True
        
    except Exception as e:
        logger.error(
            f"Eroare la trimiterea email-ului pentru outbox {outbox.id}: {e}",
            exc_info=True
        )
        return False


def _get_email_subject(template_name: str) -> str:
    """
    Returnează subiectul email-ului în funcție de tipul de template.
    
    Args:
        template_name: numele template-ului (ex: 'appointment_summary')
        
    Returns:
        str: subiectul email-ului
    """
    subjects = {
        'appointment_summary': 'Rezumat Programare - Molson Coors',
        'request_status': 'Status Cerere Rezervare - Molson Coors',
        'desk_release_ask': 'Cerere de Eliberare Birou - Molson Coors',
    }
    return subjects.get(template_name, 'Notificare - Molson Coors')


@transaction.atomic
def process_outbox_message(outbox: EmailOutbox, max_attempts: int = 3) -> bool:
    """
    Procesează un mesaj din outbox: încearcă să-l trimită și actualizează statusul.
    
    Args:
        outbox: instanță EmailOutbox de procesat
        max_attempts: numărul maxim de încercări înainte de a marca ca eșuat
        
    Returns:
        bool: True dacă a fost trimis cu succes, False altfel
    """
    # Verifică dacă mesajul a fost deja trimis
    if outbox.sent_at:
        logger.debug(f"Outbox {outbox.id} a fost deja trimis la {outbox.sent_at}")
        return True
    
    # Verifică dacă a depășit numărul maxim de încercări
    if outbox.attempts >= max_attempts:
        logger.warning(
            f"Outbox {outbox.id} a depășit numărul maxim de încercări ({max_attempts})"
        )
        # Marchează ca eșuat definitiv
        outbox.error = f"Depășit numărul maxim de încercări ({max_attempts})"
        outbox.save(update_fields=['error'])
        return False
    
    # Blochează mesajul pentru procesare (pentru a evita procesarea paralelă)
    if outbox.locked_at:
        # Verifică dacă lock-ul a expirat (ex: mai mult de 10 minute)
        lock_age = timezone.now() - outbox.locked_at
        if lock_age.total_seconds() < 600:  # 10 minute
            logger.debug(f"Outbox {outbox.id} este deja blocat")
            return False
        # Lock-ul a expirat, continuăm procesarea
    
    # Blochează mesajul
    outbox.locked_at = timezone.now()
    outbox.attempts += 1
    outbox.save(update_fields=['locked_at', 'attempts'])
    
    try:
        # Încearcă să trimită email-ul
        success = send_email_from_outbox(outbox)
        
        if success:
            # Marchează ca trimis
            outbox.sent_at = timezone.now()
            outbox.locked_at = None
            outbox.error = ""
            outbox.save(update_fields=['sent_at', 'locked_at', 'error'])
            
            # Creează înregistrare de delivery pentru audit
            EmailDelivery.objects.create(
                outbox=outbox,
                status='SENT',
                provider_message_id='',  # Poate fi completat dacă folosești un provider extern
            )
            
            return True
        else:
            # Eroare la trimitere
            outbox.error = "Eroare la trimiterea email-ului"
            outbox.locked_at = None  # Deblochează pentru a permite reîncercarea
            outbox.save(update_fields=['error', 'locked_at'])
            
            return False
            
    except Exception as e:
        # Eroare neașteptată
        outbox.error = str(e)
        outbox.locked_at = None
        outbox.save(update_fields=['error', 'locked_at'])
        logger.error(f"Eroare neașteptată la procesarea outbox {outbox.id}: {e}", exc_info=True)
        return False

