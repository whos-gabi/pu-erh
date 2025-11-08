"""
ViewSets pentru Requests și Appointments cu logică de business.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Request, Appointment
from .api import RequestSerializer, AppointmentSerializer
from .permissions import IsSuperAdmin, IsOwnerOrSuperAdmin


@extend_schema_view(
    list=extend_schema(tags=['Requests'], summary='Listează cererile'),
    retrieve=extend_schema(tags=['Requests'], summary='Obține detalii despre o cerere'),
    create=extend_schema(tags=['Requests'], summary='Creează o cerere nouă'),
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
        """Creează cererea cu utilizatorul curent."""
        serializer.save(user=self.request.user)
    
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
        
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    - POST/PUT/DELETE: doar SUPERADMIN
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisiuni diferite pentru acțiuni diferite."""
        if self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]
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
        """Creează programarea (doar SUPERADMIN)."""
        # User-ul poate fi setat din serializer sau implicit din request
        if 'user' not in serializer.validated_data:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

