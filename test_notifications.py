"""
Script simplu pentru testarea sistemului de notificări.
Rulează: python test_notifications.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import User, Room, Item, ItemCategory, Appointment, Request
from apps.notify.models import NotificationEvent, EmailOutbox
from apps.notify.services import (
    notify_appointment_summary,
    notify_request_status,
    notify_desk_release_batch
)
from django.utils import timezone
from datetime import timedelta, date, datetime

print("=" * 60)
print("🧪 TESTARE SISTEM NOTIFICĂRI")
print("=" * 60)

# Verificări inițiale
user = User.objects.first()
if not user:
    print("❌ EROARE: Nu există utilizatori în sistem!")
    print("   Creează un user mai întâi: python manage.py createsuperuser")
    exit(1)

print(f"✓ Utilizator găsit: {user.username} ({user.email})")

# Test 1: Rezumat Programare
print("\n" + "=" * 60)
print("📅 TEST 1: Rezumat Programare")
print("=" * 60)

item = Item.objects.first()
if not item:
    print("❌ EROARE: Nu există items în sistem!")
    print("   Creează camere și items mai întâi")
    exit(1)

print(f"✓ Item găsit: {item.name}")

# Creează o programare
appointment = Appointment.objects.create(
    user=user,
    item=item,
    start_at=timezone.now() + timedelta(days=1),
    end_at=timezone.now() + timedelta(days=1, hours=8)
)

print(f"✓ Appointment creat: ID={appointment.id}")

# Declanșează notificarea
try:
    notify_appointment_summary(appointment)
    print("✓ Notificare declanșată cu succes")
except Exception as e:
    print(f"❌ EROARE la declanșarea notificării: {e}")
    exit(1)

# Verifică rezultatul
event = NotificationEvent.objects.filter(
    type='APPOINTMENT_SUMMARY',
    subject_user=user
).order_by('-created_at').first()

if event:
    print(f"✓ Eveniment creat: {event.id}")
    print(f"  Payload: {event.payload}")
else:
    print("❌ EROARE: Evenimentul nu a fost creat!")

outbox = EmailOutbox.objects.filter(
    template='appointment_summary',
    to=user.email
).order_by('-scheduled_at').first()

if outbox:
    print(f"✓ Mesaj în outbox: ID={outbox.id}")
    print(f"  Destinatar: {outbox.to}")
    print(f"  Template: {outbox.template}")
    print(f"  Status: {'✓ Trimis' if outbox.sent_at else '⏳ În așteptare'}")
else:
    print("❌ EROARE: Mesajul nu a fost adăugat în outbox!")

# Test 2: Schimbare Status Cerere
print("\n" + "=" * 60)
print("📋 TEST 2: Schimbare Status Cerere")
print("=" * 60)

room = Room.objects.first()
if not room:
    print("⚠️  AVERTISMENT: Nu există camere în sistem!")
    print("   Sări peste acest test")
else:
    print(f"✓ Cameră găsită: {room.code} - {room.name}")
    
    # Creează o cerere
    request_obj = Request.objects.create(
        user=user,
        room=room,
        status=Request.WAITING
    )
    
    print(f"✓ Request creat: ID={request_obj.id}, Status=WAITING")
    
    # Aprobă cererea
    superadmin = User.objects.filter(is_superuser=True).first()
    if superadmin:
        request_obj.status = Request.APPROVED
        request_obj.decided_by = superadmin
        request_obj.save()
        
        print(f"✓ Request aprobat de: {superadmin.username}")
        
        # Declanșează notificarea
        try:
            notify_request_status(request_obj)
            print("✓ Notificare declanșată cu succes")
        except Exception as e:
            print(f"❌ EROARE la declanșarea notificării: {e}")
        
        # Verifică rezultatul
        event = NotificationEvent.objects.filter(
            type='REQUEST_STATUS',
            subject_user=user
        ).order_by('-created_at').first()
        
        if event:
            print(f"✓ Eveniment creat: {event.id}")
            print(f"  Status: {event.payload.get('status')}")
        
        outbox = EmailOutbox.objects.filter(
            template='request_status',
            to=user.email
        ).order_by('-scheduled_at').first()
        
        if outbox:
            print(f"✓ Mesaj în outbox: ID={outbox.id}")
            print(f"  Status: {'✓ Trimis' if outbox.sent_at else '⏳ În așteptare'}")
    else:
        print("⚠️  AVERTISMENT: Nu există superadmin pentru a aproba cererea")

# Test 3: Cerere Eliberare Birou
print("\n" + "=" * 60)
print("🪑 TEST 3: Cerere Eliberare Birou")
print("=" * 60)

desk_category = ItemCategory.objects.filter(slug='birou').first()
if not desk_category:
    print("⚠️  AVERTISMENT: Nu există categoria 'birou'!")
    print("   Creează categoria mai întâi:")
    print("   python manage.py shell")
    print("   >>> from apps.core.models import ItemCategory")
    print("   >>> ItemCategory.objects.create(name='Birou', slug='birou')")
else:
    print(f"✓ Categorie găsită: {desk_category.name}")
    
    desk = Item.objects.filter(category=desk_category).first()
    if not desk:
        print("⚠️  AVERTISMENT: Nu există birouri în sistem!")
    else:
        print(f"✓ Birou găsit: {desk.name}")
        
        # Creează o programare pentru mâine
        target_date = date.today() + timedelta(days=1)
        appointment = Appointment.objects.create(
            user=user,
            item=desk,
            start_at=timezone.make_aware(
                datetime.combine(target_date, datetime.min.time())
            ),
            end_at=timezone.make_aware(
                datetime.combine(target_date, datetime.max.time())
            )
        )
        
        print(f"✓ Programare creată pentru data: {target_date}")
        
        # Simulează over-quota users
        overquota_users = [{
            'user_id': user.id,
            'appointments_on_date': [{'id': appointment.id, 'item': desk.name}]
        }]
        
        # Declanșează notificarea
        try:
            notify_desk_release_batch(target_date, overquota_users, user)
            print(f"✓ Notificare declanșată pentru {len(overquota_users)} utilizator")
        except Exception as e:
            print(f"❌ EROARE la declanșarea notificării: {e}")
        
        # Verifică rezultatul
        events = NotificationEvent.objects.filter(
            type='DESK_RELEASE_ASK'
        ).order_by('-created_at')
        
        print(f"✓ Evenimente create: {events.count()}")
        
        outbox_messages = EmailOutbox.objects.filter(
            template='desk_release_ask',
            to=user.email
        )
        
        print(f"✓ Mesaje în outbox: {outbox_messages.count()}")
        for msg in outbox_messages:
            print(f"  - ID={msg.id}, Date={msg.context.get('date')}, Status={'✓ Trimis' if msg.sent_at else '⏳ În așteptare'}")

# Rezumat final
print("\n" + "=" * 60)
print("📊 REZUMAT")
print("=" * 60)

total_events = NotificationEvent.objects.count()
total_outbox = EmailOutbox.objects.count()
pending_outbox = EmailOutbox.objects.filter(sent_at__isnull=True).count()
sent_outbox = EmailOutbox.objects.exclude(sent_at__isnull=True).count()

print(f"Total evenimente create: {total_events}")
print(f"Total mesaje în outbox: {total_outbox}")
print(f"  - În așteptare: {pending_outbox}")
print(f"  - Trimise: {sent_outbox}")

if pending_outbox > 0:
    print("\n📧 Pentru a trimite email-urile, rulează:")
    print("   python manage.py send_emails")
    print("\n💡 În development, email-urile vor apărea în consolă")
    print("   (pentru că folosim console backend)")

print("\n" + "=" * 60)
print("✅ Testare completă!")
print("=" * 60)

