from rest_framework import serializers
from .models import Wishlist, Cart, CartItem, AppVersion
from courses.serializers import CourseSerializer

class WishlistSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    total_courses = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ['id', 'courses', 'total_courses', 'created_at']

    def get_total_courses(self, obj):
        return obj.courses.count()

class CartItemSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    savings = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'course',
            'original_price',
            'price_at_time_of_adding',
            'discount_percentage',
            'is_saved_for_later',
            'savings',
            'added_at'
        ]

class CartSummarySerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)
    coupon_applied = serializers.BooleanField(default=False)
    coupon_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        model = Cart
        fields = [
            'subtotal',
            'discount_amount',
            'total_price',
            'total_items',
            'coupon_applied',
            'coupon_discount',
            'items'
        ]

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ['id', 'version', 'platform', 'is_force_update', 'release_notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']