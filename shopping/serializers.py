from rest_framework import serializers
from .models import Wishlist, Cart, CartItem
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
    item_discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    coupon_discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_discount_amount = serializers.DecimalField(
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
    coupon_applied = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(read_only=True)
    coupon_discount = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            'subtotal',
            'item_discount_amount',
            'coupon_discount_amount',
            'total_discount_amount',
            'total_price',
            'total_items',
            'coupon_applied',
            'coupon_code',
            'coupon_discount',
            'items'
        ]

    def get_coupon_applied(self, obj):
        return bool(obj.coupon_code and obj.coupon_discount > 0)