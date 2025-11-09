"""
Django models for Office Smart Appointments Management System.
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, F


class Role(models.Model):
    """User role in the system."""
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'core_role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self) -> str:
        return self.name


class OrgPolicy(models.Model):
    """
    Singleton model pentru politica organizațională de prezență.
    
    Există un singur rând care definește numărul default de zile obligatorii
    de prezență fizică pe săptămână pentru toată organizația.
    """
    default_required_days_per_week = models.PositiveSmallIntegerField(
        default=2,
        help_text='Numărul default de zile obligatorii de prezență fizică pe săptămână'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_org_policy'
        verbose_name = 'Organizational Policy'
        verbose_name_plural = 'Organizational Policies'
    
    def save(self, *args, **kwargs):
        """Asigură că există un singur rând (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Previne ștergerea policy-ului."""
        pass
    
    @classmethod
    def get_policy(cls):
        """Returnează policy-ul organizațional (creează unul default dacă nu există)."""
        policy, created = cls.objects.get_or_create(pk=1)
        return policy
    
    def __str__(self) -> str:
        return f'Org Policy: {self.default_required_days_per_week} zile/săptămână'


class Team(models.Model):
    """Team/Department in the organization."""
    name = models.CharField(max_length=128, unique=True)
    manager = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_teams',
    )
    # Politica de prezență la nivel de echipă
    required_days_per_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Numărul de zile obligatorii de prezență fizică pe săptămână pentru această echipă. '
                  'Dacă este None, se folosește default-ul organizațional.'
    )
    required_weekdays = ArrayField(
        models.IntegerField(),
        null=True,
        blank=True,
        help_text='Lista opțională cu zilele din săptămână când angajații trebuie să fie prezenți. '
                  '0=Luni, 1=Marți, ..., 6=Duminică. Dacă este None, nu există restricții pe zile specifice.'
    )

    class Meta:
        db_table = 'core_team'
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def get_required_days_per_week(self) -> int:
        """
        Returnează numărul de zile obligatorii pentru această echipă.
        
        Fallback: team override → org default
        """
        if self.required_days_per_week is not None:
            return self.required_days_per_week
        return OrgPolicy.get_policy().default_required_days_per_week

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user model extending AbstractUser."""
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'core_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        constraints = [
            # Permite maxim UN rând cu is_superuser = True
            # Aceasta asigură că există un singur SUPERADMIN în sistem
            models.UniqueConstraint(
                fields=['is_superuser'],
                condition=Q(is_superuser=True),
                name='unique_single_superadmin',
            ),
        ]

    def __str__(self) -> str:
        return self.username


class RoomCategory(models.Model):
    """Category for rooms (Meeting Room, Beer Point, Training Room)."""
    name = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=32, unique=True)  # e.g., "MEETING", "BEER", "TRAINING"
    
    class Meta:
        db_table = 'core_room_category'
        verbose_name = 'Room Category'
        verbose_name_plural = 'Room Categories'
    
    def __str__(self) -> str:
        return self.name


class Room(models.Model):
    """Room that can be reserved through Request."""
    code = models.CharField(max_length=32, unique=True)  # e.g., "B1-203"
    name = models.CharField(max_length=128)
    category = models.ForeignKey(
        RoomCategory,
        on_delete=models.PROTECT,
        related_name='rooms',
    )
    capacity = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'core_room'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Item(models.Model):
    """Inventory item. Appointments are made on items."""
    ACTIVE = 'ACTIVE'
    BROKEN = 'BROKEN'
    LOST = 'LOST'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (BROKEN, 'Broken'),
        (LOST, 'Lost'),
    ]

    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=ACTIVE,
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'core_item'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f"{self.name}"


class Request(models.Model):
    """Room reservation request (workflow only for rooms)."""
    WAITING = 'WAITING'
    APPROVED = 'APPROVED'
    DISMISSED = 'DISMISSED'
    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (APPROVED, 'Approved'),
        (DISMISSED, 'Dismissed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requests',
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='requests',
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=WAITING,
    )
    start_date = models.DateTimeField(help_text="Data și ora de început")
    end_date = models.DateTimeField(help_text="Data și ora de sfârșit")
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_at = models.DateTimeField(auto_now=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decided_requests',
    )
    note = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'core_request'
        verbose_name = 'Request'
        verbose_name_plural = 'Requests'
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
        constraints = [
            CheckConstraint(
                check=Q(end_date__gt=F('start_date')),
                name='request_end_date_after_start_date',
            ),
        ]

    def clean(self) -> None:
        """Validate request data."""
        # Validate that end_date is after start_date
        if self.end_date <= self.start_date:
            raise ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )
        
        # Validate that only SUPERADMIN (is_superuser=True) can approve/dismiss requests
        if self.status in {self.APPROVED, self.DISMISSED}:
            if not self.decided_by:
                raise ValidationError(
                    {'decided_by': 'decided_by is required when status is APPROVED or DISMISSED.'}
                )
            if not self.decided_by.is_superuser:
                raise ValidationError(
                    {'decided_by': 'Only SUPERADMIN (is_superuser=True) can approve/dismiss requests.'}
                )

    def save(self, *args, **kwargs) -> None:
        """Save with validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Request {self.id} - {self.room.code} ({self.status})"


class Appointment(models.Model):
    """Appointment on an Item (not Room)."""
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    start_date = models.DateTimeField(help_text="Data și ora de început")
    end_date = models.DateTimeField(help_text="Data și ora de sfârșit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_appointment'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        indexes = [
            models.Index(fields=['item', 'start_date']),
        ]
        constraints = [
            CheckConstraint(
                check=Q(end_date__gt=F('start_date')),
                name='appointment_end_date_after_start_date',
            ),
        ]

    def clean(self) -> None:
        """Validate that end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )

    def save(self, *args, **kwargs) -> None:
        """Save appointment."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Appointment {self.id} - {self.item.name} ({self.start_date} to {self.end_date})"


# ============================================================================
# Configuration Notes
# ============================================================================
# 
# 1. AUTH_USER_MODEL = "core.User"
#    - Set in settings.py
#
# 2. Required INSTALLED_APPS additions:
#    - django.contrib.postgres
#    - rest_framework
#    - drf_spectacular
#    - apps.core (app label is 'core', so AUTH_USER_MODEL uses 'core.User')
#
# 3. Database setup commands:
#    python manage.py makemigrations core
#    python manage.py migrate
#    python manage.py createsuperuser
#
# 4. Access Swagger documentation:
#    - Swagger UI: /api/docs/
#    - ReDoc: /api/redoc/
#    - Schema JSON: /api/schema/
#
# ============================================================================

