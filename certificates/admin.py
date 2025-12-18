from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Certificate, CertificateTemplate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    """Admin interface for CertificateTemplate"""

    list_display = ['name', 'title', 'organization_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'title', 'organization_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'subtitle', 'is_active')
        }),
        ('Content', {
            'fields': ('header_text', 'body_text', 'footer_text'),
            'classes': ('collapse',)
        }),
        ('Styling', {
            'fields': ('background_image', 'primary_color', 'secondary_color',
                      'font_family', 'font_size_title', 'font_size_body'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('organization_name', 'organization_logo')
        }),
        ('Signatures', {
            'fields': ('signature_1_title', 'signature_1_name', 'signature_1_image',
                      'signature_2_title', 'signature_2_name', 'signature_2_image'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface for Certificate"""

    list_display = [
        'certificate_number', 'student_name', 'course_title',
        'certificate_type', 'status', 'issued_at', 'verification_link'
    ]
    list_filter = ['status', 'certificate_type', 'issued_at', 'created_at']
    search_fields = [
        'certificate_number', 'student__email', 'student__first_name',
        'student__last_name', 'course__title'
    ]
    readonly_fields = [
        'certificate_id', 'certificate_number', 'verification_url',
        'created_at', 'updated_at'
    ]
    ordering = ['-issued_at', '-created_at']

    fieldsets = (
        ('Certificate Information', {
            'fields': ('certificate_id', 'certificate_number', 'certificate_type', 'title')
        }),
        ('Recipients & Course', {
            'fields': ('student', 'course')
        }),
        ('Completion Details', {
            'fields': ('completion_percentage', 'grade', 'score')
        }),
        ('Template & Generation', {
            'fields': ('template', 'certificate_file', 'certificate_url')
        }),
        ('Status & Dates', {
            'fields': ('status', 'issued_at', 'expires_at')
        }),
        ('Additional Information', {
            'fields': ('additional_notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def student_name(self, obj):
        """Display student full name"""
        return obj.student.get_full_name()
    student_name.short_description = 'Student'

    def course_title(self, obj):
        """Display course title"""
        return obj.course.title
    course_title.short_description = 'Course'

    def verification_link(self, obj):
        """Display verification link"""
        if obj.certificate_id:
            url = reverse('admin:certificates_certificate_change', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank">Verify</a>',
                obj.verification_url
            )
        return '-'
    verification_link.short_description = 'Verification'

    actions = ['issue_certificates', 'revoke_certificates']

    def issue_certificates(self, request, queryset):
        """Bulk issue certificates"""
        updated = 0
        for certificate in queryset.filter(status='pending'):
            certificate.issue_certificate()
            updated += 1
        self.message_user(
            request,
            f'Successfully issued {updated} certificate(s).'
        )
    issue_certificates.short_description = 'Issue selected certificates'

    def revoke_certificates(self, request, queryset):
        """Bulk revoke certificates"""
        updated = 0
        for certificate in queryset.filter(status__in=['pending', 'issued']):
            certificate.revoke_certificate()
            updated += 1
        self.message_user(
            request,
            f'Successfully revoked {updated} certificate(s).'
        )
    revoke_certificates.short_description = 'Revoke selected certificates'
