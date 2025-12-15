from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    ProfileImageUpdateView,
    UserPublicProfileView,
    ChangePasswordView,
    ProfileStatisticsView
)

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Profile URLs
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/image/', ProfileImageUpdateView.as_view(), name='profile-image-update'),
    path('profile/<int:user_id>/', UserPublicProfileView.as_view(), name='user-public-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/statistics/', ProfileStatisticsView.as_view(), name='profile-statistics'),
]