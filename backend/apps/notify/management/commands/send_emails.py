"""
Management command pentru procesarea cozii de email-uri.

Acest command procesează mesajele din EmailOutbox care nu au fost încă trimise
și le trimite efectiv prin email.

Utilizare:
    python manage.py send_emails
    python manage.py send_emails --batch-size 50
    python manage.py send_emails --max-messages 100
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from apps.notify.models import EmailOutbox
from apps.notify.email_sender import process_outbox_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Procesează și trimite email-urile din coada EmailOutbox'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Numărul de mesaje de procesat într-un batch (default: 50)',
        )
        parser.add_argument(
            '--max-messages',
            type=int,
            default=None,
            help='Numărul maxim de mesaje de procesat (default: toate)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulează procesarea fără a trimite efectiv email-uri',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        max_messages = options['max_messages']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Nu se vor trimite email-uri efectiv'))
        
        # Găsește mesajele care trebuie procesate:
        # - Nu au fost trimise (sent_at is None)
        # - Sunt programate pentru acum sau în trecut (scheduled_at <= now)
        # - Nu sunt blocate sau lock-ul a expirat
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
            self.stdout.write(self.style.SUCCESS('Nu există mesaje de procesat'))
            return
        
        self.stdout.write(f'Găsite {total_count} mesaje de procesat')
        
        processed = 0
        sent = 0
        failed = 0
        
        # Procesează în batch-uri
        for i in range(0, total_count, batch_size):
            batch = pending_messages[i:i + batch_size]
            
            for outbox in batch:
                processed += 1
                
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Ar procesa: {outbox.to} - {outbox.template} '
                        f'(outbox_id={outbox.id})'
                    )
                    sent += 1
                    continue
                
                try:
                    success = process_outbox_message(outbox)
                    if success:
                        sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Trimis: {outbox.to} - {outbox.template} '
                                f'(outbox_id={outbox.id})'
                            )
                        )
                    else:
                        failed += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'✗ Eșuat: {outbox.to} - {outbox.template} '
                                f'(outbox_id={outbox.id}, attempts={outbox.attempts})'
                            )
                        )
                except Exception as e:
                    failed += 1
                    logger.error(f'Eroare la procesarea outbox {outbox.id}: {e}', exc_info=True)
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Eroare: {outbox.to} - {outbox.template} '
                            f'(outbox_id={outbox.id}): {e}'
                        )
                    )
        
        # Rezumat
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Rezumat:'))
        self.stdout.write(self.style.SUCCESS(f'  Procesate: {processed}'))
        self.stdout.write(self.style.SUCCESS(f'  Trimise: {sent}'))
        self.stdout.write(self.style.WARNING(f'  Eșuate: {failed}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

