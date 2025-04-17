from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist, Cart, CartItem
from .serializers import WishlistSerializer, CartSerializer
from courses.models import Course

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_object(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    @action(detail=False, methods=['post'])
    def add_course(self, request):
        wishlist = self.get_object()
        course_id = request.data.get('course_id')
        
        try:
            course = Course.objects.get(id=course_id)
            if course not in wishlist.courses.all():
                wishlist.courses.add(course)
                return Response({
                    "status": "success",
                    "message": "Course added to wishlist",
                    "data": WishlistSerializer(wishlist, context={'request': request}).data
                })
            return Response({
                "status": "info",
                "message": "Course already in wishlist",
                "data": WishlistSerializer(wishlist, context={'request': request}).data
            })
        except Course.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove_course(self, request):
        wishlist = self.get_object()
        course_id = request.data.get('course_id')
        wishlist.courses.remove(course_id)
        return Response({
            "status": "success",
            "message": "Course removed from wishlist",
            "data": WishlistSerializer(wishlist, context={'request': request}).data
        })

    @action(detail=False, methods=['post'])
    def move_to_cart(self, request):
        wishlist = self.get_object()
        course_id = request.data.get('course_id')
        
        try:
            course = Course.objects.get(id=course_id)
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            CartItem.objects.get_or_create(
                cart=cart,
                course=course,
                defaults={'price_at_time_of_adding': course.price}
            )
            wishlist.courses.remove(course)
            return Response({
                "status": "success",
                "message": "Course moved to cart",
                "data": WishlistSerializer(wishlist, context={'request': request}).data
            })
        except Course.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_course(self, request):
        cart = self.get_object()
        course_id = request.data.get('course_id')
        
        try:
            course = Course.objects.get(id=course_id)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                course=course,
                defaults={'price_at_time_of_adding': course.price}
            )
            return Response({
                "status": "success",
                "message": "Course added to cart",
                "data": CartSerializer(cart, context={'request': request}).data
            })
        except Course.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Course not found"
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove_course(self, request):
        cart = self.get_object()
        course_id = request.data.get('course_id')
        CartItem.objects.filter(cart=cart, course_id=course_id).delete()
        return Response({
            "status": "success",
            "message": "Course removed from cart",
            "data": CartSerializer(cart, context={'request': request}).data
        })

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        cart = self.get_object()
        cart.cart_items.all().delete()
        return Response({
            "status": "success",
            "message": "Cart cleared",
            "data": CartSerializer(cart, context={'request': request}).data
        })