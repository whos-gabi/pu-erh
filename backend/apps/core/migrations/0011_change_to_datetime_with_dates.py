# Generated manually

from django.db import migrations, models
from django.utils import timezone
from datetime import timedelta


def populate_datetime_fields(apps, schema_editor):
    """Populează start_date și end_date pentru Request și Appointment existente."""
    Request = apps.get_model('core', 'Request')
    Appointment = apps.get_model('core', 'Appointment')
    
    # Pentru Request: convertim date_start/date_end în start_date/end_date
    # Presupunem că date_start și date_end sunt DateField-uri
    for request in Request.objects.all():
        if hasattr(request, 'date_start') and request.date_start:
            # Setăm ora la 9:00 pentru start_date și 17:00 pentru end_date
            request.start_date = timezone.make_aware(
                request.date_start.replace(hour=9, minute=0, second=0, microsecond=0)
            ) if not timezone.is_aware(request.date_start) else request.date_start.replace(hour=9, minute=0, second=0, microsecond=0)
            request.end_date = timezone.make_aware(
                request.date_end.replace(hour=17, minute=0, second=0, microsecond=0)
            ) if not timezone.is_aware(request.date_end) else request.date_end.replace(hour=17, minute=0, second=0, microsecond=0)
            request.save()
    
    # Pentru Appointment: convertim start_at/end_at în start_date/end_date
    for appointment in Appointment.objects.all():
        if hasattr(appointment, 'start_at') and appointment.start_at:
            # Setăm ora la 9:00 pentru start_date și 11:00 pentru end_date
            appointment.start_date = timezone.make_aware(
                appointment.start_at.replace(hour=9, minute=0, second=0, microsecond=0)
            ) if not timezone.is_aware(appointment.start_at) else appointment.start_at.replace(hour=9, minute=0, second=0, microsecond=0)
            appointment.end_date = timezone.make_aware(
                appointment.end_at.replace(hour=11, minute=0, second=0, microsecond=0)
            ) if not timezone.is_aware(appointment.end_at) else appointment.end_at.replace(hour=11, minute=0, second=0, microsecond=0)
            appointment.save()


def reverse_populate(apps, schema_editor):
    """Nu putem converti înapoi datetime la date fără pierdere de informație."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_request_from_appointment'),
    ]

    operations = [
        # 1. Adaugă câmpurile noi ca nullable temporar
        migrations.AddField(
            model_name='request',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='request',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        
        # 2. Populează câmpurile noi din cele vechi
        migrations.RunPython(
            code=populate_datetime_fields,
            reverse_code=reverse_populate,
        ),
        
        # 3. Șterge constraint-urile vechi
        migrations.RemoveConstraint(
            model_name='request',
            name='request_date_end_after_or_equal_date_start',
        ),
        migrations.RemoveConstraint(
            model_name='appointment',
            name='appointment_end_after_or_equal_start',
        ),
        
        # 4. Șterge index-ul vechi (dacă există)
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS core_appointment_item_start_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # 5. Șterge câmpurile vechi
        migrations.RemoveField(
            model_name='request',
            name='date_start',
        ),
        migrations.RemoveField(
            model_name='request',
            name='date_end',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='start_at',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='end_at',
        ),
        
        # 6. Face câmpurile noi non-nullable
        migrations.AlterField(
            model_name='request',
            name='start_date',
            field=models.DateTimeField(help_text='Data și ora de început'),
        ),
        migrations.AlterField(
            model_name='request',
            name='end_date',
            field=models.DateTimeField(help_text='Data și ora de sfârșit'),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='start_date',
            field=models.DateTimeField(help_text='Data și ora de început'),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='end_date',
            field=models.DateTimeField(help_text='Data și ora de sfârșit'),
        ),
        
        # 7. Adaugă index-ul nou
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['item', 'start_date'], name='core_appointment_item_start_idx'),
        ),
        
        # 8. Adaugă constraint-urile noi
        migrations.AddConstraint(
            model_name='request',
            constraint=models.CheckConstraint(
                check=models.Q(('end_date__gt', models.F('start_date'))),
                name='request_end_date_after_start_date',
            ),
        ),
        migrations.AddConstraint(
            model_name='appointment',
            constraint=models.CheckConstraint(
                check=models.Q(('end_date__gt', models.F('start_date'))),
                name='appointment_end_date_after_start_date',
            ),
        ),
    ]

