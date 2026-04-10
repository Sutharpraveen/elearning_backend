from django.contrib import admin
from .models import Payment, MultiPayment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'user', 'course', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['razorpay_order_id', 'user__username', 'user__email', 'course__title']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(MultiPayment)
class MultiPaymentAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'user', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['razorpay_order_id', 'user__username', 'user__email']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at']
    filter_horizontal = ['courses']
    ordering = ['-created_at']
