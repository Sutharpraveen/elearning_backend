from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import SliderImage, AppVersion
from .serializers import SliderImageSerializer, AppVersionSerializer
from django.utils import timezone
from django.db import models
import logging

logger = logging.getLogger(__name__)

class SliderImageViewSet(viewsets.ModelViewSet):
    queryset = SliderImage.objects.all()
    serializer_class = SliderImageSerializer

    def get_queryset(self):
        # Remove date filtering to show all sliders
        return SliderImage.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            return Response({
                "status": "success",
                "message": "Slider images retrieved successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response({
                    "status": "success",
                    "message": "Slider created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AppVersionViewSet(viewsets.ModelViewSet):
    queryset = AppVersion.objects.all()
    serializer_class = AppVersionSerializer

    def list(self, request, *args, **kwargs):
        platform = request.query_params.get('platform', None)
        if platform:
            queryset = self.queryset.filter(platform=platform).order_by('-created_at').first()
            if queryset:
                serializer = self.get_serializer(queryset)
                return Response({
                    "status": "success",
                    "message": f"Latest {platform} version retrieved successfully",
                    "data": serializer.data
                })
            return Response({
                "status": "error",
                "message": f"No version found for {platform}",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        
        queryset = self.queryset.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "App versions retrieved successfully",
            "data": serializer.data
        })