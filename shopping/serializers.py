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

    class Meta:
        model = CartItem
        fields = ['id', 'course', 'course_id', 'price_at_time_of_adding', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items', 'created_at']