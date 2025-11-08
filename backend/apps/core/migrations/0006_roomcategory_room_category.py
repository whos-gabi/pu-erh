# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_room_is_active_add_request_dates'),
    ]

    operations = [
        # Create RoomCategory model
        migrations.CreateModel(
            name='RoomCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('code', models.CharField(max_length=32, unique=True)),
            ],
            options={
                'verbose_name': 'Room Category',
                'verbose_name_plural': 'Room Categories',
                'db_table': 'core_room_category',
            },
        ),
        # Add category field to Room (nullable first)
        migrations.AddField(
            model_name='room',
            name='category',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='rooms',
                to='core.roomcategory'
            ),
        ),
        # Populate RoomCategory with default categories
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # Will be populated by seed_data
            reverse_code=migrations.RunPython.noop,
        ),
        # Make category required
        migrations.AlterField(
            model_name='room',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='rooms',
                to='core.roomcategory'
            ),
        ),
    ]

