from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WishlistViewSet, CartViewSet
from .views import check_course_status

router = DefaultRouter()
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('course-status/<int:course_id>/', check_course_status, name='check_course_status'),
]
