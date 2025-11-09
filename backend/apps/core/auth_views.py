"""
ViewSets și Views pentru autentificare și gestionarea profilului.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

from .serializers import UserProfileSerializer, UserSerializer, UserCreateSerializer, UserUpdateSerializer
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin
from .models import Appointment, Request
from .api import AppointmentSerializer, RequestSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizat pentru JWT Token.
    
    Adaugă informații suplimentare în răspuns (ex: is_superuser).
    """
    
    @classmethod
    def get_token(cls, user):
        """Creează token-ul JWT cu informații despre utilizator."""
        token = super().get_token(user)
        # Adaugă informații suplimentare în token
        token['username'] = user.username
        token['is_superuser'] = user.is_superuser
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View pentru obținerea token-ului JWT (login).
    
    Endpoint: POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Obține profilul utilizatorului curent",
        description="Returnează informațiile despre utilizatorul autentificat.",
        tags=['Auth'],
    ),
    put=extend_schema(
        summary="Actualizează profilul utilizatorului curent",
        description="Permite actualizarea propriilor informații (email, first_name, last_name).",
        tags=['Auth'],
    ),
    patch=extend_schema(
        summary="Actualizează parțial profilul utilizatorului curent",
        description="Permite actualizarea parțială a propriilor informații.",
        tags=['Auth'],
    ),
)
class MeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea profilului utilizatorului curent.
    
    Endpoint: /api/me/
    
    Permisiuni:
    - GET: orice utilizator autentificat
    - PUT/PATCH: doar propriul profil
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']  # Doar read și update
    
    def get_queryset(self):
        """Returnează doar utilizatorul curent."""
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        """Returnează utilizatorul curent."""
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Actualizează profilul utilizatorului curent."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listează toți utilizatorii",
        description="Doar SUPERADMIN poate vedea lista completă.",
        tags=['Users'],
    ),
    retrieve=extend_schema(
        summary="Obține detalii despre un utilizator",
        description="Orice utilizator autentificat poate accesa acest endpoint. Returnează informații despre utilizator, "
                    "inclusiv appointments și requests împărțite în trecut/azi/viitor. "
                    "Pentru fiecare appointment: numele item-ului. "
                    "Pentru fiecare request: numele room-ului. "
                    "Include toate cererile indiferent de status. "
                    "Include detalii despre echipă (echipa, coechipieri, manager).",
        tags=['Users'],
        responses={
            200: {
                'description': 'Detalii despre utilizator cu appointments și requests organizate',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'appointments': {
                                    'type': 'object',
                                    'properties': {
                                        'past': {'type': 'array', 'items': {'type': 'object'}},
                                        'today': {'type': 'array', 'items': {'type': 'object'}},
                                        'future': {'type': 'array', 'items': {'type': 'object'}}
                                    }
                                },
                                'requests': {
                                    'type': 'object',
                                    'properties': {
                                        'past': {'type': 'array', 'items': {'type': 'object'}},
                                        'today': {'type': 'array', 'items': {'type': 'object'}},
                                        'future': {'type': 'array', 'items': {'type': 'object'}}
                                    }
                                },
                                'team_details': {'type': 'object'}
                            }
                        }
                    }
                }
            },
            404: {'description': 'User nu a fost găsit'}
        }
    ),
    create=extend_schema(
        summary="Creează un nou utilizator",
        description="Doar SUPERADMIN poate crea utilizatori noi.",
        tags=['Users'],
    ),
    update=extend_schema(
        summary="Actualizează un utilizator",
        description="SUPERADMIN poate actualiza orice utilizator.",
        tags=['Users'],
    ),
    partial_update=extend_schema(
        summary="Actualizează parțial un utilizator",
        description="SUPERADMIN poate actualiza orice utilizator.",
        tags=['Users'],
    ),
    destroy=extend_schema(
        summary="Șterge un utilizator",
        description="Doar SUPERADMIN poate șterge utilizatori.",
        tags=['Users'],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea utilizatorilor.
    
    Endpoint: /api/users/
    
    Permisiuni:
    - List: orice utilizator autentificat (pentru funcționalitatea de prieteni)
    - Retrieve: orice utilizator autentificat (pentru funcționalitatea de prieteni)
    - Create/Update/Delete: doar SUPERADMIN
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Returnează serializer-ul corespunzător acțiunii."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Returnează permisiunile corespunzătoare acțiunii."""
        if self.action in ['list', 'retrieve']:
            # List și Retrieve: orice utilizator autentificat
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Create/Update/Delete: doar SUPERADMIN
            return [IsSuperAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Returnează toți utilizatorii pentru orice user autentificat."""
        # Orice user autentificat poate vedea toți utilizatorii
        return User.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Returnează detalii despre utilizator, inclusiv:
        - Appointments și requests împărțite în trecut/azi/viitor
        - Pentru fiecare appointment: numele item-ului
        - Pentru fiecare request: numele room-ului
        - Include toate cererile indiferent de status
        - Detalii despre echipă (echipa, coechipieri, manager)
        """
        from apps.core.api import AppointmentSerializer, RequestSerializer
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Obține toate appointment-urile și request-urile utilizatorului
        now = timezone.now()
        today = now.date()
        
        # Appointments - include toate
        all_appointments = Appointment.objects.filter(
            user=instance
        ).select_related('item', 'user')
        
        # Requests - include toate indiferent de status
        all_requests = Request.objects.filter(
            user=instance
        ).select_related('room', 'room__category', 'decided_by')
        
        # Organizează appointments în trecut/azi/viitor
        today = now.date()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        past_appointments = all_appointments.filter(end_date__lt=today_start)
        today_appointments = all_appointments.filter(
            start_date__date=today
        )
        future_appointments = all_appointments.filter(start_date__gt=today_end)
        
        # Serializează appointments și adaugă numele item-ului
        def format_appointment(apt):
            apt_data = AppointmentSerializer(apt).data
            apt_data['resource_name'] = apt.item.name if apt.item else None
            apt_data['resource_type'] = 'item'
            return apt_data
        
        past_appointments_data = [format_appointment(apt) for apt in past_appointments]
        today_appointments_data = [format_appointment(apt) for apt in today_appointments]
        future_appointments_data = [format_appointment(apt) for apt in future_appointments]
        
        # Organizează requests în trecut/azi/viitor (bazat pe start_date)
        today = now.date()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        past_requests = all_requests.filter(end_date__lt=today_start)
        today_requests = all_requests.filter(
            start_date__date__lte=today,
            end_date__date__gte=today
        )
        future_requests = all_requests.filter(start_date__gt=today_end)
        
        # Serializează requests și adaugă numele room-ului
        def format_request(req):
            req_data = RequestSerializer(req).data
            req_data['resource_name'] = req.room.name if req.room else None
            req_data['resource_type'] = 'room'
            return req_data
        
        past_requests_data = [format_request(req) for req in past_requests]
        today_requests_data = [format_request(req) for req in today_requests]
        future_requests_data = [format_request(req) for req in future_requests]
        
        # Obține detalii despre echipă
        team_details = None
        if instance.team:
            team = instance.team
            # Obține toți membrii echipei (excluzând utilizatorul curent)
            teammates = User.objects.filter(
                team=team
            ).exclude(id=instance.id).values(
                'id', 'username', 'email', 'first_name', 'last_name'
            )
            
            manager_data = None
            if team.manager:
                manager_data = {
                    'id': team.manager.id,
                    'username': team.manager.username,
                    'email': team.manager.email,
                    'first_name': team.manager.first_name,
                    'last_name': team.manager.last_name,
                }
            
            team_details = {
                'id': team.id,
                'name': team.name,
                'manager': manager_data,
                'teammates': list(teammates),
            }
        
        # Adaugă datele în răspuns organizate în trecut/azi/viitor
        data['appointments'] = {
            'past': past_appointments_data,
            'today': today_appointments_data,
            'future': future_appointments_data,
        }
        data['requests'] = {
            'past': past_requests_data,
            'today': today_requests_data,
            'future': future_requests_data,
        }
        data['team_details'] = team_details
        
        return Response(data)
    
    @extend_schema(
        summary="Obține appointments și requests pentru un user în funcție de dată",
        description="Returnează toate appointment-urile și request-urile unui utilizator pentru o dată specificată.",
        tags=['Users'],
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Data pentru care se caută appointments/requests (format: YYYY-MM-DD)'
            ),
        ],
        responses={
            200: {'description': 'Listă de appointments și requests'},
            400: {'description': 'Parametrul date lipsă sau format invalid'},
            404: {'description': 'User nu a fost găsit'}
        }
    )
    @action(detail=True, methods=['get'], url_path='by-date')
    def by_date(self, request, pk=None):
        """
        Returnează toate appointment-urile și request-urile unui utilizator pentru o dată specificată.
        """
        from apps.core.api import AppointmentSerializer, RequestSerializer
        
        instance = self.get_object()
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
        
        # Filtrează appointments din ziua specificată
        appointments = Appointment.objects.filter(
            user=instance,
            start_date__date=target_date
        ).select_related('item', 'user')
        
        # Filtrează requests din ziua specificată (toate statusurile)
        # Un request este relevant dacă start_date sau end_date se suprapun cu ziua target
        requests = Request.objects.filter(
            user=instance
        ).filter(
            start_date__date__lte=target_date,
            end_date__date__gte=target_date
        ).select_related('room', 'room__category', 'decided_by')
        
        # Serializează și adaugă numele resursei pentru fiecare
        appointments_data = []
        for apt in appointments:
            apt_data = AppointmentSerializer(apt).data
            apt_data['resource_name'] = apt.item.name if apt.item else None
            apt_data['resource_type'] = 'item'
            appointments_data.append(apt_data)
        
        requests_data = []
        for req in requests:
            req_data = RequestSerializer(req).data
            req_data['resource_name'] = req.room.name if req.room else None
            req_data['resource_type'] = 'room'
            requests_data.append(req_data)
        
        return Response({
            'user_id': instance.id,
            'username': instance.username,
            'date': target_date.isoformat(),
            'appointments': appointments_data,
            'requests': requests_data,
            'total_appointments': len(appointments_data),
            'total_requests': len(requests_data),
            'total': len(appointments_data) + len(requests_data)
        })

