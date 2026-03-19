


from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import models
from django.utils import timezone
from .models import SliderImage, AppVersion
from .serializers import SliderImageSerializer, AppVersionSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health endpoint for load balancer / deploy script. No auth required."""
    return Response({
        'status': 'ok', 
        'service': 'elearning_backend',
        'server_time': timezone.now() # Server time zaroori hota hai debugging ke liye
    })

class SliderImageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SliderImageSerializer
    permission_classes = [AllowAny] # Home screen data public hona chahiye (sirf GET ke liye)

    def get_queryset(self):
        """Optimization: select_related use kiya hai taaki course/category fast load ho"""
        now = timezone.now()
        return SliderImage.objects.select_related('course', 'category').filter(
            is_active=True,
            show_from__lte=now
        ).filter(
            models.Q(show_until__isnull=True) | models.Q(show_until__gte=now)
        )

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Homepage ke liye sirf 5 featured sliders"""
        queryset = self.get_queryset()[:5] 
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

class AppVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AppVersion.objects.all()
    serializer_class = AppVersionSerializer
    # Latest version check public honi chahiye taaki bina login ke app update prompt de sake
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = AppVersion.objects.all()
        platform = self.request.query_params.get('platform', None)
        if platform:
            queryset = queryset.filter(platform=platform)
        return queryset

    @action(detail=False, methods=['get'], url_path=r'latest/(?P<platform>[^/.]+)')
    def get_latest_version(self, request, platform=None):
        """Flutter app startup par ise call karegi"""
        version = AppVersion.objects.filter(platform=platform.lower()).first()
        if version:
            serializer = self.get_serializer(version)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        return Response(
            {'status': 'error', 'message': f'No version found for {platform}'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_force_update(self, request, pk=None):
        """Staff only: Force update activate karne ke liye"""
        if not request.user.is_staff:
            return Response(
                {'status': 'error', 'message': 'Only staff can perform this action'},
                status=status.HTTP_403_FORBIDDEN
            )

        version = self.get_object()
        version.force_update = True
        version.save()
        return Response({'status': 'success', 'message': 'Force update enabled'})