from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'type',
        'message',
        'is_read',
        'created_at',
    )

    list_filter = (
        'type',
        'is_read',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'message',
    )

    ordering = (
        '-created_at',
    )