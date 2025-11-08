from django.contrib import admin
from .models import (
    NotificationEvent,
    EmailOutbox,
    EmailDelivery,
    UserEmailPreference,
)


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'subject_user', 'actor', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('subject_user__username', 'subject_user__email', 'actor__username')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(EmailOutbox)
class EmailOutboxAdmin(admin.ModelAdmin):
    list_display = ('id', 'to', 'template', 'locale', 'scheduled_at', 'sent_at', 'attempts', 'status_display')
    list_filter = ('template', 'locale', 'sent_at', 'scheduled_at')
    search_fields = ('to', 'template', 'event__type')
    readonly_fields = ('id', 'idempotency_key')
    date_hierarchy = 'scheduled_at'
    
    def status_display(self, obj):
        if obj.sent_at:
            return '✓ Trimis'
        elif obj.attempts >= 3:
            return '✗ Eșuat'
        else:
            return '⏳ În așteptare'
    status_display.short_description = 'Status'


@admin.register(EmailDelivery)
class EmailDeliveryAdmin(admin.ModelAdmin):
    list_display = ('outbox', 'status', 'provider_message_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('outbox__to', 'provider_message_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(UserEmailPreference)
class UserEmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'appointment_summary', 'request_status', 'desk_release_ask', 'frequency')
    list_filter = ('appointment_summary', 'request_status', 'desk_release_ask', 'frequency')
    search_fields = ('user__username', 'user__email')
