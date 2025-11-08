"""
Script de inițializare pentru Docker.
Rulează migrațiile, creează superadmin-ul și datele de test.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


def main():
    """Funcția principală de inițializare."""
    print("🔧 Rulare migrații...")
    call_command('migrate', verbosity=1)
    
    print("👤 Verificare superadmin...")
    with transaction.atomic():
        # Verifică dacă există deja un superadmin
        if not User.objects.filter(is_superuser=True).exists():
            print("   [+] Creez superadmin (username: super123, password: super123)...")
            User.objects.create_superuser(
                username='super123',
                email='superadmin@molsoncoors.app',
                password='super123',
                first_name='Super',
                last_name='Admin'
            )
            print("   [OK] Superadmin creat cu succes!")
        else:
            print("   [i] Superadmin există deja, skip...")
    
    print("📦 Creez date de test...")
    try:
        # Folosim --clear pentru a șterge datele vechi și a crea altele noi
        call_command('seed_data', '--clear', verbosity=1)
    except Exception as e:
        # Dacă seed_data eșuează (ex: date deja existente sau suprapuneri),
        # continuăm oricum - aplicația poate funcționa fără date de test
        print(f"   [!] Avertisment: seed_data a eșuat: {e}")
        print("   [i] Continuăm oricum - aplicația poate funcționa fără date de test")
    
    print("✅ Inițializare completă!")
    print("")
    print("🚀 Serverul pornește...")
    print("")
    print("📝 Credențiale superadmin:")
    print("   Username: super123")
    print("   Password: super123")
    print("")
    
    # Pornește serverul Django
    call_command('runserver', '0.0.0.0:8000')


if __name__ == '__main__':
    main()

