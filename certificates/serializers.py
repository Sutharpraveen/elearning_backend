from rest_framework import serializers
from .models import Certificate, CertificateTemplate
from users.models import CustomUser
from courses.models import Course


class CertificateTemplateSerializer(serializers.ModelSerializer):
    """Serializer for CertificateTemplate model"""

    class Meta:
        model = CertificateTemplate
        fields = [
            'id', 'name', 'title', 'subtitle',
            'header_text', 'body_text', 'footer_text',
            'background_image', 'primary_color', 'secondary_color',
            'font_family', 'font_size_title', 'font_size_body',
            'organization_name', 'organization_logo',
            'signature_1_title', 'signature_1_name', 'signature_1_image',
            'signature_2_title', 'signature_2_name', 'signature_2_image',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CertificateListSerializer(serializers.ModelSerializer):
    """Serializer for listing certificates"""

    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.EmailField(source='student.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_instructor = serializers.CharField(source='course.instructor.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'certificate_number',
            'student_name', 'student_email',
            'course_title', 'course_instructor',
            'certificate_type', 'title', 'completion_percentage',
            'grade', 'score', 'status', 'issued_at',
            'expires_at', 'template_name', 'verification_url'
        ]
        read_only_fields = ['id', 'certificate_id', 'certificate_number', 'verification_url']


class CertificateDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed certificate view"""

    student = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    template = CertificateTemplateSerializer(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'certificate_number',
            'student', 'course', 'certificate_type', 'title',
            'completion_percentage', 'grade', 'score',
            'template', 'certificate_file', 'certificate_url',
            'status', 'issued_at', 'expires_at',
            'additional_notes', 'verification_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'certificate_id', 'certificate_number',
            'certificate_file', 'certificate_url', 'verification_url',
            'created_at', 'updated_at'
        ]

    def get_student(self, obj):
        """Get student details"""
        return {
            'id': obj.student.id,
            'name': obj.student.get_full_name(),
            'email': obj.student.email,
            'username': obj.student.username
        }

    def get_course(self, obj):
        """Get course details"""
        return {
            'id': obj.course.id,
            'title': obj.course.title,
            'slug': obj.course.slug,
            'instructor': obj.course.instructor.get_full_name(),
            'level': obj.course.level,
            'language': obj.course.language
        }


class CertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating certificates"""

    class Meta:
        model = Certificate
        fields = [
            'student', 'course', 'certificate_type', 'title',
            'completion_percentage', 'grade', 'score',
            'template', 'additional_notes'
        ]

    def validate(self, data):
        """Validate certificate creation"""
        student = data.get('student')
        course = data.get('course')

        # Check if certificate already exists for this student-course combination
        if Certificate.objects.filter(student=student, course=course).exists():
            raise serializers.ValidationError(
                "A certificate already exists for this student and course."
            )

        # Validate completion percentage
        if data.get('completion_percentage', 0) < 100 and data.get('certificate_type') == 'completion':
            raise serializers.ValidationError(
                "Course completion certificates require 100% completion."
            )

        return data


class CertificateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating certificates"""

    class Meta:
        model = Certificate
        fields = [
            'status', 'grade', 'score', 'additional_notes',
            'expires_at', 'template'
        ]

    def validate_status(self, value):
        """Validate status transitions"""
        current_status = self.instance.status

        # Valid transitions
        valid_transitions = {
            'pending': ['issued', 'revoked'],
            'issued': ['revoked'],
            'revoked': []  # Cannot change from revoked
        }

        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}."
            )

        return value


class CertificateVerificationSerializer(serializers.Serializer):
    """Serializer for certificate verification"""

    certificate_id = serializers.UUIDField()
    certificate_number = serializers.CharField(required=False)

    def validate(self, data):
        """Validate verification request"""
        certificate_id = data.get('certificate_id')
        certificate_number = data.get('certificate_number')

        if not certificate_id and not certificate_number:
            raise serializers.ValidationError(
                "Either certificate_id or certificate_number is required."
            )

        return data


class CertificateStatsSerializer(serializers.Serializer):
    """Serializer for certificate statistics"""

    total_certificates = serializers.IntegerField()
    issued_certificates = serializers.IntegerField()
    pending_certificates = serializers.IntegerField()
    revoked_certificates = serializers.IntegerField()
    certificates_this_month = serializers.IntegerField()
    most_popular_course = serializers.DictField()
    average_completion_score = serializers.DecimalField(max_digits=5, decimal_places=2)







