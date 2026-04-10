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
from django.conf import settings
from PIL import Image, ImageDraw
import io
import logging
import os

logger = logging.getLogger(__name__)


def optimize_and_resize_image(image_file, max_size=(500, 500), quality=85):
    """Optimize and resize uploaded image to standard square dimensions."""
    try:
        image = Image.open(image_file)

        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        square_size = max(image.size)
        square_image = Image.new('RGB', (square_size, square_size), (255, 255, 255))

        x = (square_size - image.size[0]) // 2
        y = (square_size - image.size[1]) // 2
        square_image.paste(image, (x, y))

        buffer = io.BytesIO()
        square_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)

        return buffer
    except Exception as e:
        logger.warning("Error optimizing image: %s", e)
        return None


def create_circular_mask(image_file, size=(200, 200)):
    """Create a circular mask version of the uploaded image."""
    try:
        image = Image.open(image_file)

        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        image.thumbnail(size, Image.Resampling.LANCZOS)

        square_size = max(image.size)
        square_image = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))

        x = (square_size - image.size[0]) // 2
        y = (square_size - image.size[1]) // 2
        square_image.paste(image, (x, y))

        mask = Image.new('L', (square_size, square_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, square_size, square_size), fill=255)

        circular_image = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
        circular_image.paste(square_image, mask=mask)

        buffer = io.BytesIO()
        circular_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        return buffer
    except Exception as e:
        logger.warning("Error creating circular mask: %s", e)
        return None


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
                try:
                    # Bulk blacklist all old tokens in 2 queries instead of N get_or_creates
                    user_tokens = list(OutstandingToken.objects.filter(user=user))
                    if user_tokens:
                        already_blacklisted = set(
                            BlacklistedToken.objects.filter(token__in=user_tokens).values_list('token_id', flat=True)
                        )
                        new_blacklists = [
                            BlacklistedToken(token=t) for t in user_tokens if t.id not in already_blacklisted
                        ]
                        if new_blacklists:
                            BlacklistedToken.objects.bulk_create(new_blacklists, ignore_conflicts=True)
                except Exception as e:
                    logger.warning("Error blacklisting old tokens: %s", e)

                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

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
                    'user': UserProfileSerializer(user, context={'request': request}).data
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

            if image.size > 10 * 1024 * 1024:
                return Response(
                    {'error': 'Image size should not exceed 10MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                return Response(
                    {'error': 'Only JPG, PNG and GIF files are allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = request.user

            if user.profile_image:
                try:
                    if os.path.exists(user.profile_image.path):
                        os.remove(user.profile_image.path)

                    circular_path = user.profile_image.path.replace('.jpg', '_circ_mask.png').replace('.jpeg', '_circ_mask.png').replace('.png', '_circ_mask.png').replace('.gif', '_circ_mask.png')
                    if os.path.exists(circular_path):
                        os.remove(circular_path)
                except Exception as e:
                    logger.warning("Error deleting old images: %s", e)

            user_dir = os.path.join('user_profiles', str(user.id))
            os.makedirs(os.path.join(settings.MEDIA_ROOT, user_dir), exist_ok=True)

            image.seek(0)
            optimized_buffer = optimize_and_resize_image(image, max_size=(800, 800), quality=90)
            original_file_path = None
            if optimized_buffer:
                original_file_name = f"profile_{user.id}_original.jpg"
                original_file_path = f'{user_dir}/{original_file_name}'
                original_full_path = os.path.join(settings.MEDIA_ROOT, original_file_path)

                with open(original_full_path, 'wb+') as destination:
                    destination.write(optimized_buffer.getvalue())

            image.seek(0)
            circular_mask_buffer = create_circular_mask(image, size=(300, 300))
            if circular_mask_buffer:
                circular_file_name = f"profile_{user.id}_circ_mask.png"
                circular_file_path = f'{user_dir}/{circular_file_name}'
                circular_full_path = os.path.join(settings.MEDIA_ROOT, circular_file_path)

                with open(circular_full_path, 'wb+') as circular_destination:
                    circular_destination.write(circular_mask_buffer.getvalue())

                user.profile_image = circular_file_path
                user.save()

                return Response({
                    'message': 'Profile image updated successfully',
                    'profile_image': request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
                    'original_image': request.build_absolute_uri(settings.MEDIA_URL + original_file_path) if original_file_path else None,
                    'optimized_size': {
                        'original': f"{len(optimized_buffer.getvalue()) if optimized_buffer else 0} bytes",
                        'circular': f"{len(circular_mask_buffer.getvalue())} bytes"
                    }
                })

            return Response(
                {'error': 'Failed to process image'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

            if not user.check_password(old_password):
                return Response(
                    {'error': 'Current password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if len(new_password) < 8:
                return Response(
                    {'error': 'Password must be at least 8 characters long'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
            from django.db.models import Count, Q

            # Single query for enrollment stats
            enrollment_stats = Enrollment.objects.filter(user=user).aggregate(
                total_enrollments=Count('id'),
                completed_courses=Count('id', filter=Q(completed=True))
            )
            total_enrollments = enrollment_stats['total_enrollments'] or 0
            completed_courses = enrollment_stats['completed_courses'] or 0

            created_courses = 0
            total_students = 0
            if user.role == 'instructor':
                # Single query for instructor stats
                inst_stats = Course.objects.filter(instructor=user).aggregate(
                    created_courses=Count('id'),
                    total_students=Count('enrollments', distinct=True)
                )
                created_courses = inst_stats['created_courses'] or 0
                total_students = inst_stats['total_students'] or 0

            total_payments = Payment.objects.filter(user=user, status='completed').count()

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
