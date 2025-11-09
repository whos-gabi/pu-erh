"""
DRF serializers and viewsets pentru gestionarea resurselor.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view, extend_schema_field
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Role,
    Team,
    RoomCategory,
    Room,
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


class RoomCategorySerializer(serializers.ModelSerializer):
    """Serializer for RoomCategory model."""
    class Meta:
        model = RoomCategory
        fields = ['id', 'code', 'name']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    category = serializers.PrimaryKeyRelatedField(queryset=RoomCategory.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'code', 'name', 'category', 'category_name', 'capacity']


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""
    class Meta:
        model = Item
        fields = ['id', 'name', 'status', 'meta']


class RequestSerializer(serializers.ModelSerializer):
    """Serializer for Request model."""
    user = serializers.CharField(source='user.username', read_only=True)
    room_code = serializers.CharField(write_only=True, help_text="Codul camerei (ex: 'meetingRoom1', 'beerPointArea', 'meetingLarge1')")
    roomCode = serializers.SerializerMethodField(read_only=True, help_text="Codul camerei")
    decided_by = serializers.CharField(source='decided_by.username', read_only=True, allow_null=True)
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_roomCode(self, obj) -> str | None:
        """Returnează codul camerei folosind doar room_id pentru a evita loop-uri."""
        # Folosim doar room_id pentru a evita accesarea obiectului room
        # care ar putea cauza loop-uri infinite
        if not hasattr(obj, 'room_id') or not obj.room_id:
            return None
        
        # Folosim cache-ul din context pentru a evita query-uri multiple
        if hasattr(self, '_room_cache'):
            room_cache = self._room_cache
        else:
            room_cache = {}
            self._room_cache = room_cache
        
        # Dacă avem room_id în cache, folosim-l
        if obj.room_id in room_cache:
            return room_cache[obj.room_id]
        
        # Dacă nu, încercăm să obținem codul direct din baza de date
        # fără a accesa obiectul room
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT code FROM core_room WHERE id = %s", [obj.room_id])
                row = cursor.fetchone()
                if row:
                    code = row[0]
                    room_cache[obj.room_id] = code
                    return code
        except Exception:
            pass
        
        return None
    
    class Meta:
        model = Request
        fields = [
            'id', 'user', 'roomCode', 'room_code',
            'status', 'start_date', 'end_date', 'created_at', 'status_changed_at', 'decided_by', 'note'
        ]
        read_only_fields = ['user', 'status', 'created_at', 'status_changed_at', 'decided_by']
    
    def validate_room_code(self, value):
        """Validează că camera cu acest cod există."""
        try:
            room = Room.objects.get(code=value)
            if not hasattr(room, 'category') or not room.category:
                raise serializers.ValidationError(f"Camera '{room.name}' nu are o categorie asociată.")
            return value
        except Room.DoesNotExist:
            raise serializers.ValidationError(f"Camera cu codul '{value}' nu există.")
    
    def create(self, validated_data):
        """Creează request-ul folosind room_code."""
        room_code = validated_data.pop('room_code')
        room = Room.objects.get(code=room_code)
        validated_data['room'] = room
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizează request-ul folosind room_code dacă este furnizat."""
        if 'room_code' in validated_data:
            room_code = validated_data.pop('room_code')
            room = Room.objects.get(code=room_code)
            validated_data['room'] = room
        return super().update(instance, validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model."""
    item_name = serializers.CharField(write_only=True, help_text="Numele item-ului (ex: 'LT-001', 'MON-001')")
    item = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'username', 'item', 'item_name', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['user', 'item', 'created_at']
    
    def validate_item_name(self, value):
        """Validează că item-ul cu acest nume există."""
        try:
            Item.objects.get(name=value)
            return value
        except Item.DoesNotExist:
            raise serializers.ValidationError(f"Item-ul cu numele '{value}' nu există.")
    
    def create(self, validated_data):
        """Creează appointment-ul folosind item_name."""
        item_name = validated_data.pop('item_name')
        item = Item.objects.get(name=item_name)
        validated_data['item'] = item
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizează appointment-ul folosind item_name dacă este furnizat."""
        if 'item_name' in validated_data:
            item_name = validated_data.pop('item_name')
            item = Item.objects.get(name=item_name)
            validated_data['item'] = item
        return super().update(instance, validated_data)
    
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
    list=extend_schema(tags=['RoomCategories'], summary='Listează toate categoriile de camere'),
    retrieve=extend_schema(tags=['RoomCategories'], summary='Obține detalii despre o categorie de camere'),
    create=extend_schema(tags=['RoomCategories'], summary='Creează o categorie de camere nouă'),
    update=extend_schema(tags=['RoomCategories'], summary='Actualizează o categorie de camere'),
    destroy=extend_schema(tags=['RoomCategories'], summary='Șterge o categorie de camere'),
)
class RoomCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet pentru gestionarea categoriilor de camere.
    
    Permisiuni:
    - GET: toți utilizatorii autentificați
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = RoomCategory.objects.all()
    serializer_class = RoomCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


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

