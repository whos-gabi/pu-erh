"""
Management command pentru crearea de date de test (seed data).

Utilizare:
    python manage.py seed_data
    
Opțional, poți șterge datele existente:
    python manage.py seed_data --clear
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from datetime import timedelta
import random
import json

from apps.core.models import (
    Role,
    Team,
    RoomCategory,
    Room,
    Item,
    Request,
    Appointment,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Creează date de test pentru aplicație'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge datele existente înainte de a crea noi date',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Șterg datele existente...'))
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('Incep crearea datelor de test...'))
        
        # Creează datele în ordine (respectând dependențele)
        roles = self.create_roles()
        teams = self.create_teams()
        users = self.create_users(teams, roles)
        room_categories = self.create_room_categories()
        rooms = self.create_rooms(room_categories)
        items = self.create_items()
        requests = self.create_requests(users, rooms)
        appointments = self.create_appointments(users, items, requests)
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Date de test create cu succes!'))
        self.print_summary(roles, teams, users, room_categories, rooms, items, requests, appointments)

    def reset_sequences(self):
        """Resetează secvențele (ID-urile) pentru toate tabelele."""
        self.stdout.write('  [*] Resetez secvențele (ID-uri)...')
        
        with connection.cursor() as cursor:
            # Listează toate tabelele pentru care vrem să resetăm secvențele
            tables = [
                'core_role',
                'core_team',
                'core_room_category',
                'core_room',
                'core_item',
                'core_request',
                'core_appointment',
            ]
            
            for table in tables:
                try:
                    # Resetează secvența la 1 (pentru că am șters toate datele)
                    cursor.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false);"
                    )
                    self.stdout.write(f'    [+] Resetat secvența pentru {table} la 1')
                except Exception as e:
                    # Dacă tabelul nu există sau nu are secvență, continuă
                    self.stdout.write(f'    [!] Nu s-a putut reseta {table}: {e}')

    def clear_data(self):
        """Șterge toate datele (păstrând doar superadmin)."""
        # Șterge în ordinea corectă (respectând dependențele)
        Appointment.objects.all().delete()
        Request.objects.all().delete()
        Item.objects.all().delete()
        Room.objects.all().delete()  # Trebuie șters înainte de RoomCategory (PROTECT)
        RoomCategory.objects.all().delete()
        # Nu ștergem User-ii (păstrăm superadmin)
        Team.objects.all().delete()
        Role.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Date șterse.'))
        
        # Resetează secvențele (ID-uri) la 1
        self.reset_sequences()

    def create_roles(self):
        """Creează roluri."""
        self.stdout.write('  [*] Creez roluri...')
        roles_data = [
            {'name': 'ADMIN'},
            {'name': 'MANAGER'},
            {'name': 'EMPLOYEE'},
            {'name': 'DEVELOPER'},
        ]
        
        roles = []
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(**role_data)
            roles.append(role)
            if created:
                self.stdout.write(f'    [+] Creat: {role.name}')
        
        return roles

    def create_teams(self):
        """Creează echipe."""
        self.stdout.write('  [*] Creez echipe...')
        
        # Obține superadmin pentru manageri (dacă există)
        superadmin = User.objects.filter(is_superuser=True).first()
        
        teams_data = [
            {'name': 'IT Department', 'manager': superadmin},
            {'name': 'HR Department', 'manager': None},
            {'name': 'Sales Team', 'manager': None},
            {'name': 'Marketing', 'manager': None},
            {'name': 'ML BI', 'manager': None},
        ]
        
        teams = []
        for team_data in teams_data:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={'manager': team_data['manager']}
            )
            teams.append(team)
            if created:
                self.stdout.write(f'    [+] Creat: {team.name}')
        
        return teams

    def create_room_categories(self):
        """Creează categorii de camere."""
        self.stdout.write('  [*] Creez categorii de camere...')
        
        categories_data = [
            {'name': 'Meeting Room', 'code': 'MEETING'},
            {'name': 'Beer Point', 'code': 'BEER'},
            {'name': 'Training Room', 'code': 'TRAINING'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = RoomCategory.objects.get_or_create(**cat_data)
            categories.append(category)
            if created:
                self.stdout.write(f'    [+] Creat: {category.name} ({category.code})')
        
        return categories

    def create_users(self, teams, roles):
        """Creează utilizatori (Employee-uri)."""
        self.stdout.write('  [*] Creez utilizatori...')
        
        users_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'team': teams[0] if teams else None,
                'role': roles[2] if len(roles) > 2 else None,  # EMPLOYEE
            },
        ]
        
        users = []
        for user_data in users_data:
            username = user_data.pop('username')
            email = user_data.pop('email')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_active': True,
                    **user_data
                }
            )
            
            if created:
                # Setăm parola pentru utilizatorii noi
                user.set_password('test123')  # Parolă simplă pentru testare
                user.save()
                self.stdout.write(f'    [+] Creat: {user.username} (parola: test123)')
            else:
                # Actualizăm datele pentru utilizatorii existenți
                for key, value in user_data.items():
                    setattr(user, key, value)
                user.save()
            
            users.append(user)
        
        return users

    def create_rooms(self, room_categories):
        """Creează camere."""
        self.stdout.write('  [*] Creez camere...')
        
        # Găsește categoriile
        training_category = next((c for c in room_categories if c.code == 'TRAINING'), None)
        meeting_category = next((c for c in room_categories if c.code == 'MEETING'), None)
        beer_category = next((c for c in room_categories if c.code == 'BEER'), None)
        
        rooms_data = [
            {
                'code': 'meetingLarge1',
                'name': 'Training Room 1',
                'category': training_category,
                'capacity': 18
            },
            {
                'code': 'meetingLarge2',
                'name': 'Training Room 2',
                'category': training_category,
                'capacity': 19
            },
            {
                'code': 'meetingRoom1',
                'name': 'Meeting Room 1',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'meetingRoom2',
                'name': 'Meeting Room 2',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'meetingRoom3',
                'name': 'Meeting Room 3',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'meetingRoom4',
                'name': 'Meeting Room 4',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'meetingRoom5',
                'name': 'Meeting Room 5',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'meetingRoom6',
                'name': 'Meeting Room 6',
                'category': meeting_category,
                'capacity': 4
            },
            {
                'code': 'beerPointArea',
                'name': 'Beer Point',
                'category': beer_category,
                'capacity': 100
            }
        ]
        
        rooms = []
        for room_data in rooms_data:
            code = room_data.pop('code')
            room, created = Room.objects.get_or_create(
                code=code,
                defaults=room_data
            )
            rooms.append(room)
            if created:
                self.stdout.write(f'    [+] Creat: {room.code} - {room.name}')
        
        return rooms

    def create_items(self):
        """Creează item-uri de inventar."""
        self.stdout.write('  [*] Creez item-uri de inventar...')
        
        items_data = []
        for i in range(1, 217):
            items_data.append({
                'name': f'scaun{i}',
                'status': Item.ACTIVE,
                'meta': json.dumps({"an_fabricatie": 2018})
            })
        
        items = []
        for item_data in items_data:
            name = item_data.pop('name')
            item, created = Item.objects.get_or_create(
                name=name,
                defaults=item_data
            )
            items.append(item)
            if created:
                self.stdout.write(f'    [+] Creat: {item.name}')
        
        return items

    def create_requests(self, users, rooms):
        requests = []
        
        return requests

    def create_appointments(self, users, items, requests):
        appointments = []
        
        return appointments

    def print_summary(self, roles, teams, users, room_categories, rooms, items, requests, appointments):
        """Afișează un rezumat al datelor create."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('REZUMAT DATE CREATE:'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Roles: {len(roles)}')
        self.stdout.write(f'  Teams: {len(teams)}')
        self.stdout.write(f'  Users (Employee): {len(users)}')
        self.stdout.write(f'  Room Categories: {len(room_categories)}')
        self.stdout.write(f'  Rooms: {len(rooms)}')
        self.stdout.write(f'  Items: {len(items)}')
        self.stdout.write(f'  Requests: {len(requests)}')
        self.stdout.write(f'  Appointments: {len(appointments)}')
        self.stdout.write('=' * 60)
        
        # Credențiale pentru testare
        self.stdout.write('\n' + self.style.SUCCESS('CREDENTIALE PENTRU TESTARE:'))
        self.stdout.write('=' * 60)
        self.stdout.write('  SUPERADMIN:')
        self.stdout.write('    Username: super123')
        self.stdout.write('    Password: super123')
        self.stdout.write('\n  EMPLOYEE (toti au parola: test123):')
        for user in users:
            self.stdout.write(f'    - {user.username} ({user.email})')
        self.stdout.write('=' * 60)