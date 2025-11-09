"""
Django admin configuration for core models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Role,
    Team,
    User,
    RoomCategory,
    Room,
    Item,
    Request,
    Appointment,
    OrgPolicy,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for Role model."""
    list_display = ('name',)


@admin.register(OrgPolicy)
class OrgPolicyAdmin(admin.ModelAdmin):
    """Admin for OrgPolicy model."""
    list_display = ('default_required_days_per_week', 'updated_at')
    
    def has_add_permission(self, request):
        """Previne crearea de multiple policy-uri."""
        return not OrgPolicy.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Previne ștergerea policy-ului."""
        return False


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""
    list_display = ('name', 'manager', 'required_days_per_week', 'required_weekdays')
    list_filter = ('required_days_per_week',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extended User admin with role and team."""
    list_display = ('username', 'email', 'role', 'team', 'is_staff', 'is_active')
    list_filter = ('role', 'team', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'team')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'team')}),
    )


@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    """Admin for RoomCategory model."""
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin for Room model."""
    list_display = ('code', 'name', 'category', 'capacity')
    list_filter = ('category',)
    search_fields = ('code', 'name')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin for Item model."""
    list_display = ('id', 'name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin for Request model."""
    list_display = ('id', 'room', 'user', 'status', 'start_date', 'end_date', 'created_at', 'decided_by')
    list_filter = ('status', 'created_at')
    search_fields = ('room__code', 'user__username')
    readonly_fields = ('created_at', 'status_changed_at')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for Appointment model."""
    list_display = ('id', 'item', 'user', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'created_at')
    search_fields = ('item__name', 'user__username')
    readonly_fields = ('created_at',)

