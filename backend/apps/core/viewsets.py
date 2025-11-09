"""
ViewSets pentru Requests și Appointments cu logică de business.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.db.models.functions import TruncDate

from .models import Request, Appointment, OrgPolicy
from .api import RequestSerializer, AppointmentSerializer
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin
from apps.notify.services import (
    notify_appointment_summary,
    notify_request_status,
    notify_desk_release_batch,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Requests'], 
        summary='Listează cererile',
        description='Returnează lista de cereri. Employee vede doar propriile cereri, SUPERADMIN vede toate. '
                    'Fiecare cerere include roomCode (ex: meetingRoom1, beerPointArea, meetingLarge1).'
    ),
    retrieve=extend_schema(
        tags=['Requests'], 
        summary='Obține detalii despre o cerere',
        description='Returnează detaliile unei cereri specifice. Include roomCode (ex: meetingRoom1, beerPointArea, meetingLarge1).'
    ),
    create=extend_schema(
        tags=['Requests'], 
        summary='Creează o cerere nouă',
        description='Creează o cerere nouă pentru rezervarea unei camere. Statusul este setat automat la WAITING. '
                    'Room codes disponibile: meetingRoom1, meetingRoom2, meetingRoom3, meetingRoom4, meetingRoom5, '
                    'meetingRoom6, meetingLarge1, meetingLarge2, beerPointArea.',
        request={
            'application/json': {
                'example': {
                    'room_code': 'meetingRoom1',
                    'start_date': '2025-01-15T10:00:00Z',
                    'end_date': '2025-01-15T12:00:00Z',
                    'note': 'Meeting cu echipa de dezvoltare'
                }
            }
        },
        responses={
            201: {
                'description': 'Cerere creată cu succes',
                'content': {
                    'application/json': {
                        'example': {
                            'id': 1,
                            'user': 'john.doe',
                            'roomCode': 'meetingRoom1',
                            'status': 'WAITING',
                            'start_date': '2025-01-15T10:00:00Z',
                            'end_date': '2025-01-15T12:00:00Z',
                            'note': 'Meeting cu echipa de dezvoltare',
                            'created_at': '2025-01-10T08:00:00Z',
                            'status_changed_at': '2025-01-10T08:00:00Z',
                            'decided_by': None
                        }
                    }
                }
            },
            400: {'description': 'Date invalide sau camera nu există. Verifică că room_code este valid (ex: meetingRoom1, beerPointArea).'}
        }
    ),
    update=extend_schema(tags=['Requests'], summary='Actualizează o cerere'),
    destroy=extend_schema(tags=['Requests'], summary='Șterge o cerere'),
)
class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea cererilor de rezervare.
    
    Permisiuni:
    - GET: Employee vede doar propriile cereri, SUPERADMIN vede toate
    - POST: toți utilizatorii autentificați (Employee poate crea)
    - PUT: Employee doar pentru anulare proprie (status -> DISMISSED), SUPERADMIN pentru orice
    - DELETE: doar SUPERADMIN
    """
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action == 'destroy':
            return [IsSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrSuperAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filtrează cererile în funcție de permisiuni."""
        user = self.request.user
        
        # SUPERADMIN vede tot
        if user.is_superuser:
            return Request.objects.all()
        
        # Employee vede doar propriile cereri
        return Request.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Creează cererea cu utilizatorul curent și statusul WAITING."""
        # Statusul este setat automat la WAITING (default din model)
        # dar îl setăm explicit pentru claritate
        serializer.save(user=self.request.user, status=Request.WAITING)
    
    def update(self, request, *args, **kwargs):
        """Actualizează cererea cu validări speciale."""
        instance = self.get_object()
        user = request.user
        
        # Employee poate actualiza doar propriile cereri
        if not user.is_superuser and instance.user != user:
            return Response(
                {'detail': 'Nu ai permisiunea să actualizezi această cerere.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Employee poate doar să anuleze propria cerere (status -> DISMISSED)
        if not user.is_superuser:
            if 'status' in request.data:
                if request.data['status'] != Request.DISMISSED:
                    return Response(
                        {'status': 'Employee poate doar să anuleze propria cerere (status -> DISMISSED).'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Setăm decided_by la utilizatorul curent pentru anulare
                request.data['decided_by'] = user.id
        
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Requests'],
        summary='Aprobă o cerere',
        description='Doar SUPERADMIN poate aproba cereri.',
    )
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def approve(self, request, pk=None):
        """Aprobă o cerere (doar SUPERADMIN)."""
        request_obj = self.get_object()
        
        if request_obj.status != Request.WAITING:
            return Response(
                {'detail': f'Cererea trebuie să fie în status WAITING. Status actual: {request_obj.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request_obj.status = Request.APPROVED
        request_obj.decided_by = request.user
        request_obj.save()
        
        # Trimite notificare prin email după ce statusul este schimbat
        from django.db import transaction
        transaction.on_commit(lambda: notify_request_status(request_obj))
        
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Requests'],
        summary='Respinge o cerere',
        description='Doar SUPERADMIN poate respinge cereri.',
    )
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def dismiss(self, request, pk=None):
        """Respinge o cerere (doar SUPERADMIN)."""
        request_obj = self.get_object()
        
        if request_obj.status != Request.WAITING:
            return Response(
                {'detail': f'Cererea trebuie să fie în status WAITING. Status actual: {request_obj.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request_obj.status = Request.DISMISSED
        request_obj.decided_by = request.user
        request_obj.save()
        
        # Trimite notificare prin email după ce statusul este schimbat
        from django.db import transaction
        transaction.on_commit(lambda: notify_request_status(request_obj))
        
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Requests'],
        summary='Obține request-urile pentru o cameră și o dată',
        description='Returnează toate request-urile care au fost făcute pentru o cameră specificată (după roomCode) '
                    'și pentru o dată specificată (după start_date).',
        parameters=[
            OpenApiParameter(
                name='roomCode',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Codul camerei. Exemple: meetingRoom1, meetingRoom2, meetingRoom3, meetingRoom4, meetingRoom5, meetingRoom6, meetingLarge1, meetingLarge2, beerPointArea'
            ),
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se caută request-urile (format: YYYY-MM-DD). Ex: 2025-01-15'
            ),
        ],
        responses={
            200: {
                'description': 'Lista request-urilor pentru camera și data specificată',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'roomCode': {'type': 'string'},
                                'date': {'type': 'string', 'format': 'date'},
                                'requests': {
                                    'type': 'array',
                                    'items': {'type': 'object'}
                                },
                                'total': {'type': 'integer'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Parametri lipsă sau invalizi'},
            404: {'description': 'Camera nu a fost găsită'}
        }
    )
    @action(detail=False, methods=['get'], url_path='by-room-and-date')
    def by_room_and_date(self, request):
        """
        Returnează toate request-urile care au fost făcute pentru o cameră specificată (după roomCode)
        și pentru o dată specificată (după start_date).
        """
        from apps.core.models import Room
        
        room_code = request.query_params.get('roomCode')
        date_str = request.query_params.get('date')
        
        if not room_code:
            return Response(
                {'error': 'Parametrul "roomCode" este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not date_str:
            return Response(
                {'error': 'Parametrul "date" este obligatoriu (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifică dacă camera există
        try:
            room = Room.objects.get(code=room_code)
        except Room.DoesNotExist:
            return Response(
                {'error': f'Camera cu codul "{room_code}" nu a fost găsită'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parsează data
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format invalid pentru date. Folosește YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrează request-urile după room și start_date
        requests = Request.objects.filter(
            room=room,
            start_date__date=target_date
        ).select_related('user', 'room', 'room__category', 'decided_by')
        
        # Aplică permisiunile: Employee vede doar propriile, SUPERADMIN vede toate
        user = request.user
        if not user.is_superuser:
            requests = requests.filter(user=user)
        
        serializer = self.get_serializer(requests, many=True)
        
        return Response({
            'roomCode': room_code,
            'roomName': room.name,
            'date': target_date.isoformat(),
            'requests': serializer.data,
            'total': len(serializer.data)
        })


@extend_schema_view(
    list=extend_schema(tags=['Appointments'], summary='Listează programările'),
    retrieve=extend_schema(tags=['Appointments'], summary='Obține detalii despre o programare'),
    create=extend_schema(tags=['Appointments'], summary='Creează o programare nouă'),
    update=extend_schema(tags=['Appointments'], summary='Actualizează o programare'),
    destroy=extend_schema(tags=['Appointments'], summary='Șterge o programare'),
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea programărilor.
    
    Permisiuni:
    - GET: Employee vede doar propriile programări, SUPERADMIN vede toate
    - POST: orice utilizator autentificat poate crea programări
    - PUT: orice utilizator autentificat poate actualiza propriile programări
    - DELETE: orice utilizator autentificat poate șterge propriile programări
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        # Orice utilizator autentificat poate face POST/PUT/DELETE
        # (cu validări în metodele respective pentru a asigura că poate modifica doar propriile appointments)
        return super().get_permissions()
    
    def get_queryset(self):
        """Filtrează programările în funcție de permisiuni."""
        user = self.request.user
        
        # SUPERADMIN vede tot
        if user.is_superuser:
            return Appointment.objects.all()
        
        # Employee vede doar propriile programări
        return Appointment.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Creează programarea - orice utilizator autentificat."""
        # User-ul este setat automat la utilizatorul curent
        if 'user' not in serializer.validated_data:
            appointment = serializer.save(user=self.request.user)
        else:
            # Dacă user este specificat, verifică că este utilizatorul curent (sau SUPERADMIN)
            if serializer.validated_data['user'] != self.request.user and not self.request.user.is_superuser:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Nu poți crea programări pentru alți utilizatori.")
            appointment = serializer.save()
        
        # Trimite notificare prin email după ce appointment-ul este creat cu succes
        # Folosim transaction.on_commit pentru a ne asigura că appointment-ul este salvat
        # înainte de a trimite email-ul
        from django.db import transaction
        transaction.on_commit(lambda: notify_appointment_summary(appointment))
    
    def update(self, request, *args, **kwargs):
        """Actualizează programarea - doar proprietarul poate actualiza propria programare."""
        instance = self.get_object()
        user = request.user
        
        # Orice utilizator poate actualiza doar propriile programări
        if instance.user != user:
            return Response(
                {'detail': 'Nu ai permisiunea să actualizezi această programare.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Șterge programarea - doar proprietarul poate șterge propria programare."""
        instance = self.get_object()
        user = request.user
        
        # Orice utilizator poate șterge doar propriile programări
        if instance.user != user:
            return Response(
                {'detail': 'Nu ai permisiunea să ștergi această programare.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Appointments'],
        summary='Listează utilizatorii over-quota pentru birouri',
        description='Caută prin toate appointment-urile pentru birouri din ziua specificată și returnează '
                    'doar utilizatorii care au atins deja numărul obligatoriu de zile fizice în săptămâna de lucru (Luni-Vineri). '
                    'Logica: găsește toate rezervările de birouri din ziua specificată, apoi pentru fiecare user verifică '
                    'dacă a atins deja norma de zile obligatorii în săptămâna de lucru.',
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se verifică (format: YYYY-MM-DD). Ex: 2024-01-15'
            ),
        ],
        responses={
            200: {
                'description': 'Lista utilizatorilor over-quota',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'date': {'type': 'string', 'format': 'date'},
                                'week_start': {'type': 'string', 'format': 'date'},
                                'week_end': {'type': 'string', 'format': 'date'},
                                'over_quota_users': {
                                    'type': 'array',
                                    'items': {'type': 'object'}
                                },
                                'total_over_quota': {'type': 'integer'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Parametrul date lipsă sau format invalid'},
            404: {'description': 'Categoria "birou" nu există'}
        }
    )
    @action(detail=False, methods=['get'], url_path='desk-overquota')
    def desk_overquota(self, request):
        """
        Returnează utilizatorii care au rezervat birou în ziua specificată
        și au atins deja numărul obligatoriu de zile fizice în săptămâna de lucru (Luni-Vineri).
        
        Calcul:
        1. Găsește toate appointment-urile pentru birouri (ItemCategory.slug="birou") în ziua specificată
        2. Pentru fiecare user, calculează numărul de zile distincte din săptămâna de lucru (Luni-Vineri)
           în care au cel puțin o rezervare pe item de tip "birou"
        3. Compară cu required_days (fallback: team override → org default)
        4. Returnează doar userii care au atins deja norma
        
        Notă: Săptămâna de lucru este hardcodată ca Luni-Vineri (5 zile lucrătoare).
        """
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Parametrul "date" este obligatoriu (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format invalid pentru date. Folosește YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Găsește toate appointment-urile în ziua specificată
        # Notă: ItemCategory a fost eliminat, deci nu mai filtram după categorie
        appointments_on_date = Appointment.objects.filter(
            start_date__date=target_date
        ).select_related('user', 'item', 'user__team')
        
        # Calculează săptămâna de lucru (Luni-Vineri)
        # Luni = 0, Vineri = 4, Sâmbătă = 5, Duminică = 6
        days_since_monday = target_date.weekday()  # 0=Luni, 4=Vineri, 5=Sâmbătă, 6=Duminică
        week_start = target_date - timedelta(days=days_since_monday)  # Luni
        week_end = week_start + timedelta(days=4)  # Vineri (săptămâna de lucru: 5 zile)
        
        if not appointments_on_date.exists():
            return Response({
                'date': target_date.isoformat(),
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'over_quota_users': [],
                'total_over_quota': 0,
                'message': 'Nu există rezervări de birouri în această zi'
            })
        
        # Obține policy-ul organizațional
        org_policy = OrgPolicy.get_policy()
        
        over_quota_users = []
        
        # Pentru fiecare user care are rezervare în ziua specificată
        users_with_appointments = set(apt.user for apt in appointments_on_date)
        
        for user in users_with_appointments:
            # Găsește toate appointment-urile ale userului în săptămâna de lucru (Luni-Vineri)
            week_appointments = Appointment.objects.filter(
                user=user,
                start_date__date__gte=week_start,
                start_date__date__lte=week_end
            )
            
            # Numără zilele distincte în care userul are cel puțin o rezervare
            distinct_days = week_appointments.values('start_date__date').distinct().count()
            
            # Determină required_days pentru user (team override → org default)
            if user.team:
                required_days = user.team.get_required_days_per_week()
            else:
                required_days = org_policy.default_required_days_per_week
            
            # Verifică dacă userul a atins deja norma
            if distinct_days >= required_days:
                over_quota_users.append({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'team': user.team.name if user.team else None,
                    'required_days': required_days,
                    'actual_days': distinct_days,
                    'appointments_on_date': [
                        {
                            'id': apt.id,
                            'item': apt.item.name,
                            'start_date': apt.start_date.isoformat(),
                            'end_date': apt.end_date.isoformat(),
                        }
                        for apt in appointments_on_date.filter(user=user)
                    ]
                })
        
        response_data = {
            'date': target_date.isoformat(),
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'over_quota_users': over_quota_users,
            'total_over_quota': len(over_quota_users),
        }
        
        # Trimite notificări prin email pentru utilizatorii over-quota
        # Notă: În producție, ar trebui să existe un user care cere eliberarea
        # Pentru moment, folosim request.user (cel care face request-ul)
        if over_quota_users and request.user:
            from django.db import transaction
            transaction.on_commit(
                lambda: notify_desk_release_batch(
                    target_date,
                    over_quota_users,
                    request.user
                )
            )
        
        return Response(response_data)
    
    @extend_schema(
        tags=['Appointments'],
        summary='Listează toate appointment-urile dintr-o anumită dată',
        description='Returnează toate appointment-urile din ziua specificată.',
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se caută appointment-urile (format: YYYY-MM-DD). Ex: 2024-01-15'
            ),
        ],
        responses={
            200: {
                'description': 'Lista appointment-urilor din ziua specificată',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'date': {'type': 'string', 'format': 'date'},
                                'appointments': {
                                    'type': 'array',
                                    'items': {'type': 'object'}
                                },
                                'total': {'type': 'integer'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Parametrul date lipsă sau format invalid'}
        }
    )
    @action(detail=False, methods=['get'], url_path='by-date')
    def by_date(self, request):
        """
        Returnează toate appointment-urile și request-urile approved din ziua specificată.
        Include și toate cererile care au fost approved pentru ziua respectivă.
        """
        from apps.core.api import RequestSerializer
        
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Parametrul "date" este obligatoriu (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format invalid pentru date. Folosește YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrează appointment-urile din ziua specificată
        appointments = Appointment.objects.filter(
            start_date__date=target_date
        ).select_related('user', 'item')
        
        # Filtrează request-urile approved din ziua specificată
        # Un request este relevant dacă start_date sau end_date se suprapun cu ziua target
        approved_requests = Request.objects.filter(
            status=Request.APPROVED
        ).filter(
            start_date__date__lte=target_date,
            end_date__date__gte=target_date
        ).select_related('user', 'room', 'room__category', 'decided_by')
        
        # Aplică permisiunile: Employee vede doar propriile, SUPERADMIN vede toate
        user = request.user
        if not user.is_superuser:
            appointments = appointments.filter(user=user)
            approved_requests = approved_requests.filter(user=user)
        
        appointments_serializer = self.get_serializer(appointments, many=True)
        requests_serializer = RequestSerializer(approved_requests, many=True)
        
        return Response({
            'date': target_date.isoformat(),
            'appointments': appointments_serializer.data,
            'approved_requests': requests_serializer.data,
            'total_appointments': len(appointments_serializer.data),
            'total_approved_requests': len(requests_serializer.data),
            'total': len(appointments_serializer.data) + len(requests_serializer.data)
        })


class AvailabilityViewSet(viewsets.ViewSet):
    """
    ViewSet pentru verificarea disponibilității resurselor (items/rooms).
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Verifică disponibilitatea items/rooms pentru o dată",
        description="Returnează pentru fiecare item/room dacă e liber sau ocupat. "
                    "Pentru resurse ocupate, indică dacă e ocupată de un teammate și numele teammate-ului.",
        tags=['Availability'],
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='ID-ul utilizatorului pentru care se verifică disponibilitatea'
            ),
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se verifică disponibilitatea (format: YYYY-MM-DD)'
            ),
        ],
        responses={
            200: {'description': 'Listă de resurse cu statusul lor de disponibilitate'},
            400: {'description': 'Parametri lipsă sau invalizi'},
            404: {'description': 'User nu a fost găsit'}
        }
    )
    @action(detail=False, methods=['get'], url_path='check')
    def check_availability(self, request):
        """
        Verifică disponibilitatea items/rooms pentru o dată specificată.
        Returnează liste separate pentru resurse libere și ocupate.
        Pentru resurse ocupate, indică dacă e ocupată de un teammate.
        """
        from apps.core.models import Room, Item, User
        from apps.core.api import RoomSerializer, ItemSerializer
        
        user_id = request.query_params.get('user_id')
        date_str = request.query_params.get('date')
        
        if not user_id:
            return Response(
                {'error': 'Parametrul "user_id" este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not date_str:
            return Response(
                {'error': 'Parametrul "date" este obligatoriu (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User nu a fost găsit'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format invalid pentru date. Folosește YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obține toate items și rooms
        all_items = Item.objects.filter(status=Item.ACTIVE)
        all_rooms = Room.objects.all().select_related('category')
        
        # Obține appointments pentru ziua specificată
        appointments = Appointment.objects.filter(
            start_date__date=target_date
        ).select_related('user', 'item')
        
        # Obține approved requests pentru ziua specificată
        approved_requests = Request.objects.filter(
            status=Request.APPROVED
        ).filter(
            start_date__date__lte=target_date,
            end_date__date__gte=target_date
        ).select_related('user', 'room')
        
        # Verifică dacă user-ul are teammates (din aceeași echipă)
        user_team = target_user.team
        teammate_ids = set()
        if user_team:
            teammates = User.objects.filter(team=user_team).exclude(id=target_user.id)
            teammate_ids = set(teammates.values_list('id', flat=True))
        
        # Verifică disponibilitatea items
        free_items = []
        occupied_items = []
        
        for item in all_items:
            # Verifică dacă item-ul este ocupat în ziua specificată
            item_appointments = [apt for apt in appointments if apt.item_id == item.id]
            
            if not item_appointments:
                # Item-ul este liber
                item_data = ItemSerializer(item).data
                item_data['is_available'] = True
                item_data['occupied_by_teammate'] = False
                item_data['teammate_name'] = None
                free_items.append(item_data)
            else:
                # Item-ul este ocupat
                # Verifică dacă e ocupat de un teammate
                occupied_by_teammate = False
                teammate_name = None
                
                for apt in item_appointments:
                    if apt.user_id in teammate_ids:
                        occupied_by_teammate = True
                        teammate_name = f"{apt.user.first_name} {apt.user.last_name}".strip() or apt.user.username
                        break
                
                item_data = ItemSerializer(item).data
                item_data['is_available'] = False
                item_data['occupied_by_teammate'] = occupied_by_teammate
                item_data['teammate_name'] = teammate_name
                occupied_items.append(item_data)
        
        # Verifică disponibilitatea rooms
        free_rooms = []
        occupied_rooms = []
        
        for room in all_rooms:
            # Verifică dacă room-ul este ocupat în ziua specificată
            room_requests = [req for req in approved_requests if req.room_id == room.id]
            
            if not room_requests:
                # Room-ul este liber
                room_data = RoomSerializer(room).data
                room_data['is_available'] = True
                room_data['occupied_by_teammate'] = False
                room_data['teammate_name'] = None
                free_rooms.append(room_data)
            else:
                # Room-ul este ocupat
                # Verifică dacă e ocupat de un teammate
                occupied_by_teammate = False
                teammate_name = None
                
                for req in room_requests:
                    if req.user_id in teammate_ids:
                        occupied_by_teammate = True
                        teammate_name = f"{req.user.first_name} {req.user.last_name}".strip() or req.user.username
                        break
                
                room_data = RoomSerializer(room).data
                room_data['is_available'] = False
                room_data['occupied_by_teammate'] = occupied_by_teammate
                room_data['teammate_name'] = teammate_name
                occupied_rooms.append(room_data)
        
        return Response({
            'user_id': target_user.id,
            'username': target_user.username,
            'date': target_date.isoformat(),
            'free_items': free_items,
            'occupied_items': occupied_items,
            'free_rooms': free_rooms,
            'occupied_rooms': occupied_rooms,
            'total_free_items': len(free_items),
            'total_occupied_items': len(occupied_items),
            'total_free_rooms': len(free_rooms),
            'total_occupied_rooms': len(occupied_rooms),
        })


class AppAndReqViewSet(viewsets.ViewSet):
    """
    ViewSet pentru combinarea appointments și requests într-un singur endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obține appointments și approved requests pentru o dată",
        description="Returnează toate appointment-urile și request-urile approved din ziua specificată. "
                    "Include și toate cererile care au fost approved pentru ziua respectivă.",
        tags=['Appointments & Requests'],
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se caută appointments și requests (format: YYYY-MM-DD). Ex: 2024-01-15'
            ),
        ],
        responses={
            200: {
                'description': 'Lista appointments și approved requests din ziua specificată',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'date': {'type': 'string', 'format': 'date'},
                                'appointments': {
                                    'type': 'array',
                                    'items': {'type': 'object'}
                                },
                                'approved_requests': {
                                    'type': 'array',
                                    'items': {'type': 'object'}
                                },
                                'total_appointments': {'type': 'integer'},
                                'total_approved_requests': {'type': 'integer'},
                                'total': {'type': 'integer'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Parametrul date lipsă sau format invalid'}
        }
    )
    @action(detail=False, methods=['get'], url_path='by-date')
    def by_date(self, request):
        """
        Returnează toate appointment-urile și request-urile approved din ziua specificată.
        Include și toate cererile care au fost approved pentru ziua respectivă.
        """
        from apps.core.api import RequestSerializer
        
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Parametrul "date" este obligatoriu (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format invalid pentru date. Folosește YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrează appointment-urile din ziua specificată
        appointments = Appointment.objects.filter(
            start_date__date=target_date
        ).select_related('user', 'item')
        
        # Filtrează request-urile approved din ziua specificată
        # Un request este relevant dacă start_date sau end_date se suprapun cu ziua target
        approved_requests = Request.objects.filter(
            status=Request.APPROVED
        ).filter(
            start_date__date__lte=target_date,
            end_date__date__gte=target_date
        ).select_related('user', 'room', 'room__category', 'decided_by')
        
        # Aplică permisiunile: Employee vede doar propriile, SUPERADMIN vede toate
        user = request.user
        if not user.is_superuser:
            appointments = appointments.filter(user=user)
            approved_requests = approved_requests.filter(user=user)
        
        appointments_serializer = AppointmentSerializer(appointments, many=True)
        requests_serializer = RequestSerializer(approved_requests, many=True)
        
        return Response({
            'date': target_date.isoformat(),
            'appointments': appointments_serializer.data,
            'approved_requests': requests_serializer.data,
            'total_appointments': len(appointments_serializer.data),
            'total_approved_requests': len(requests_serializer.data),
            'total': len(appointments_serializer.data) + len(requests_serializer.data)
        })


class ItemOccupancyStatsViewSet(viewsets.ViewSet):
    """
    ViewSet pentru statisticile de ocupabilitate items.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obține statisticile de ocupabilitate pentru un item specific",
        description="Returnează pentru un item specific o listă cu zilele de luni până vineri, "
                    "iar pentru fiecare zi o listă cu perechile (hour, popularity).",
        tags=['Item Occupancy Stats'],
        parameters=[
            OpenApiParameter(
                name='item_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='ID-ul item-ului pentru care se caută statisticile'
            ),
        ],
        responses={
            200: {
                'description': 'Statistici de ocupabilitate pentru item',
                'content': {
                    'application/json': {
                        'example': {
                            'item_id': 2,
                            'item_name': 'scaun1',
                            'weekdays': [
                                {
                                    'weekday': 'Monday',
                                    'hours': [
                                        {'hour': 8, 'popularity': 100},
                                        {'hour': 9, 'popularity': 50}
                                    ]
                                },
                                {
                                    'weekday': 'Tuesday',
                                    'hours': []
                                }
                            ]
                        }
                    }
                }
            },
            400: {'description': 'Parametrul item_id lipsă sau invalid'},
            404: {'description': 'Item nu a fost găsit'}
        }
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """
        Returnează statisticile de ocupabilitate pentru un item specific.
        Pentru item: zilele de luni-vineri, iar pentru fiecare zi: lista de (hour, popularity).
        """
        from django.db import connection
        from apps.core.models import Item
        
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'Parametrul "item_id" este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item_id = int(item_id)
        except ValueError:
            return Response(
                {'error': 'Parametrul "item_id" trebuie să fie un număr întreg'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifică dacă item-ul există
        try:
            item = Item.objects.get(id=item_id, status=Item.ACTIVE)
        except Item.DoesNotExist:
            return Response(
                {'error': f'Item cu ID-ul {item_id} nu a fost găsit sau nu este activ'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Zilele de lucru (luni-vineri)
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # Query pentru a obține statisticile pentru item-ul specificat
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.weekday,
                    s.hour,
                    s.popularity
                FROM core_item_occupancy_stats s
                WHERE s.item_id = %s
                    AND s.weekday IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
                ORDER BY 
                    CASE s.weekday
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                    END,
                    s.hour
            """, [item_id])
            
            rows = cursor.fetchall()
        
        # Inițializează toate zilele cu liste goale
        weekdays_data = []
        for day in weekdays:
            weekdays_data.append({
                'weekday': day,
                'hours': []
            })
        
        # Adaugă datele pentru fiecare zi
        for row in rows:
            weekday, hour, popularity = row
            
            # Găsește ziua în listă
            for day_data in weekdays_data:
                if day_data['weekday'] == weekday:
                    day_data['hours'].append({
                        'hour': hour,
                        'popularity': popularity
                    })
                    break
        
        return Response({
            'item_id': item.id,
            'item_name': item.name,
            'weekdays': weekdays_data
        })

