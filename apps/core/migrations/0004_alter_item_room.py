# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_orgpolicy_team_required_days_per_week_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='room',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='items',
                to='core.room'
            ),
        ),
    ]

