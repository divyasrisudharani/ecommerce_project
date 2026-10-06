from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'order',
        'amount',
        'payment_method',
        'transaction_id',
        'status',
        'created_at',
    )

    list_filter = (
        'payment_method',
        'status',
    )

    search_fields = (
        'transaction_id',
        'order__id',
    )

    ordering = (
        '-created_at',
    )