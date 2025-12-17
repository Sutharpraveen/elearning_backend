from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, LoginSerializer, UserProfileSerializer, UserProfileUpdateSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging
from rest_framework import viewsets
from rest_framework.decorators import action
import os

logger = logging.getLogger(__name__)

# Create your views here.

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Registration successful',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(username=email, password=password)
            
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'user': UserProfileSerializer(user).data
                })
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        try:
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request):
        try:
            serializer = UserProfileSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profile updated successfully',
                    'data': serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        """Delete user account"""
        try:
            user = request.user
            user.delete()
            return Response(
                {"message": "User account deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProfileImageUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        try:
            if 'profile_image' not in request.FILES:
                return Response(
                    {'error': 'Please provide an image file'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            image = request.FILES['profile_image']
            
            # Validate file size (5MB max)
            if image.size > 5 * 1024 * 1024:
                return Response(
                    {'error': 'Image size should not exceed 5MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                return Response(
                    {'error': 'Only JPG, PNG and GIF files are allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = request.user

            # Delete old image if exists
            if user.profile_image:
                try:
                    if os.path.exists(user.profile_image.path):
                        os.remove(user.profile_image.path)
                except Exception as e:
                    print(f"Error deleting old image: {e}")

            # Save new image
            file_name = f"profile_{user.id}_{image.name}"
            file_path = f'user_profiles/{user.id}/{file_name}'
            user.profile_image = file_path
            user.save()

            return Response({
                'message': 'Profile image updated successfully',
                'profile_image': request.build_absolute_uri(user.profile_image.url)
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserPublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Get public profile of any user"""
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserProfileSerializer(user, context={'request': request})
            # Remove sensitive information for public view
            data = serializer.data
            sensitive_fields = ['email', 'phone_number', 'address']
            for field in sensitive_fields:
                data.pop(field, None)
            return Response(data)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change user password"""
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not all([old_password, new_password, confirm_password]):
                return Response(
                    {'error': 'All password fields are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return Response(
                    {'error': 'New passwords do not match'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = request.user

            # Check if old password is correct
            if not user.check_password(old_password):
                return Response(
                    {'error': 'Current password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate new password strength
            if len(new_password) < 8:
                return Response(
                    {'error': 'Password must be at least 8 characters long'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set new password
            user.set_password(new_password)
            user.save()

            return Response({
                'message': 'Password changed successfully'
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user profile statistics"""
        try:
            user = request.user
            from courses.models import Enrollment, Course
            from payments.models import Payment

            # Enrollment statistics
            enrollments = Enrollment.objects.filter(user=user)
            total_enrollments = enrollments.count()
            completed_courses = enrollments.filter(completed=True).count()

            # Course statistics (if instructor)
            created_courses = 0
            total_students = 0
            if user.role == 'instructor':
                created_courses = Course.objects.filter(instructor=user).count()
                total_students = Enrollment.objects.filter(course__instructor=user).count()

            # Payment statistics
            total_payments = Payment.objects.filter(user=user, status='completed').count()

            # Profile completion percentage
            profile_fields = [
                user.first_name, user.last_name, user.phone_number,
                user.address, user.bio, user.headline, user.expertise,
                user.website, user.profile_image
            ]
            filled_fields = sum(1 for field in profile_fields if field)
            profile_completion = int((filled_fields / len(profile_fields)) * 100)

            return Response({
                'enrollment_stats': {
                    'total_enrollments': total_enrollments,
                    'completed_courses': completed_courses,
                    'completion_rate': round((completed_courses / total_enrollments * 100) if total_enrollments > 0 else 0, 1)
                },
                'instructor_stats': {
                    'created_courses': created_courses,
                    'total_students': total_students
                },
                'payment_stats': {
                    'total_payments': total_payments
                },
                'profile_completion': {
                    'percentage': profile_completion,
                    'filled_fields': filled_fields,
                    'total_fields': len(profile_fields)
                }
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
