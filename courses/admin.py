from django.contrib import admin
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from django import forms
from django.contrib import messages


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'level', 'is_published', 'created_at']
    list_filter = ['is_published', 'level', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title', 'course__title']
    readonly_fields = []


class LectureAdminForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = '__all__'

    def clean_video_file(self):
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            max_size = 2 * 1024 * 1024 * 1024
            if video_file.size > max_size:
                raise forms.ValidationError('Video file must not exceed 2GB.')
        return video_file


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    form = LectureAdminForm
    list_display = ['title', 'section', 'order', 'processing_status', 'duration']
    list_filter = ['processing_status', 'section__course']
    readonly_fields = ['processing_status', 'duration', 'file_size', 'created_at']

    fieldsets = (
        ('Basic Info', {'fields': ('section', 'title', 'description', 'order')}),
        ('Video Upload', {'fields': ('video_file', 'processing_status', 'duration', 'file_size')}),
        ('Processed Versions (Read Only)', {
            'fields': ('video_1080p', 'video_720p', 'video_480p', 'video_360p', 'hls_playlist'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if 'video_file' in form.changed_data or not change:
            obj.processing_status = 'pending'

        super().save_model(request, obj, form, change)

        if obj.video_file and obj.processing_status == 'pending':
            from .tasks import process_lecture_video_task
            from django.db import transaction
            
            def trigger_task():
                try:
                    process_lecture_video_task.delay(obj.id)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to trigger video processing task: {e}")
                    
            transaction.on_commit(trigger_task)
            messages.success(request, f'Video saved successfully. Processing started for "{obj.title}" (Requires Redis for background processing).')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'lecture', 'file']
    list_filter = ['lecture__section__course']
    readonly_fields = ['created_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'completed']
    readonly_fields = ['enrolled_at', 'completed_at', 'last_accessed']


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'lecture', 'completed', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'rating', 'created_at']
    readonly_fields = ['created_at']
