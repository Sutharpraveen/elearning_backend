from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    ProfileImageUpdateView
)

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # Profile URLs
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/image/', ProfileImageUpdateView.as_view(), name='profile-image-update'),
] 