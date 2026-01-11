from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db import models
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Certificate, CertificateTemplate
from .certificate_generator import CertificateGenerator
from .serializers import (
    CertificateTemplateSerializer,
    CertificateListSerializer,
    CertificateDetailSerializer,
    CertificateCreateSerializer,
    CertificateUpdateSerializer,
    CertificateVerificationSerializer,
    CertificateStatsSerializer
)
from courses.models import Enrollment


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing certificate templates"""

    queryset = CertificateTemplate.objects.all()
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  # Only admins can manage templates

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'title', 'organization_name']
    ordering_fields = ['name', 'created_at', 'updated_at']

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a certificate template"""
        template = self.get_object()

        # Create duplicate
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.save()

        serializer = self.get_serializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CertificateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing certificates"""

    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'certificate_number', 'student__first_name', 'student__last_name',
        'student__email', 'course__title', 'title'
    ]
    ordering_fields = ['issued_at', 'created_at', 'certificate_number', 'completion_percentage']

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        if user.is_staff or user.role == 'instructor':
            # Admins and instructors can see all certificates
            return Certificate.objects.select_related('student', 'course', 'template')
        else:
            # Students can only see their own certificates
            return Certificate.objects.filter(student=user).select_related('student', 'course', 'template')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CertificateListSerializer
        elif self.action in ['create']:
            return CertificateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CertificateUpdateSerializer
        else:
            return CertificateDetailSerializer

    def perform_create(self, serializer):
        """Set default values when creating certificate"""
        certificate = serializer.save()

        # If completion is 100% and no grade set, set a default grade
        if certificate.completion_percentage >= 100 and not certificate.grade:
            certificate.grade = self.calculate_grade(certificate.score or 100)
            certificate.save()

    def calculate_grade(self, score):
        """Calculate grade based on score"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        else:
            return 'F'

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """Issue a certificate"""
        certificate = self.get_object()

        if certificate.status != 'pending':
            return Response(
                {'error': f'Certificate is already {certificate.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certificate.issue_certificate()
        serializer = self.get_serializer(certificate)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a certificate"""
        certificate = self.get_object()

        if certificate.status == 'revoked':
            return Response(
                {'error': 'Certificate is already revoked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certificate.revoke_certificate()
        serializer = self.get_serializer(certificate)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate file"""
        certificate = self.get_object()

        if not certificate.certificate_file:
            return Response(
                {'error': 'Certificate file not available'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return file download response
        from django.http import FileResponse
        return FileResponse(
            certificate.certificate_file.open(),
            as_attachment=True,
            filename=f"certificate_{certificate.certificate_number}.pdf"
        )

    @action(detail=False, methods=['get'])
    def my_certificates(self, request):
        """Get current user's certificates"""
        certificates = self.get_queryset().filter(student=request.user)
        serializer = self.get_serializer(certificates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get certificate statistics"""
        # Only admins can view stats
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Calculate stats
        total_certificates = Certificate.objects.count()
        issued_certificates = Certificate.objects.filter(status='issued').count()
        pending_certificates = Certificate.objects.filter(status='pending').count()
        revoked_certificates = Certificate.objects.filter(status='revoked').count()

        # Certificates issued this month
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        certificates_this_month = Certificate.objects.filter(
            issued_at__gte=month_start
        ).count()

        # Most popular course for certificates
        most_popular = Certificate.objects.values('course__title').annotate(
            count=Count('course')
        ).order_by('-count').first()

        # Average completion score
        avg_score = Certificate.objects.filter(
            score__isnull=False
        ).aggregate(avg_score=Avg('score'))['avg_score'] or 0

        stats_data = {
            'total_certificates': total_certificates,
            'issued_certificates': issued_certificates,
            'pending_certificates': pending_certificates,
            'revoked_certificates': revoked_certificates,
            'certificates_this_month': certificates_this_month,
            'most_popular_course': most_popular or {'title': 'N/A', 'count': 0},
            'average_completion_score': round(avg_score, 2)
        }

        serializer = CertificateStatsSerializer(stats_data)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([])
def verify_certificate(request):
    """Verify certificate authenticity"""
    serializer = CertificateVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    certificate_id = serializer.validated_data.get('certificate_id')
    certificate_number = serializer.validated_data.get('certificate_number')

    try:
        if certificate_id:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
        else:
            certificate = Certificate.objects.get(certificate_number=certificate_number)
    except Certificate.DoesNotExist:
        return Response(
            {'error': 'Certificate not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if certificate is valid
    if certificate.status != 'issued':
        return Response({
            'valid': False,
            'status': certificate.status,
            'message': f'Certificate is {certificate.status}'
        })

    if certificate.is_expired:
        return Response({
            'valid': False,
            'status': 'expired',
            'message': 'Certificate has expired'
        })

    # Return certificate details
    detail_serializer = CertificateDetailSerializer(certificate)
    return Response({
        'valid': True,
        'certificate': detail_serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_generate_certificates(request):
    """Automatically generate certificates for completed courses"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Find enrollments with 100% completion but no certificates
    completed_enrollments = Enrollment.objects.filter(
        completed=True
    ).exclude(
        user__certificates__course=F('course')
    ).select_related('user', 'course')

    # Get default template
    try:
        template = CertificateTemplate.objects.first()
        if not template:
            return Response(
                {'error': 'No certificate template available'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': f'Template error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    certificates_created = []

    for enrollment in completed_enrollments:
        try:
            # Create certificate using the generator
            certificate = CertificateGenerator.generate_certificate_for_student(
                enrollment.user,
                enrollment.course,
                template
            )

            certificates_created.append({
                'certificate_id': str(certificate.certificate_id),
                'certificate_number': certificate.certificate_number,
                'student': enrollment.user.get_full_name(),
                'course': enrollment.course.title
            })
        except Exception as e:
            print(f"Failed to generate certificate for {enrollment.user}: {e}")
            continue

    return Response({
        'message': f'Created {len(certificates_created)} certificates',
        'certificates': certificates_created
    })


def certificate_verification_page(request, certificate_id):
    """Public certificate verification page"""
    try:
        certificate = Certificate.objects.select_related('student', 'course').get(
            certificate_id=certificate_id
        )
    except Certificate.DoesNotExist:
        return render(request, 'certificates/verification_error.html', {
            'error': 'Certificate not found',
            'certificate_id': certificate_id
        })

    # Check certificate status
    if certificate.status != 'issued':
        return render(request, 'certificates/verification_error.html', {
            'error': f'Certificate is {certificate.status}',
            'certificate': certificate
        })

    if certificate.is_expired:
        return render(request, 'certificates/verification_error.html', {
            'error': 'Certificate has expired',
            'certificate': certificate
        })

    # Certificate is valid
    return render(request, 'certificates/verification_success.html', {
        'certificate': certificate,
        'student_name': certificate.student.get_full_name(),
        'course_title': certificate.course.title,
        'issued_date': certificate.issued_at.strftime('%B %d, %Y') if certificate.issued_at else None,
    })
