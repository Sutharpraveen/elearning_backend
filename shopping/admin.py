from django.contrib import admin
from .models import Wishlist, Cart, CartItem, Coupon

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_courses', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')

    def total_courses(self, obj):
        return obj.courses.count()
    total_courses.short_description = 'Total Courses'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'subtotal', 'discount_amount', 'total_price', 'created_at')
    search_fields = ('user__email', 'coupon_code')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('created_at',)

    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'course', 'original_price', 'price_at_time_of_adding', 
                   'discount_percentage', 'is_saved_for_later', 'added_at')
    search_fields = ('cart__user__email', 'course__title')
    list_filter = ('is_saved_for_later', 'added_at')
    readonly_fields = ('added_at',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'is_active', 'start_date', 'end_date', 
                   'usage_limit', 'used_count', 'created_at')
    search_fields = ('code', 'description')
    list_filter = ('is_active', 'start_date', 'end_date')
    readonly_fields = ('used_count', 'created_at', 'updated_at')