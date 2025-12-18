import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from .models import Certificate, CertificateTemplate


class CertificateGenerator:
    """Generate certificates in HTML/PDF format"""

    def __init__(self, certificate):
        self.certificate = certificate
        self.template = certificate.template

    def generate_html_certificate(self):
        """Generate HTML certificate content"""
        template = self.template
        certificate = self.certificate

        # Prepare context data
        context = {
            'certificate': certificate,
            'template': template,
            'student_name': certificate.student.get_full_name(),
            'course_title': certificate.course.title,
            'completion_date': certificate.issued_at.strftime('%B %d, %Y') if certificate.issued_at else '',
            'certificate_number': certificate.certificate_number,
            'grade': certificate.grade or 'N/A',
            'completion_percentage': certificate.completion_percentage,
        }

        # Add template styling
        if template:
            context.update({
                'primary_color': template.primary_color,
                'secondary_color': template.secondary_color,
                'font_family': template.font_family,
                'font_size_title': template.font_size_title,
                'font_size_body': template.font_size_body,
                'organization_name': template.organization_name,
                'signature_1_name': template.signature_1_name,
                'signature_1_title': template.signature_1_title,
                'signature_2_name': template.signature_2_name,
                'signature_2_title': template.signature_2_title,
            })

        # Render HTML template
        html_content = render_to_string('certificates/certificate_template.html', context)

        return html_content

    def save_certificate_file(self, file_format='html'):
        """Save certificate as file"""
        if file_format == 'html':
            content = self.generate_html_certificate()
            file_name = f"certificate_{self.certificate.certificate_number}.html"
            mime_type = 'text/html'
        else:
            # For now, just save as HTML (PDF would require additional libraries)
            content = self.generate_html_certificate()
            file_name = f"certificate_{self.certificate.certificate_number}.html"
            mime_type = 'text/html'

        # Save file
        file_path = f"certificates/{file_name}"
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Update certificate model
        self.certificate.certificate_file.name = file_path
        self.certificate.save(update_fields=['certificate_file'])

        return file_path

    @staticmethod
    def generate_certificate_for_student(student, course, template=None, **kwargs):
        """Generate certificate for a student-course completion"""
        from courses.models import Enrollment

        # Check if enrollment exists and is complete
        try:
            enrollment = Enrollment.objects.get(user=student, course=course)
            if not enrollment.completed:
                raise ValueError("Course not completed")
        except Enrollment.DoesNotExist:
            raise ValueError("Student not enrolled in course")

        # Create certificate
        cert_kwargs = {
            'student': student,
            'course': course,
            'certificate_type': 'completion',
            'title': f"Certificate of Completion - {course.title}",
            'completion_percentage': 100.00,
            'score': kwargs.get('score', 100.00),
            'template': template,
            'status': 'issued',
        }

        # Add any additional kwargs (like grade)
        for key, value in kwargs.items():
            if key not in cert_kwargs:
                cert_kwargs[key] = value

        certificate = Certificate.objects.create(**cert_kwargs)

        # Generate certificate file
        generator = CertificateGenerator(certificate)
        generator.save_certificate_file()

        return certificate

    @staticmethod
    def bulk_generate_certificates(course=None, template=None):
        """Generate certificates for all completed enrollments"""
        from courses.models import Enrollment

        # Get completed enrollments
        enrollments = Enrollment.objects.filter(completed=True)

        if course:
            enrollments = enrollments.filter(course=course)

        # Exclude students who already have certificates
        enrollments = enrollments.exclude(
            user__certificates__course__in=enrollments.values('course')
        ).distinct()

        certificates = []
        for enrollment in enrollments:
            try:
                certificate = CertificateGenerator.generate_certificate_for_student(
                    enrollment.student,
                    enrollment.course,
                    template
                )
                certificates.append(certificate)
            except Exception as e:
                print(f"Failed to generate certificate for {enrollment.student}: {e}")
                continue

        return certificates


def generate_sample_certificate_template():
    """Create a default certificate template"""
    template, created = CertificateTemplate.objects.get_or_create(
        name="Default Certificate Template",
        defaults={
            'title': "Certificate of Completion",
            'subtitle': "This certifies that",
            'header_text': "has successfully completed the course",
            'body_text': "with outstanding performance and dedication.",
            'footer_text': "Presented on {date}",
            'primary_color': '#2C3E50',
            'secondary_color': '#3498DB',
            'font_family': 'Arial, sans-serif',
            'font_size_title': 48,
            'font_size_body': 24,
            'organization_name': 'E-Learning Platform',
            'signature_1_title': 'Director',
            'signature_1_name': 'Dr. John Smith',
            'signature_2_title': 'Instructor',
            'signature_2_name': 'Jane Doe',
            'is_active': True
        }
    )

    return template
