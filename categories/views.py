from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Category
from .serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CourseInCategorySerializer
)


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrAuthenticatedReadOnly]
    authentication_classes = [JWTAuthentication]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Category.objects.annotate(
            annotated_total_courses=Count('courses', distinct=True)
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategoryDetailSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CategoryDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'data': serializer.data
        })

