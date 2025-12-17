from django.contrib import admin
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from django import forms

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'level', 'original_price', 'is_published', 'created_at']
    list_filter = ['is_published', 'level', 'category', 'language', 'created_at']
    search_fields = ['title', 'description', 'instructor__email']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('instructor', 'category', 'title', 'slug', 'description')
        }),
        ('Course Details', {
            'fields': ('learning_objectives', 'requirements', 'target_audience', 'level')
        }),
        ('Pricing', {
            'fields': ('original_price', 'discounted_price')
        }),
        ('Media', {
            'fields': ('thumbnail', 'intro_video')
        }),
        ('Additional Info', {
            'fields': ('language', 'duration', 'is_published')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class LectureAdminForm(forms.ModelForm):
    """Custom form for Lecture admin to handle video uploads"""

    class Meta:
        model = Lecture
        fields = '__all__'

    def clean_video_file(self):
        """Validate video file upload"""
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            # Check file size (max 2GB)
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            if video_file.size > max_size:
                raise forms.ValidationError('Video file size cannot exceed 2GB.')

            # Check file extension
            allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
            file_ext = video_file.name.lower().split('.')[-1]
            if f'.{file_ext}' not in allowed_extensions:
                raise forms.ValidationError(
                    f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'
                )

        return video_file

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    form = LectureAdminForm
    list_display = ['title', 'section', 'order', 'duration', 'processing_status', 'is_preview']
    list_filter = ['is_preview', 'processing_status', 'created_at', 'section__course']
    search_fields = ['title', 'description', 'section__title']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'processing_status']
    fieldsets = (
        ('Basic Information', {
            'fields': ('section', 'title', 'description', 'order')
        }),
        ('Media', {
            'fields': ('video_file', 'processing_status', 'duration', 'file_size', 'is_preview')
        }),
        ('Advanced Videos (Optional)', {
            'fields': ('video_1080p', 'video_720p', 'video_480p', 'video_360p', 'hls_playlist'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Override save_model to trigger video processing when saving from admin"""
        # Check if video_file was uploaded or changed
        if hasattr(obj, 'video_file') and obj.video_file:
            # If this is a new lecture or video file changed
            if not change or 'video_file' in form.changed_data:
                # Reset processing status to trigger new processing
                obj.processing_status = 'pending'
                obj.duration = 0
                obj.file_size = 0

                # Clear any existing processed files
                obj.video_1080p = None
                obj.video_720p = None
                obj.video_480p = None
                obj.video_360p = None
                obj.hls_playlist = None

        # Save the object first
        super().save_model(request, obj, form, change)

        # Trigger video processing if video was uploaded
        if hasattr(obj, 'video_file') and obj.video_file and obj.processing_status == 'pending':
            try:
                from .video_utils import process_lecture_video_universal
                import threading

                # Start universal video processing
                thread = threading.Thread(target=process_lecture_video_universal, args=(obj.id,))
                thread.daemon = True
                thread.start()

                # Add success message
                from django.contrib import messages
                messages.success(request, f'Lecture "{obj.title}" saved. Video processing started in background.')

            except Exception as e:
                from django.contrib import messages
                messages.error(request, f'Lecture saved but video processing failed to start: {str(e)}')
                print(f"Video processing start error: {e}")
                import traceback
                traceback.print_exc()

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'lecture', 'resource_type', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['title', 'lecture__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('lecture', 'title', 'resource_type')
        }),
        ('Content', {
            'fields': ('file', 'external_link')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'completed']
    list_filter = ['completed', 'enrolled_at']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at', 'last_accessed']
    fieldsets = (
        (None, {
            'fields': ('user', 'course', 'completed')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at', 'completed_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'lecture', 'completed', 'last_position', 'updated_at']
    list_filter = ['completed', 'updated_at']
    search_fields = ['enrollment__student__email', 'lecture__title']
    readonly_fields = ['updated_at']
    fieldsets = (
        (None, {
            'fields': ('enrollment', 'lecture', 'completed', 'last_position')
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['course__title', 'student__email', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('course', 'student', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
