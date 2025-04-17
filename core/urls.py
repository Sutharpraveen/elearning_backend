from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SliderImageViewSet, AppVersionViewSet

router = DefaultRouter()
router.register(r'sliders', SliderImageViewSet)
router.register(r'app-versions', AppVersionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]