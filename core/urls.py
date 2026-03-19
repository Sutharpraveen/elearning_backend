from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SliderImageViewSet, AppVersionViewSet, health_check

router = DefaultRouter()
router.register(r'sliders', SliderImageViewSet, basename='sliderimage')
router.register(r'app-versions', AppVersionViewSet, basename='appversion')

urlpatterns = [
    path('health/', health_check),
    path('', include(router.urls)),
]
