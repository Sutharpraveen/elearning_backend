from django.contrib import admin
from .models import Payment, MultiPayment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'amount', 'status', 'razorpay_order_id')
    list_filter = ('status',)
    search_fields = ('user__username', 'razorpay_order_id')

@admin.register(MultiPayment)
class MultiPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'razorpay_order_id')
    list_filter = ('status',)
    search_fields = ('user__username', 'razorpay_order_id')
    filter_horizontal = ('courses',)