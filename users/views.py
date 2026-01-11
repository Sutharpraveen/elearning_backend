from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, LoginSerializer, UserProfileSerializer, UserProfileUpdateSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import CustomUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
from PIL import Image, ImageDraw
import io
import logging
from rest_framework import viewsets
from rest_framework.decorators import action
import os

logger = logging.getLogger(__name__)

def optimize_and_resize_image(image_file, max_size=(500, 500), quality=85):
    """
    Optimize and resize uploaded image to standard dimensions
    """
    try:
        # Open the image
        image = Image.open(image_file)

        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Resize image while maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Create a square canvas with white background
        square_size = max(image.size)
        square_image = Image.new('RGB', (square_size, square_size), (255, 255, 255))

        # Center the image on the square canvas
        x = (square_size - image.size[0]) // 2
        y = (square_size - image.size[1]) // 2
        square_image.paste(image, (x, y))

        # Save optimized image to buffer
        buffer = io.BytesIO()
        square_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)

        return buffer
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return None

def create_circular_mask(image_file, size=(200, 200)):
    """
    Create a circular mask version of the uploaded image
    """
    try:
        # Open the image
        image = Image.open(image_file)

        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Resize to standard size first
        image.thumbnail(size, Image.Resampling.LANCZOS)

        # Create square canvas
        square_size = max(image.size)
        square_image = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))

        # Center the image
        x = (square_size - image.size[0]) // 2
        y = (square_size - image.size[1]) // 2
        square_image.paste(image, (x, y))

        # Create circular mask
        mask = Image.new('L', (square_size, square_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, square_size, square_size), fill=255)

        # Apply circular mask
        circular_image = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
        circular_image.paste(square_image, mask=mask)

        # Save to BytesIO buffer
        buffer = io.BytesIO()
        circular_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        return buffer
    except Exception as e:
        print(f"Error creating circular mask: {e}")
        return None

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
                # BLACKLIST ALL EXISTING TOKENS - SINGLE DEVICE LOGIN
                # This ensures only one active session per user
                try:
                    # Blacklist all outstanding refresh tokens for this user
                    user_tokens = OutstandingToken.objects.filter(user=user)
                    for token in user_tokens:
                        try:
                            # Create blacklist entry for each token
                            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
                            BlacklistedToken.objects.get_or_create(token=token)
                        except:
                            pass  # Token might already be blacklisted

                    # Also try to blacklist by token value if needed
                    refresh_tokens = RefreshToken.objects.filter(user=user)
                    for refresh_token in refresh_tokens:
                        try:
                            refresh_token.blacklist()
                        except:
                            pass  # Token might already be blacklisted

                except Exception as e:
                    # Log the error but don't fail the login
                    logger.warning(f"Error blacklisting old tokens for user {user.email}: {str(e)}")

                # Generate new tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                # Store current session token JTI for single device tracking
                user.current_session_token = access_token['jti']
                user.last_login = timezone.now()
                user.save(update_fields=['current_session_token', 'last_login'])

                return Response({
                    'status': 'success',
                    'message': 'Login successful. All other devices have been logged out.',
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(access_token),
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
            
            # Validate file size (10MB max before optimization)
            if image.size > 10 * 1024 * 1024:
                return Response(
                    {'error': 'Image size should not exceed 10MB'},
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

            # Delete old images if they exist
            if user.profile_image:
                try:
                    # Delete original image
                    if os.path.exists(user.profile_image.path):
                        os.remove(user.profile_image.path)

                    # Delete circular mask if it exists
                    circular_path = user.profile_image.path.replace('.jpg', '_circ_mask.png').replace('.jpeg', '_circ_mask.png').replace('.png', '_circ_mask.png').replace('.gif', '_circ_mask.png')
                    if os.path.exists(circular_path):
                        os.remove(circular_path)
                except Exception as e:
                    print(f"Error deleting old images: {e}")

            # Create directory if it doesn't exist
            user_dir = os.path.join('user_profiles', str(user.id))
            os.makedirs(os.path.join(settings.MEDIA_ROOT, user_dir), exist_ok=True)

            # Optimize and resize the original image
            image.seek(0)  # Reset file pointer
            optimized_buffer = optimize_and_resize_image(image, max_size=(800, 800), quality=90)
            if optimized_buffer:
                # Save optimized original image
                original_file_name = f"profile_{user.id}_original.jpg"
                original_file_path = f'{user_dir}/{original_file_name}'
                original_full_path = os.path.join(settings.MEDIA_ROOT, original_file_path)

                with open(original_full_path, 'wb+') as destination:
                    destination.write(optimized_buffer.getvalue())

                print(f"✅ Saved optimized original: {original_file_name} ({len(optimized_buffer.getvalue())} bytes)")

            # Create circular mask version
            image.seek(0)  # Reset file pointer
            circular_mask_buffer = create_circular_mask(image, size=(300, 300))
            if circular_mask_buffer:
                circular_file_name = f"profile_{user.id}_circ_mask.png"
                circular_file_path = f'{user_dir}/{circular_file_name}'
                circular_full_path = os.path.join(settings.MEDIA_ROOT, circular_file_path)

                with open(circular_full_path, 'wb+') as circular_destination:
                    circular_destination.write(circular_mask_buffer.getvalue())

                print(f"✅ Saved circular mask: {circular_file_name} ({len(circular_mask_buffer.getvalue())} bytes)")

                # Save the circular mask path to database (frontend expects this)
                user.profile_image = circular_file_path
                user.save()

                return Response({
                    'message': 'Profile image updated successfully',
                    'profile_image': request.build_absolute_uri(user.profile_image.url),
                    'original_image': request.build_absolute_uri(settings.MEDIA_URL + original_file_path) if optimized_buffer else None,
                    'optimized_size': {
                        'original': f"{len(optimized_buffer.getvalue()) if optimized_buffer else 0} bytes",
                        'circular': f"{len(circular_mask_buffer.getvalue()) if circular_mask_buffer else 0} bytes"
                    }
                })
            else:
                return Response(
                    {'error': 'Failed to process image'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

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
