from django.contrib import admin
from .models import DetectionHistory, Payment, Subscription




# -------- DETECTION HISTORY ADMIN --------
@admin.register(DetectionHistory)
class DetectionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'result', 'confidence', 'created_at')
    list_filter = ('result', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_months', 'amount', 'started_at', 'expires_at', 'is_active')
    list_filter = ('plan_months', 'is_active', 'expires_at')
    search_fields = ('user__username',)
    ordering = ('-started_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('user__username', 'transaction_id', 'upi_id')
    ordering = ('-created_at',)
