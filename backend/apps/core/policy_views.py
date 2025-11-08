"""
ViewSets pentru gestionarea politicilor organizaționale și a echipelor.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import OrgPolicy, Team
from .permissions import IsSuperAdmin


class OrgPolicyViewSet(viewsets.ViewSet):
    """
    ViewSet pentru gestionarea politicii organizaționale de prezență.
    
    Singleton pattern - există un singur policy pentru organizație.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    @extend_schema(
        tags=['Policy'],
        summary='Obține politica organizațională',
        description='Returnează politica curentă de prezență (default_required_days_per_week).',
    )
    def list(self, request):
        """Returnează politica organizațională."""
        policy = OrgPolicy.get_policy()
        return Response({
            'default_required_days_per_week': policy.default_required_days_per_week,
            'updated_at': policy.updated_at,
        })
    
    @extend_schema(
        tags=['Policy'],
        summary='Actualizează numărul de zile obligatorii',
        description='Setează noul minim global și ridică automat echipele care au un minim mai mic.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'default_required_days_per_week': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 7,
                        'description': 'Numărul de zile obligatorii de prezență fizică pe săptămână'
                    }
                },
                'required': ['default_required_days_per_week']
            }
        },
    )
    @action(detail=False, methods=['post'], url_path='required-days')
    def set_required_days(self, request):
        """
        Setează noul minim global de zile obligatorii.
        
        Ridică automat echipele care au un minim mai mic decât noul minim.
        Nu scade echipele care au valori mai mari.
        """
        new_days = request.data.get('default_required_days_per_week')
        
        if new_days is None:
            return Response(
                {'error': 'default_required_days_per_week este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_days = int(new_days)
            if new_days < 0 or new_days > 7:
                return Response(
                    {'error': 'default_required_days_per_week trebuie să fie între 0 și 7'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'default_required_days_per_week trebuie să fie un număr întreg'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Actualizează policy-ul organizațional
            policy = OrgPolicy.get_policy()
            old_days = policy.default_required_days_per_week
            policy.default_required_days_per_week = new_days
            policy.save()
            
            # Ridică echipele care au un minim mai mic decât noul minim
            # (nu scade pe cele cu valori mai mari)
            updated_teams = Team.objects.filter(
                required_days_per_week__isnull=False,
                required_days_per_week__lt=new_days
            ).update(required_days_per_week=new_days)
            
            return Response({
                'message': f'Policy actualizat de la {old_days} la {new_days} zile/săptămână',
                'default_required_days_per_week': new_days,
                'updated_teams_count': updated_teams,
            }, status=status.HTTP_200_OK)


# TeamPresencePolicyViewSet a fost mutat în TeamViewSet ca action

