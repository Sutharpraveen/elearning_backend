from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import razorpay
import hmac
import hashlib
from .models import Payment
from courses.models import Course
from django.db import transaction
from shopping.models import CartItem, Wishlist

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    try:
        course_id = request.data.get('course_id')
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'INR')

        if not course_id or not amount:
            return Response({
                'status': 'error',
                'message': 'Course ID and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user already owns the course
        if course in request.user.enrolled_courses.all():
            return Response({
                'status': 'error',
                'message': 'You already own this course'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create Razorpay order
        order_data = {
            'amount': int(float(amount) * 100),  # Convert to paise
            'currency': currency,
            'payment_capture': 1
        }
        
        razorpay_order = client.order.create(data=order_data)

        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=razorpay_order['id'],
            amount=amount,
            currency=currency
        )

        return Response({
            'status': 'success',
            'message': 'Payment order created successfully',
            'data': {
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': currency,
                'key': settings.RAZORPAY_KEY_ID,
                'course_id': course.id,
                'course_title': course.title
            }
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({
                'status': 'error',
                'message': 'Missing required parameters'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Invalid signature'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update payment record and handle post-payment actions
        try:
            with transaction.atomic():
                payment = Payment.objects.get(
                    razorpay_order_id=razorpay_order_id,
                    user=request.user
                )
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'completed'
                payment.save()

                course = payment.course
                user = request.user

                # 1. Add course to user's enrollments
                user.enrolled_courses.add(course)

                # 2. Remove course from cart if it exists
                if hasattr(user, 'user_cart'):
                    CartItem.objects.filter(cart=user.user_cart, course=course).delete()

                # 3. Remove course from wishlist if it exists
                try:
                    wishlist = Wishlist.objects.get(user=user)
                    wishlist.courses.remove(course)
                except Wishlist.DoesNotExist:
                    pass

                return Response({
                    'status': 'success',
                    'message': 'Payment verified and course enrolled successfully',
                    'data': {
                        'payment_id': payment.id,
                        'order_id': payment.razorpay_order_id,
                        'status': payment.status,
                        'course_id': course.id,
                        'course_title': course.title,
                        'actions_taken': {
                            'enrolled': True,
                            'removed_from_cart': True,
                            'removed_from_wishlist': True
                        }
                    }
                })

        except Payment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Payment record not found'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
