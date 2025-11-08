"""
DRF serializers and viewsets pentru gestionarea resurselor.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Role,
    Team,
    Room,
    ItemCategory,
    Item,
    Request,
    Appointment,
)
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin


# Serializers
class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    class Meta:
        model = Role
        fields = ['id', 'name']


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""
    manager_username = serializers.CharField(source='manager.username', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'manager', 'manager_username', 'required_days_per_week', 'required_weekdays']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setăm queryset-ul pentru manager după ce Django este inițializat
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['manager'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            required=False,
            allow_null=True
        )


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    class Meta:
        model = Room
        fields = ['id', 'code', 'name', 'capacity', 'features', 'is_active']


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer for ItemCategory model."""
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'slug', 'description']


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=ItemCategory.objects.all())
    room_code = serializers.CharField(source='room.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Item
        fields = ['id', 'room', 'room_code', 'category', 'category_name', 'name', 'status', 'meta']


class RequestSerializer(serializers.ModelSerializer):
    """Serializer for Request model."""
    user = serializers.StringRelatedField(read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    room_code = serializers.CharField(source='room.code', read_only=True)
    decided_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Request
        fields = ['id', 'user', 'room', 'room_code', 'status', 'created_at', 'status_changed_at', 'decided_by', 'note']
        read_only_fields = ['user', 'created_at', 'status_changed_at', 'decided_by']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model."""
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    item_name = serializers.CharField(source='item.name', read_only=True)
    request = serializers.PrimaryKeyRelatedField(
        queryset=Request.objects.all(),
        required=False,
        allow_null=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'username', 'item', 'item_name', 'start_at', 'end_at', 'created_at', 'request']
        read_only_fields = ['created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setăm queryset-ul pentru user după ce Django este inițializat
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['user'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            required=False
        )


# ViewSets
@extend_schema_view(
    list=extend_schema(tags=['Roles'], summary='Listează toate rolurile'),
    retrieve=extend_schema(tags=['Roles'], summary='Obține detalii despre un rol'),
    create=extend_schema(tags=['Roles'], summary='Creează un rol nou'),
    update=extend_schema(tags=['Roles'], summary='Actualizează un rol'),
    destroy=extend_schema(tags=['Roles'], summary='Șterge un rol'),
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea rolurilor.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(tags=['Teams'], summary='Listează toate echipele'),
    retrieve=extend_schema(tags=['Teams'], summary='Obține detalii despre o echipă'),
    create=extend_schema(tags=['Teams'], summary='Creează o echipă nouă'),
    update=extend_schema(tags=['Teams'], summary='Actualizează o echipă'),
    destroy=extend_schema(tags=['Teams'], summary='Șterge o echipă'),
)
class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea echipelor.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        # update_presence_policy are permisiuni custom în metoda respectivă
        return super().get_permissions()
    
    @extend_schema(
        tags=['Teams'],
        summary='Actualizează politica de prezență pentru o echipă',
        description='Actualizează required_days_per_week și/sau required_weekdays pentru echipă. '
                    'Manager-ul echipei poate modifica doar echipa sa. SUPERADMIN poate modifica orice echipă.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'required_days_per_week': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 7,
                        'nullable': True,
                        'description': 'Numărul de zile obligatorii pe săptămână (None = folosește default-ul org)'
                    },
                    'required_weekdays': {
                        'type': 'array',
                        'items': {'type': 'integer', 'minimum': 0, 'maximum': 6},
                        'nullable': True,
                        'description': 'Lista zilelor din săptămână (0=Luni, ..., 6=Duminică)'
                    }
                }
            }
        },
    )
    @action(detail=True, methods=['patch'], url_path='presence-policy')
    def update_presence_policy(self, request, pk=None):
        """
        Actualizează politica de prezență pentru o echipă.
        
        Permisiuni:
        - SUPERADMIN: poate modifica orice echipă
        - Manager-ul echipei: poate modifica doar echipa sa
        
        Permite setarea:
        - required_days_per_week: numărul de zile obligatorii (None = folosește default-ul org)
        - required_weekdays: lista zilelor din săptămână când trebuie să fie prezenți
        """
        team = self.get_object()
        user = request.user
        
        # Verifică permisiunile: SUPERADMIN sau manager-ul echipei
        if not user.is_superuser:
            if not team.manager or team.manager != user:
                return Response(
                    {'error': 'Doar SUPERADMIN sau manager-ul echipei poate modifica politica de prezență.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Validare required_days_per_week
        if 'required_days_per_week' in request.data:
            days = request.data['required_days_per_week']
            if days is not None:
                try:
                    days = int(days)
                    if days < 0 or days > 7:
                        return Response(
                            {'error': 'required_days_per_week trebuie să fie între 0 și 7'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    team.required_days_per_week = days
                except (ValueError, TypeError):
                    return Response(
                        {'error': 'required_days_per_week trebuie să fie un număr întreg sau null'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                team.required_days_per_week = None
        
        # Validare required_weekdays
        if 'required_weekdays' in request.data:
            weekdays = request.data['required_weekdays']
            if weekdays is not None:
                if not isinstance(weekdays, list):
                    return Response(
                        {'error': 'required_weekdays trebuie să fie o listă sau null'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Validare că toate valorile sunt între 0 și 6
                try:
                    weekdays = [int(wd) for wd in weekdays]
                    if not all(0 <= wd <= 6 for wd in weekdays):
                        return Response(
                            {'error': 'required_weekdays trebuie să conțină valori între 0 (Luni) și 6 (Duminică)'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # Elimină duplicatele și sortează
                    team.required_weekdays = sorted(set(weekdays))
                except (ValueError, TypeError):
                    return Response(
                        {'error': 'required_weekdays trebuie să conțină doar numere întregi'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                team.required_weekdays = None
        
        team.save()
        
        serializer = self.get_serializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=['Rooms'], summary='Listează toate camerele'),
    retrieve=extend_schema(tags=['Rooms'], summary='Obține detalii despre o cameră'),
    create=extend_schema(tags=['Rooms'], summary='Creează o cameră nouă'),
    update=extend_schema(tags=['Rooms'], summary='Actualizează o cameră'),
    destroy=extend_schema(tags=['Rooms'], summary='Șterge o cameră'),
)
class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea camerelor.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(tags=['ItemCategories'], summary='Listează toate categoriile'),
    retrieve=extend_schema(tags=['ItemCategories'], summary='Obține detalii despre o categorie'),
    create=extend_schema(tags=['ItemCategories'], summary='Creează o categorie nouă'),
    update=extend_schema(tags=['ItemCategories'], summary='Actualizează o categorie'),
    destroy=extend_schema(tags=['ItemCategories'], summary='Șterge o categorie'),
)
class ItemCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea categoriilor de inventar.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'  # Folosim slug în loc de id pentru URL-uri mai frumoase
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(tags=['Items'], summary='Listează toate item-urile'),
    retrieve=extend_schema(tags=['Items'], summary='Obține detalii despre un item'),
    create=extend_schema(tags=['Items'], summary='Creează un item nou'),
    update=extend_schema(tags=['Items'], summary='Actualizează un item'),
    destroy=extend_schema(tags=['Items'], summary='Șterge un item'),
)
class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea item-urilor de inventar.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


# RequestViewSet și AppointmentViewSet sunt în viewsets.py pentru logică de business


# UserViewSet a fost mutat în auth_views.py pentru gestionarea completă

