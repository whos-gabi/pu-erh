"""
Django admin configuration for core models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Role,
    Team,
    User,
    Room,
    ItemCategory,
    Item,
    Request,
    Appointment,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for Role model."""
    list_display = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""
    list_display = ('name', 'manager')


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


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin for Room model."""
    list_display = ('code', 'name', 'capacity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    """Admin for ItemCategory model."""
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin for Item model."""
    list_display = ('id', 'name', 'category', 'room', 'status')
    list_filter = ('status', 'category', 'room')
    search_fields = ('name', 'room__code', 'room__name')


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin for Request model."""
    list_display = ('id', 'room', 'user', 'status', 'created_at', 'decided_by')
    list_filter = ('status', 'created_at')
    search_fields = ('room__code', 'user__username')
    readonly_fields = ('created_at', 'status_changed_at')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for Appointment model."""
    list_display = ('id', 'item', 'user', 'start_at', 'end_at', 'created_at')
    list_filter = ('start_at', 'created_at')
    search_fields = ('item__name', 'user__username')
    readonly_fields = ('created_at', 'time_range')

