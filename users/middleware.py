from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.http import JsonResponse
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

class SingleDeviceLoginMiddleware(MiddlewareMixin):
    """
    Middleware to enforce single device login by validating JWT token JTI
    against user's current_session_token
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that don't require authentication
        self.exempt_urls = [
            '/api/users/login/',
            '/api/users/register/',
            '/api/courses/search/',
            '/admin/',
        ]

    def __call__(self, request):
        # Skip authentication check for exempt URLs
        if any(request.path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)

        # Check for Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return self.get_response(request)

        try:
            # Extract token
            token_str = auth_header.split(' ')[1]
            token = AccessToken(token_str)

            # Get user from token
            user_id = token.payload.get('user_id')
            if not user_id:
                return JsonResponse({
                    'error': 'Invalid token: no user_id'
                }, status=401)

            # Import here to avoid circular imports
            from .models import CustomUser
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'error': 'User not found'
                }, status=401)

            # Check if token JTI matches user's current session
            token_jti = token.payload.get('jti')
            if user.current_session_token != token_jti:
                logger.warning(f"Single device login violation for user {user.email}: Token JTI {token_jti} != Current session {user.current_session_token}")
                return JsonResponse({
                    'error': 'Session expired. Please login again.',
                    'detail': 'You have been logged in from another device.'
                }, status=401)

        except (InvalidToken, TokenError, IndexError, ValueError) as e:
            return JsonResponse({
                'error': 'Invalid token',
                'detail': str(e)
            }, status=401)
        except Exception as e:
            logger.error(f"Unexpected error in SingleDeviceLoginMiddleware: {str(e)}")
            return JsonResponse({
                'error': 'Authentication error'
            }, status=500)

        return self.get_response(request)



