# Generated manually

from django.db import migrations, models


def delete_first_10_items(apps, schema_editor):
    """Șterge primele 10 înregistrări din Item (doar dacă nu au appointments asociate)."""
    Item = apps.get_model('core', 'Item')
    Appointment = apps.get_model('core', 'Appointment')
    
    # Șterge primele 10 items ordonate după id, dar doar dacă nu au appointments
    items_to_delete = Item.objects.all().order_by('id')[:10]
    deleted_count = 0
    
    for item in items_to_delete:
        # Verifică dacă item-ul are appointments asociate
        has_appointments = Appointment.objects.filter(item=item).exists()
        if not has_appointments:
            item.delete()
            deleted_count += 1
    
    # Dacă nu am putut șterge toate cele 10, încercăm să ștergem appointments-urile asociate
    # și apoi items-urile
    remaining = 10 - deleted_count
    if remaining > 0:
        items_with_appointments = Item.objects.all().order_by('id')[:remaining]
        for item in items_with_appointments:
            # Șterge appointments-urile asociate
            Appointment.objects.filter(item=item).delete()
            # Acum putem șterge item-ul
            item.delete()


def reverse_delete_items(apps, schema_editor):
    """Nu putem restaura items șterse."""
    pass


class Migration(migrations.Migration):
    atomic = False  # Necesar pentru a evita erorile cu pending trigger events

    dependencies = [
        ('core', '0006_roomcategory_room_category'),
    ]

    operations = [
        # 1. Șterge primele 10 înregistrări din Item (cu appointments asociate)
        migrations.RunPython(
            code=delete_first_10_items,
            reverse_code=reverse_delete_items,
        ),
        
        # 2. Șterge coloanele category și room din Item (înainte de a șterge ItemCategory)
        migrations.RemoveField(
            model_name='item',
            name='category',
        ),
        migrations.RemoveField(
            model_name='item',
            name='room',
        ),
        
        # 3. Șterge index-ul vechi care include room (dacă există)
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS core_item_room_status_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # 4. Șterge tabelul ItemCategory (după ce am șters coloanele care îl referențiază)
        migrations.DeleteModel(
            name='ItemCategory',
        ),
        
        # 5. Adaugă index nou doar pentru status
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['status'], name='core_item_status_idx'),
        ),
        
        # 6. Șterge features din Room (ultimul, nu are dependențe)
        migrations.RemoveField(
            model_name='room',
            name='features',
        ),
    ]

