from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist, Cart, CartItem, Coupon
from .serializers import WishlistSerializer, CartSummarySerializer, CartItemSerializer
from courses.models import Course
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
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
        try:
            wishlist = self.get_object()
            course_id = request.data.get('course_id')
            
            if not course_id:
                return Response({
                    "status": "error",
                    "message": "course_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": f"Course with id {course_id} does not exist"
                }, status=status.HTTP_404_NOT_FOUND)

            if course in wishlist.courses.all():
                return Response({
                    "status": "info",
                    "message": "Course already in wishlist",
                    "data": WishlistSerializer(wishlist, context={'request': request}).data
                })

            wishlist.courses.add(course)
            return Response({
                "status": "success",
                "message": "Course added to wishlist",
                "data": WishlistSerializer(wishlist, context={'request': request}).data
            })

        except Exception as e:
            import traceback
            print(f"Error adding course to wishlist: {str(e)}")
            print(traceback.format_exc())
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        try:
            wishlist = self.get_object()
            course_id = request.data.get('course_id')
            
            if not course_id:
                return Response({
                    "status": "error",
                    "message": "course_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": f"Course with id {course_id} does not exist"
                }, status=status.HTTP_404_NOT_FOUND)

            if course not in wishlist.courses.all():
                return Response({
                    "status": "error",
                    "message": "Course is not in wishlist"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create cart
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
            
            # Check if course is already in cart
            if CartItem.objects.filter(cart=cart, course=course).exists():
                return Response({
                    "status": "info",
                    "message": "Course already in cart",
                    "data": WishlistSerializer(wishlist, context={'request': request}).data
                })

            # Add course to cart
            CartItem.objects.create(
                cart=cart,
                course=course,
                original_price=course.original_price,
                price_at_time_of_adding=course.discounted_price or course.original_price
            )

            # Remove from wishlist
            wishlist.courses.remove(course)

            return Response({
                "status": "success",
                "message": "Course moved to cart",
                "data": {
                    "wishlist": WishlistSerializer(wishlist, context={'request': request}).data,
                    "cart": CartSummarySerializer(cart, context={'request': request}).data
                }
            })

        except Exception as e:
            import traceback
            print(f"Error moving course to cart: {str(e)}")
            print(traceback.format_exc())
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSummarySerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['get'])
    def get_cart_summary(self, request):
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def add(self, request):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({
                'status': 'error',
                'message': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, id=course_id)
        cart = self.get_object()

        # Check if course is already in cart
        cart_item = CartItem.objects.filter(cart=cart, course=course).first()
        if cart_item:
            return Response({
                'status': 'error',
                'message': 'Course is already in cart'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new cart item
        cart_item = CartItem.objects.create(
            cart=cart,
            course=course,
            original_price=course.original_price,
            price_at_time_of_adding=course.discounted_price or course.original_price,
            discount_percentage=((course.original_price - (course.discounted_price or course.original_price)) / course.original_price) * 100 if course.discounted_price else 0
        )

        serializer = CartItemSerializer(cart_item)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def remove(self, request):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({
                'status': 'error',
                'message': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_object()
        cart_item = get_object_or_404(CartItem, cart=cart, course_id=course_id)
        cart_item.delete()

        return Response({
            'status': 'success',
            'message': 'Course removed from cart'
        })

    @action(detail=False, methods=['post'])
    def save_for_later(self, request):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({
                'status': 'error',
                'message': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_object()
        cart_item = get_object_or_404(CartItem, cart=cart, course_id=course_id)
        cart_item.is_saved_for_later = True
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        cart = self.get_object()
        cart.items.all().delete()
        return Response({
            "status": "success",
            "message": "Cart cleared",
            "data": CartSummarySerializer(cart, context={'request': request}).data
        })

    @action(detail=False, methods=['post'])
    def apply_coupon(self, request):
        try:
            cart = self.get_object()
            coupon_code = request.data.get('coupon_code')
            
            if not coupon_code:
                return Response({
                    "status": "error",
                    "message": "coupon_code is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the same coupon is already applied
            if cart.coupon_code == coupon_code:
                return Response({
                    "status": "info",
                    "message": "This coupon is already applied to your cart"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                coupon = Coupon.objects.get(code=coupon_code)
            except Coupon.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Invalid coupon code"
                }, status=status.HTTP_404_NOT_FOUND)

            if not coupon.is_valid():
                return Response({
                    "status": "error",
                    "message": "Coupon is not valid or has expired"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user has already used this coupon
            if coupon.users_used.filter(id=request.user.id).exists():
                return Response({
                    "status": "error",
                    "message": "You have already used this coupon"
                }, status=status.HTTP_400_BAD_REQUEST)

            if cart.subtotal < coupon.min_purchase_amount:
                return Response({
                    "status": "error",
                    "message": f"Minimum purchase amount of {coupon.min_purchase_amount} required"
                }, status=status.HTTP_400_BAD_REQUEST)

            cart.coupon_code = coupon.code
            cart.coupon_discount = coupon.discount_percentage
            cart.save()

            # Add user to coupon users and increment usage
            coupon.users_used.add(request.user)
            coupon.used_count += 1
            coupon.save()

            return Response({
                "status": "success",
                "message": "Coupon applied successfully",
                "data": {
                    "coupon_code": coupon.code,
                    "discount_percentage": coupon.discount_percentage,
                    "coupon_discount_amount": cart.coupon_discount_amount,
                    "subtotal": cart.subtotal,
                    "total_discount_amount": cart.total_discount_amount,
                    "total_price": cart.total_price
                }
            })

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def move_to_cart(self, request):
        try:
            cart = self.get_object()
            course_id = request.data.get('course_id')
            
            try:
                cart_item = CartItem.objects.get(cart=cart, course_id=course_id)
                cart_item.is_saved_for_later = False
                cart_item.save()
                
                return Response({
                    "status": "success",
                    "message": "Course moved to cart",
                    "data": CartSummarySerializer(cart, context={'request': request}).data
                })
            except CartItem.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Course not found"
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def remove_coupon(self, request):
        try:
            cart = self.get_object()
            
            if not cart.coupon_code:
                return Response({
                    "status": "error",
                    "message": "No coupon applied to cart"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the coupon and decrease its usage count
            try:
                coupon = Coupon.objects.get(code=cart.coupon_code)
                coupon.used_count = max(0, coupon.used_count - 1)  # Don't go below 0
                coupon.save()
            except Coupon.DoesNotExist:
                pass  # Coupon might have been deleted, that's okay

            # Clear coupon from cart
            cart.coupon_code = None
            cart.coupon_discount = 0
            cart.save()

            return Response({
                "status": "success",
                "message": "Coupon removed successfully",
                "data": {
                    "subtotal": cart.subtotal,
                    "total_discount_amount": cart.total_discount_amount,
                    "total_price": cart.total_price
                }
            })

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_saved_items(self, request):
        try:
            cart = self.get_object()
            saved_items = cart.items.filter(is_saved_for_later=True)
            
            return Response({
                "status": "success",
                "data": {
                    "total_saved_items": saved_items.count(),
                    "items": CartItemSerializer(saved_items, many=True, context={'request': request}).data
                }
            })

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_course_status(request, course_id):
    user = request.user

    # Check if course exists
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)

    # Check in cart
    in_cart = CartItem.objects.filter(cart__user=user, course=course).exists()

    # Check in wishlist
    in_wishlist = False
    if hasattr(user, 'wishlist'):
        in_wishlist = user.wishlist.courses.filter(id=course_id).exists()

    return Response({
        "in_cart": in_cart,
        "in_wishlist": in_wishlist
    })