# Generated manually

from django.db import migrations, models
from django.utils import timezone
from datetime import timedelta


def populate_request_dates(apps, schema_editor):
    """Populează date_start și date_end pentru Request-urile existente."""
    Request = apps.get_model('core', 'Request')
    
    # Pentru toate Request-urile existente care nu au date_start/date_end
    # le populăm cu date default (mâine, 4 ore)
    now = timezone.now()
    for request in Request.objects.filter(date_start__isnull=True):
        request.date_start = now + timedelta(days=1)
        request.date_end = now + timedelta(days=1, hours=4)
        request.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_item_room'),
    ]

    operations = [
        # Remove index for is_active from Room
        migrations.RemoveIndex(
            model_name='room',
            name='core_room_is_acti_9de2db_idx',
        ),
        # Remove is_active field from Room
        migrations.RemoveField(
            model_name='room',
            name='is_active',
        ),
        # Add date_start and date_end to Request
        # First add as nullable, then make them required
        migrations.AddField(
            model_name='request',
            name='date_start',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='request',
            name='date_end',
            field=models.DateTimeField(null=True, blank=True),
        ),
        # Populate existing requests with default dates (if any exist)
        migrations.RunPython(
            code=populate_request_dates,
            reverse_code=migrations.RunPython.noop,
        ),
        # Make date_start and date_end required
        migrations.AlterField(
            model_name='request',
            name='date_start',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='request',
            name='date_end',
            field=models.DateTimeField(),
        ),
        # Add constraint to ensure date_end > date_start
        migrations.AddConstraint(
            model_name='request',
            constraint=models.CheckConstraint(
                check=models.Q(('date_end__gt', models.F('date_start'))),
                name='request_date_end_after_date_start'
            ),
        ),
    ]

