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
from datetime import timedelta
import random

from apps.core.models import (
    Role,
    Team,
    Room,
    ItemCategory,
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
        rooms = self.create_rooms()
        categories = self.create_item_categories()
        items = self.create_items(rooms, categories)
        requests = self.create_requests(users, rooms)
        appointments = self.create_appointments(users, items, requests)
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Date de test create cu succes!'))
        self.print_summary(roles, teams, users, rooms, categories, items, requests, appointments)

    def clear_data(self):
        """Șterge toate datele (păstrând doar superadmin)."""
        Appointment.objects.all().delete()
        Request.objects.all().delete()
        Item.objects.all().delete()
        ItemCategory.objects.all().delete()
        Room.objects.all().delete()
        # Nu ștergem User-ii (păstrăm superadmin)
        Team.objects.all().delete()
        Role.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Date șterse.'))

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
            {
                'username': 'jane.smith',
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'team': teams[0] if teams else None,
                'role': roles[2] if len(roles) > 2 else None,  # EMPLOYEE
            },
            {
                'username': 'bob.wilson',
                'email': 'bob.wilson@example.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'team': teams[1] if len(teams) > 1 else None,
                'role': roles[2] if len(roles) > 2 else None,  # EMPLOYEE
            },
            {
                'username': 'alice.brown',
                'email': 'alice.brown@example.com',
                'first_name': 'Alice',
                'last_name': 'Brown',
                'team': teams[2] if len(teams) > 2 else None,
                'role': roles[3] if len(roles) > 3 else None,  # DEVELOPER
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

    def create_rooms(self):
        """Creează camere."""
        self.stdout.write('  [*] Creez camere...')
        
        rooms_data = [
            {
                'code': 'B1-101',
                'name': 'Sala de conferinte A',
                'capacity': 20,
                'features': {'projector': True, 'whiteboard': True, 'video_conference': True},
                'is_active': True,
            },
            {
                'code': 'B1-102',
                'name': 'Sala de conferinte B',
                'capacity': 15,
                'features': {'projector': True, 'whiteboard': True},
                'is_active': True,
            },
            {
                'code': 'B1-203',
                'name': 'Birou individual 1',
                'capacity': 1,
                'features': {'desk': True, 'monitor': True},
                'is_active': True,
            },
            {
                'code': 'B1-204',
                'name': 'Birou individual 2',
                'capacity': 1,
                'features': {'desk': True, 'monitor': True},
                'is_active': True,
            },
            {
                'code': 'B2-301',
                'name': 'Sala de training',
                'capacity': 30,
                'features': {'projector': True, 'whiteboard': True, 'computers': 15},
                'is_active': True,
            },
            {
                'code': 'B2-302',
                'name': 'Sala inactiva',
                'capacity': 10,
                'features': {},
                'is_active': False,  # Cameră inactivă pentru testare
            },
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

    def create_item_categories(self):
        """Creează categorii de inventar."""
        self.stdout.write('  [*] Creez categorii de inventar...')
        
        categories_data = [
            {'name': 'Laptop', 'slug': 'laptop', 'description': 'Laptop-uri pentru lucru'},
            {'name': 'Monitor', 'slug': 'monitor', 'description': 'Monitoare externe'},
            {'name': 'Proiector', 'slug': 'projector', 'description': 'Proiectoare pentru prezentari'},
            {'name': 'Tableta', 'slug': 'tablet', 'description': 'Tablete pentru prezentari'},
            {'name': 'Mouse', 'slug': 'mouse', 'description': 'Mouse-uri wireless'},
        ]
        
        categories = []
        for cat_data in categories_data:
            slug = cat_data.pop('slug')
            category, created = ItemCategory.objects.get_or_create(
                slug=slug,
                defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f'    [+] Creat: {category.name}')
        
        return categories

    def create_items(self, rooms, categories):
        """Creează item-uri de inventar."""
        self.stdout.write('  [*] Creez item-uri de inventar...')
        
        items_data = [
            # Laptop-uri
            {'name': 'LT-001', 'room': rooms[0], 'category': categories[0], 'status': Item.ACTIVE},
            {'name': 'LT-002', 'room': rooms[0], 'category': categories[0], 'status': Item.ACTIVE},
            {'name': 'LT-003', 'room': rooms[1], 'category': categories[0], 'status': Item.ACTIVE},
            {'name': 'LT-004', 'room': rooms[2], 'category': categories[0], 'status': Item.ACTIVE},
            {'name': 'LT-005', 'room': rooms[3], 'category': categories[0], 'status': Item.BROKEN},  # Broken pentru testare
            
            # Monitoare
            {'name': 'MON-001', 'room': rooms[2], 'category': categories[1], 'status': Item.ACTIVE},
            {'name': 'MON-002', 'room': rooms[3], 'category': categories[1], 'status': Item.ACTIVE},
            
            # Proiectoare
            {'name': 'PROJ-001', 'room': rooms[0], 'category': categories[2], 'status': Item.ACTIVE},
            {'name': 'PROJ-002', 'room': rooms[1], 'category': categories[2], 'status': Item.ACTIVE},
            
            # Tablete
            {'name': 'TAB-001', 'room': rooms[0], 'category': categories[3], 'status': Item.ACTIVE},
        ]
        
        items = []
        for item_data in items_data:
            name = item_data.pop('name')
            item, created = Item.objects.get_or_create(
                name=name,
                defaults=item_data
            )
            items.append(item)
            if created:
                self.stdout.write(f'    [+] Creat: {item.name} ({item.category.name}) in {item.room.code}')
        
        return items

    def create_requests(self, users, rooms):
        """Creează cereri de rezervare."""
        self.stdout.write('  [*] Creez cereri de rezervare...')
        
        superadmin = User.objects.filter(is_superuser=True).first()
        if not superadmin:
            self.stdout.write(self.style.WARNING('    [!] Nu exista superadmin pentru aprobare!'))
            return []
        
        # Creează cereri cu statusuri diferite
        requests = []
        
        # Cereri WAITING (în așteptare)
        for i, user in enumerate(users[:2]):  # Primele 2 utilizatori
            request = Request.objects.create(
                user=user,
                room=rooms[i % len(rooms)],
                status=Request.WAITING,
                note=f'Cerere de test #{i+1}',
            )
            requests.append(request)
            self.stdout.write(f'    [+] Creat: Request {request.id} - {request.room.code} (WAITING)')
        
        # Cereri APPROVED (aprobate de superadmin)
        for i, user in enumerate(users[1:3]):  # Următorii 2 utilizatori
            request = Request.objects.create(
                user=user,
                room=rooms[(i+1) % len(rooms)],
                status=Request.APPROVED,
                decided_by=superadmin,
                note=f'Cerere aprobata #{i+1}',
            )
            requests.append(request)
            self.stdout.write(f'    [+] Creat: Request {request.id} - {request.room.code} (APPROVED)')
        
        # Cereri DISMISSED (respinse de superadmin)
        if len(users) > 2:
            request = Request.objects.create(
                user=users[2],
                room=rooms[2],
                status=Request.DISMISSED,
                decided_by=superadmin,
                note='Cerere respinsa pentru testare',
            )
            requests.append(request)
            self.stdout.write(f'    [+] Creat: Request {request.id} - {request.room.code} (DISMISSED)')
        
        return requests

    def create_appointments(self, users, items, requests):
        """Creează programări."""
        self.stdout.write('  [*] Creez programari...')
        
        now = timezone.now()
        appointments = []
        
        # Programări în trecut (finalizate)
        for i, user in enumerate(users[:2]):
            start_at = now - timedelta(days=2, hours=10-i)
            end_at = start_at + timedelta(hours=1)
            item = items[i % len(items)]
            
            appointment = Appointment.objects.create(
                user=user,
                item=item,
                start_at=start_at,
                end_at=end_at,
            )
            appointments.append(appointment)
            self.stdout.write(f'    [+] Creat: Appointment {appointment.id} - {item.name} (trecut)')
        
        # Programări în prezent (active)
        for i, user in enumerate(users[1:3]):
            start_at = now - timedelta(minutes=30)
            end_at = now + timedelta(hours=1)
            item = items[(i+2) % len(items)]
            
            appointment = Appointment.objects.create(
                user=user,
                item=item,
                start_at=start_at,
                end_at=end_at,
            )
            appointments.append(appointment)
            self.stdout.write(f'    [+] Creat: Appointment {appointment.id} - {item.name} (activ)')
        
        # Programări în viitor
        for i, user in enumerate(users[:2]):
            start_at = now + timedelta(days=1, hours=10+i)
            end_at = start_at + timedelta(hours=2)
            item = items[(i+4) % len(items)]
            
            # Asociază cu o cerere aprobată dacă există
            approved_request = None
            if requests:
                approved_requests = [r for r in requests if r.status == Request.APPROVED]
                if approved_requests:
                    approved_request = approved_requests[i % len(approved_requests)]
            
            appointment = Appointment.objects.create(
                user=user,
                item=item,
                start_at=start_at,
                end_at=end_at,
                request=approved_request,
            )
            appointments.append(appointment)
            self.stdout.write(f'    [+] Creat: Appointment {appointment.id} - {item.name} (viitor)')
        
        # Programări care se suprapun (pentru testare ExclusionConstraint)
        # Vom crea o programare care se suprapune cu una existentă
        # Aceasta ar trebui să eșueze dacă încercăm să o creăm manual
        # (nu o creăm aici pentru că ar eșua)
        
        return appointments

    def print_summary(self, roles, teams, users, rooms, categories, items, requests, appointments):
        """Afișează un rezumat al datelor create."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('REZUMAT DATE CREATE:'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Roles: {len(roles)}')
        self.stdout.write(f'  Teams: {len(teams)}')
        self.stdout.write(f'  Users (Employee): {len(users)}')
        self.stdout.write(f'  Rooms: {len(rooms)}')
        self.stdout.write(f'  Item Categories: {len(categories)}')
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

