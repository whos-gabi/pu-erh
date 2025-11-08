"""
Celery tasks pentru procesarea notificărilor prin email.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from .models import EmailOutbox
from .email_sender import process_outbox_message

logger = logging.getLogger(__name__)


@shared_task(name='notify.process_email_queue', bind=True)
def process_email_queue(self, batch_size=50, max_messages=None):
    """
    Task Celery pentru procesarea cozii de email-uri.
    
    Acest task rulează periodic (configurat în beat schedule) și procesează
    mesajele din EmailOutbox care nu au fost încă trimise.
    
    Args:
        batch_size: Numărul de mesaje de procesat într-un batch (default: 50)
        max_messages: Numărul maxim de mesaje de procesat (default: toate)
    
    Returns:
        dict: Rezumat cu numărul de mesaje procesate, trimise și eșuate
    """
    now = timezone.now()
    
    # Query pentru mesaje de procesat
    pending_query = Q(sent_at__isnull=True) & Q(scheduled_at__lte=now)
    
    # Exclude mesajele care sunt blocate recent (lock-ul nu a expirat)
    # Lock-ul expiră după 10 minute
    lock_expiry = now - timezone.timedelta(minutes=10)
    pending_query &= (
        Q(locked_at__isnull=True) | 
        Q(locked_at__lt=lock_expiry)
    )
    
    pending_messages = EmailOutbox.objects.filter(pending_query).order_by('scheduled_at', 'id')
    
    if max_messages:
        pending_messages = pending_messages[:max_messages]
    
    total_count = pending_messages.count()
    
    if total_count == 0:
        logger.info('Nu există mesaje de procesat')
        return {
            'processed': 0,
            'sent': 0,
            'failed': 0,
            'total': 0
        }
    
    logger.info(f'Găsite {total_count} mesaje de procesat')
    
    processed = 0
    sent = 0
    failed = 0
    
    # Procesează în batch-uri
    for i in range(0, total_count, batch_size):
        batch = pending_messages[i:i + batch_size]
        
        for outbox in batch:
            processed += 1
            
            try:
                success = process_outbox_message(outbox)
                if success:
                    sent += 1
                    logger.info(
                        f'✓ Email trimis: {outbox.to} - {outbox.template} '
                        f'(outbox_id={outbox.id})'
                    )
                else:
                    failed += 1
                    logger.warning(
                        f'✗ Email eșuat: {outbox.to} - {outbox.template} '
                        f'(outbox_id={outbox.id}, attempts={outbox.attempts})'
                    )
            except Exception as e:
                failed += 1
                logger.error(
                    f'✗ Eroare la procesarea outbox {outbox.id}: {e}',
                    exc_info=True
                )
    
    result = {
        'processed': processed,
        'sent': sent,
        'failed': failed,
        'total': total_count
    }
    
    logger.info(f'Procesare completă: {result}')
    return result


@shared_task(name='notify.send_single_email', bind=True)
def send_single_email(self, outbox_id):
    """
    Task pentru trimiterea unui singur email din outbox.
    
    Utilizat pentru retry-uri sau trimitere imediată.
    
    Args:
        outbox_id: ID-ul mesajului din EmailOutbox
        
    Returns:
        bool: True dacă a fost trimis cu succes, False altfel
    """
    try:
        outbox = EmailOutbox.objects.get(id=outbox_id)
        success = process_outbox_message(outbox)
        
        if success:
            logger.info(f'Email trimis cu succes: outbox_id={outbox_id}')
        else:
            logger.warning(f'Email eșuat: outbox_id={outbox_id}')
        
        return success
    except EmailOutbox.DoesNotExist:
        logger.error(f'EmailOutbox cu id={outbox_id} nu există')
        return False
    except Exception as e:
        logger.error(f'Eroare la trimiterea email-ului outbox_id={outbox_id}: {e}', exc_info=True)
        return False

