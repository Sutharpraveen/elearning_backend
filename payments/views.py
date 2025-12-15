from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import razorpay
from django.db import transaction
from .models import Payment, MultiPayment
from courses.models import Course, Enrollment
from shopping.models import CartItem, Wishlist

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ---------------- Single Course -----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    try:
        course_id = request.data.get('course_id')
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'INR')

        if not course_id or not amount:
            return Response({'status': 'error', 'message': 'Course ID and amount are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'status': 'error', 'message': 'Course not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response({'status': 'error', 'message': 'You already own this course'},
                            status=status.HTTP_400_BAD_REQUEST)

        order_data = {'amount': int(float(amount) * 100), 'currency': currency, 'payment_capture': 1}
        razorpay_order = client.order.create(data=order_data)

        payment = Payment.objects.create(user=request.user, course=course,
                                         razorpay_order_id=razorpay_order['id'],
                                         amount=amount, currency=currency)

        return Response({'status': 'success',
                         'message': 'Payment order created successfully',
                         'data': {'order_id': razorpay_order['id'], 'amount': amount,
                                  'currency': currency, 'key': settings.RAZORPAY_KEY_ID,
                                  'course_id': course.id, 'course_title': course.title}})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'status': 'error', 'message': 'Missing required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)

        params_dict = {'razorpay_order_id': razorpay_order_id,
                       'razorpay_payment_id': razorpay_payment_id,
                       'razorpay_signature': razorpay_signature}

        try:
            client.utility.verify_payment_signature(params_dict)
        except:
            return Response({'status': 'error', 'message': 'Invalid signature'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'completed'
                payment.save()

                course = payment.course
                user = request.user

                Enrollment.objects.get_or_create(user=user, course=course)

                if hasattr(user, 'user_cart'):
                    CartItem.objects.filter(cart=user.user_cart, course=course).delete()

                try:
                    wishlist = Wishlist.objects.get(user=user)
                    wishlist.courses.remove(course)
                except Wishlist.DoesNotExist:
                    pass

                return Response({'status': 'success',
                                 'message': 'Payment verified and course enrolled successfully',
                                 'data': {'payment_id': payment.id,
                                          'order_id': payment.razorpay_order_id,
                                          'status': payment.status,
                                          'course_id': course.id,
                                          'course_title': course.title,
                                          'actions_taken': {'enrolled': True,
                                                            'removed_from_cart': True,
                                                            'removed_from_wishlist': True}}})
        except Payment.DoesNotExist:
            return Response({'status': 'error', 'message': 'Payment record not found'},
                            status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------- Multi Course -----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_multi_payment(request):
    try:
        course_ids = request.data.get('course_ids', [])
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'INR')

        if not course_ids or not amount:
            return Response({'status': 'error', 'message': 'Course IDs and amount are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        courses = Course.objects.filter(id__in=course_ids)
        if not courses.exists():
            return Response({'status': 'error', 'message': 'No valid courses found'},
                            status=status.HTTP_404_NOT_FOUND)

        order_data = {'amount': int(float(amount) * 100), 'currency': currency, 'payment_capture': 1}
        razorpay_order = client.order.create(data=order_data)

        multi_payment = MultiPayment.objects.create(user=request.user,
                                                    razorpay_order_id=razorpay_order['id'],
                                                    amount=amount,
                                                    currency=currency)
        multi_payment.courses.set(courses)
        multi_payment.save()

        return Response({'status': 'success',
                         'message': 'Multi-course payment order created successfully',
                         'data': {'order_id': razorpay_order['id'],
                                  'amount': amount,
                                  'currency': currency,
                                  'key': settings.RAZORPAY_KEY_ID,
                                  'course_ids': [c.id for c in courses],
                                  'course_titles': [c.title for c in courses]}})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_multi_payment(request):
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'status': 'error', 'message': 'Missing required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)

        params_dict = {'razorpay_order_id': razorpay_order_id,
                       'razorpay_payment_id': razorpay_payment_id,
                       'razorpay_signature': razorpay_signature}

        try:
            client.utility.verify_payment_signature(params_dict)
        except:
            return Response({'status': 'error', 'message': 'Invalid signature'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                multi_payment = MultiPayment.objects.get(razorpay_order_id=razorpay_order_id,
                                                         user=request.user)
                multi_payment.razorpay_payment_id = razorpay_payment_id
                multi_payment.razorpay_signature = razorpay_signature
                multi_payment.status = 'completed'
                multi_payment.save()

                courses = multi_payment.courses.all()
                user = request.user

                for course in courses:
                    Enrollment.objects.get_or_create(user=user, course=course)

                    if hasattr(user, 'user_cart'):
                        CartItem.objects.filter(cart=user.user_cart, course=course).delete()

                    try:
                        wishlist = Wishlist.objects.get(user=user)
                        wishlist.courses.remove(course)
                    except Wishlist.DoesNotExist:
                        pass

                return Response({'status': 'success',
                                 'message': 'Multi-course payment verified and courses enrolled successfully',
                                 'data': {'payment_id': multi_payment.id,
                                          'order_id': multi_payment.razorpay_order_id,
                                          'status': multi_payment.status,
                                          'course_ids': [c.id for c in courses],
                                          'course_titles': [c.title for c in courses],
                                          'actions_taken': {'enrolled': True,
                                                            'removed_from_cart': True,
                                                            'removed_from_wishlist': True}}})
        except MultiPayment.DoesNotExist:
            return Response({'status': 'error', 'message': 'MultiPayment record not found'},
                            status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
