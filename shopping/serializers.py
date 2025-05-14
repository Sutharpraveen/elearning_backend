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
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    price_at_time_of_adding = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_saved_for_later = serializers.BooleanField(read_only=True)
    savings = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'course', 'course_id', 'original_price', 'price_at_time_of_adding', 
                 'discount_percentage', 'is_saved_for_later', 'savings', 'added_at']

    def get_savings(self, obj):
        return obj.original_price - obj.price_at_time_of_adding

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    coupon_code = serializers.CharField(read_only=True)
    coupon_discount = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_savings = serializers.SerializerMethodField()
    has_saved_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal', 'discount_amount', 'total_price', 
                 'total_items', 'coupon_code', 'coupon_discount', 'total_savings',
                 'has_saved_items', 'created_at']

    def get_total_savings(self, obj):
        return sum(item.original_price - item.price_at_time_of_adding for item in obj.cart_items.all())

    def get_has_saved_items(self, obj):
        return obj.cart_items.filter(is_saved_for_later=True).exists()