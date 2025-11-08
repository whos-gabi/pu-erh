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

from .serializers import UserProfileSerializer, UserSerializer, UserCreateSerializer, UserUpdateSerializer
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin

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
        description="Employee poate vedea doar propriul profil.",
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

