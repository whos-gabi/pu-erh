"""
Django models for Office Smart Appointments Management System.
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import ArrayField, DateTimeRangeField
from django.contrib.postgres.indexes import GistIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, F
from psycopg2.extras import DateTimeTZRange


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


class Room(models.Model):
    """Room that can be reserved through Request."""
    code = models.CharField(max_length=32, unique=True)  # e.g., "B1-203"
    name = models.CharField(max_length=128)
    capacity = models.IntegerField(null=True, blank=True)
    features = models.JSONField(default=dict, blank=True)  # e.g., {"projector": True}
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_room'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ItemCategory(models.Model):
    """Category for inventory items."""
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'core_item_category'
        verbose_name = 'Item Category'
        verbose_name_plural = 'Item Categories'

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    """Inventory item in a room. Appointments are made on items."""
    ACTIVE = 'ACTIVE'
    BROKEN = 'BROKEN'
    LOST = 'LOST'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (BROKEN, 'Broken'),
        (LOST, 'Lost'),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='items',
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name='items',
    )
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
            models.Index(fields=['room', 'status']),
        ]

    def __str__(self) -> str:
        if self.room:
            return f"{self.name} ({self.room.code})"
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

    def clean(self) -> None:
        """Validate that only SUPERADMIN (is_superuser=True) can approve/dismiss requests."""
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
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    time_range = DateTimeRangeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    request = models.ForeignKey(
        Request,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )

    class Meta:
        db_table = 'core_appointment'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        indexes = [
            models.Index(fields=['item', 'start_at']),
            GistIndex(fields=['time_range']),
        ]
        constraints = [
            CheckConstraint(
                check=Q(end_at__gt=F('start_at')),
                name='appointment_end_after_start',
            ),
            ExclusionConstraint(
                name='exclude_overlap_per_item',
                expressions=[
                    ('item', '='),
                    ('time_range', '&&'),
                ],
            ),
        ]

    def clean(self) -> None:
        """Validate that end_at is after start_at."""
        if self.end_at <= self.start_at:
            raise ValidationError(
                {'end_at': 'end_at must be after start_at.'}
            )

    def save(self, *args, **kwargs) -> None:
        """Save appointment and sync time_range with start_at/end_at (inclusive bounds)."""
        # Sync time_range: [start_at, end_at] with inclusive bounds
        if self.start_at and self.end_at:
            self.time_range = DateTimeTZRange(
                lower=self.start_at,
                upper=self.end_at,
                bounds='[]',  # Inclusive bounds
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Appointment {self.id} - {self.item.name} ({self.start_at} to {self.end_at})"


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

