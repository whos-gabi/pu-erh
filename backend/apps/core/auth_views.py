"""
ViewSets și Views pentru autentificare și gestionarea profilului.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth import get_user_model
from django.utils import timezone

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
        description="Employee poate vedea doar propriul profil. Returnează informații despre utilizator, "
                    "inclusiv appointments și requests împărțite în trecut/prezent, categoria item-ului "
                    "pentru fiecare appointment și request, și detalii despre echipă (echipa, coechipieri, manager).",
        tags=['Users'],
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
    - List: doar SUPERADMIN
    - Retrieve: Employee doar propriul profil, SUPERADMIN orice
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
        if self.action == 'list':
            # List: doar SUPERADMIN
            return [IsSuperAdmin()]
        elif self.action == 'retrieve':
            # Retrieve: Employee doar propriul profil, SUPERADMIN orice
            return [IsOwnerOrSuperAdmin()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Create/Update/Delete: doar SUPERADMIN
            return [IsSuperAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filtrează queryset-ul în funcție de permisiuni."""
        user = self.request.user
        
        # SUPERADMIN vede tot
        if user.is_superuser:
            return User.objects.all()
        
        # Employee vede doar propriul profil
        return User.objects.filter(id=user.id)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Returnează detalii despre utilizator, inclusiv:
        - Appointments și requests împărțite în trecut/prezent
        - Categoria item-ului pentru fiecare appointment și request
        - Detalii despre echipă (echipa, coechipieri, manager)
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Obține toate appointment-urile și request-urile utilizatorului
        now = timezone.now()
        
        # Appointments
        all_appointments = Appointment.objects.filter(
            user=instance
        ).select_related('item', 'item__category', 'request', 'user')
        
        # Requests
        all_requests = Request.objects.filter(
            user=instance
        ).select_related('room', 'decided_by').prefetch_related('appointments', 'appointments__item', 'appointments__item__category')
        
        # Împarte appointments în trecut și prezent
        past_appointments = all_appointments.filter(end_at__lt=now)
        present_appointments = all_appointments.filter(end_at__gte=now)
        
        # Serializează appointments
        past_appointments_data = AppointmentSerializer(past_appointments, many=True).data
        present_appointments_data = AppointmentSerializer(present_appointments, many=True).data
        
        # Pentru requests, trebuie să determinăm categoria
        # O request este pentru o cameră, dar categoria vine de la item-urile din cameră
        # sau de la appointment-urile asociate cu request-ul
        def get_request_category(request_obj):
            """Obține categoria pentru un request."""
            # Încearcă să obțină categoria din appointment-urile asociate (folosind prefetch)
            appointments_for_request = request_obj.appointments.all()
            if appointments_for_request.exists():
                first_appointment = appointments_for_request[0]
                if first_appointment.item and first_appointment.item.category:
                    return {
                        'id': first_appointment.item.category.id,
                        'name': first_appointment.item.category.name,
                        'slug': first_appointment.item.category.slug
                    }
            
            # Dacă nu există appointment-uri, încearcă să obțină categoria din primul item al camerei
            if request_obj.room:
                first_item = request_obj.room.items.select_related('category').first()
                if first_item and first_item.category:
                    return {
                        'id': first_item.category.id,
                        'name': first_item.category.name,
                        'slug': first_item.category.slug
                    }
            
            return None
        
        # Serializează requests și adaugă categoria
        # Pentru requests, determinăm trecut/prezent bazat pe appointment-urile asociate
        # sau pe created_at dacă nu există appointment-uri
        past_requests_data = []
        present_requests_data = []
        
        for req in all_requests:
            req_data = RequestSerializer(req).data
            category = get_request_category(req)
            req_data['category'] = category
            
            # Determină dacă request-ul este în trecut sau prezent
            # Verifică dacă există appointment-uri asociate (folosind prefetch)
            appointments_for_req = req.appointments.all()
            if appointments_for_req.exists():
                # Folosește data ultimului appointment pentru a determina trecut/prezent
                last_appointment = max(appointments_for_req, key=lambda apt: apt.end_at)
                is_past = last_appointment.end_at < now
            else:
                # Dacă nu există appointment-uri, folosește created_at
                is_past = req.created_at < now
            
            if is_past:
                past_requests_data.append(req_data)
            else:
                present_requests_data.append(req_data)
        
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
        
        # Adaugă datele în răspuns
        data['appointments'] = {
            'past': past_appointments_data,
            'present': present_appointments_data,
        }
        data['requests'] = {
            'past': past_requests_data,
            'present': present_requests_data,
        }
        data['team_details'] = team_details
        
        return Response(data)

