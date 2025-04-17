from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WishlistViewSet, CartViewSet

router = DefaultRouter()
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
