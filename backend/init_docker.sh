#!/bin/bash
# Script de inițializare pentru Docker
# Rulează migrațiile, creează superadmin-ul și datele de test

set -e

echo "🔧 Rulare migrații..."
python manage.py migrate

echo "👤 Verificare superadmin..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

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
EOF

echo "📦 Creez date de test..."
python manage.py seed_data

echo "✅ Inițializare completă!"
echo ""
echo "🚀 Serverul pornește..."
exec python manage.py runserver 0.0.0.0:8000

