from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChapterViewSet

router = DefaultRouter()
router.register('chapters', ChapterViewSet, basename='chapter')

urlpatterns = [
    path('', include(router.urls)),
]