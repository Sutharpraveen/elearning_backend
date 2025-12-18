from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import os


class CertificateTemplate(models.Model):
    """Template for generating certificates"""
    name = models.CharField(max_length=200, help_text="Template name")
    title = models.CharField(max_length=300, help_text="Certificate title")
    subtitle = models.CharField(max_length=300, blank=True, help_text="Certificate subtitle")

    # Content
    header_text = models.TextField(blank=True, help_text="Header text above recipient name")
    body_text = models.TextField(blank=True, help_text="Main body text")
    footer_text = models.TextField(blank=True, help_text="Footer text")

    # Styling
    background_image = models.ImageField(
        upload_to='certificate_templates/',
        blank=True,
        null=True,
        help_text="Background image for certificate"
    )
    primary_color = models.CharField(
        max_length=7,
        default='#2C3E50',
        help_text="Primary color (hex code)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#3498DB',
        help_text="Secondary color (hex code)"
    )

    # Layout
    font_family = models.CharField(
        max_length=100,
        default='Arial, sans-serif',
        help_text="Font family"
    )
    font_size_title = models.IntegerField(
        default=48,
        validators=[MinValueValidator(12), MaxValueValidator(72)],
        help_text="Title font size (px)"
    )
    font_size_body = models.IntegerField(
        default=24,
        validators=[MinValueValidator(8), MaxValueValidator(48)],
        help_text="Body font size (px)"
    )

    # Organization details
    organization_name = models.CharField(
        max_length=200,
        default='E-Learning Platform',
        help_text="Organization/Platform name"
    )
    organization_logo = models.ImageField(
        upload_to='certificate_logos/',
        blank=True,
        null=True,
        help_text="Organization logo"
    )

    # Signature fields
    signature_1_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="First signature title (e.g., 'Director')"
    )
    signature_1_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="First signature name"
    )
    signature_1_image = models.ImageField(
        upload_to='certificate_signatures/',
        blank=True,
        null=True,
        help_text="First signature image"
    )

    signature_2_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Second signature title"
    )
    signature_2_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Second signature name"
    )
    signature_2_image = models.ImageField(
        upload_to='certificate_signatures/',
        blank=True,
        null=True,
        help_text="Second signature image"
    )

    is_active = models.BooleanField(default=True, help_text="Is this template active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificate Template"
        verbose_name_plural = "Certificate Templates"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Certificate(models.Model):
    """Certificate issued to students upon course completion"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked'),
    ]

    CERTIFICATE_TYPES = [
        ('completion', 'Course Completion'),
        ('achievement', 'Achievement'),
        ('participation', 'Participation'),
    ]

    # Core fields
    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique certificate identifier"
    )
    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Human-readable certificate number"
    )

    # Relationships
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        help_text="Student who earned the certificate"
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='certificates',
        help_text="Course for which certificate was issued"
    )

    # Certificate details
    certificate_type = models.CharField(
        max_length=20,
        choices=CERTIFICATE_TYPES,
        default='completion',
        help_text="Type of certificate"
    )
    title = models.CharField(
        max_length=300,
        help_text="Certificate title"
    )

    # Completion details
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Course completion percentage"
    )
    grade = models.CharField(
        max_length=10,
        blank=True,
        help_text="Grade earned (A+, A, B+, etc.)"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final score/percentage"
    )

    # Certificate generation
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        help_text="Certificate template used"
    )

    # Certificate file
    certificate_file = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True,
        help_text="Generated certificate file (PDF/HTML)"
    )
    certificate_url = models.URLField(
        blank=True,
        help_text="Public URL for certificate verification"
    )

    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Certificate status"
    )
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when certificate was issued"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Certificate expiration date (optional)"
    )

    # Additional information
    additional_notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ['-issued_at', '-created_at']
        unique_together = ['student', 'course']  # One certificate per student per course

    def __str__(self):
        return f"Certificate for {self.student.get_full_name()} - {self.course.title}"

    def save(self, *args, **kwargs):
        # Generate certificate number if not set
        if not self.certificate_number:
            self.certificate_number = self.generate_certificate_number()

        # Set issued date when status changes to issued
        if self.status == 'issued' and not self.issued_at:
            self.issued_at = timezone.now()

        super().save(*args, **kwargs)

    def generate_certificate_number(self):
        """Generate a unique certificate number"""
        import random
        import string

        # Format: CERT-YYYY-XXXXXX (e.g., CERT-2024-ABC123)
        year = timezone.now().year
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"CERT-{year}-{random_string}"

    @property
    def is_expired(self):
        """Check if certificate is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def verification_url(self):
        """Get verification URL for this certificate"""
        if not self.certificate_url:
            # Generate verification URL
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            self.certificate_url = f"{base_url}/api/certificates/verify/{self.certificate_id}/"
            self.save(update_fields=['certificate_url'])
        return self.certificate_url

    def issue_certificate(self):
        """Mark certificate as issued"""
        self.status = 'issued'
        self.issued_at = timezone.now()
        self.save()

    def revoke_certificate(self):
        """Revoke certificate"""
        self.status = 'revoked'
        self.save()
