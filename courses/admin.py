from django.contrib import admin
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review

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

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order', 'duration', 'is_preview']
    list_filter = ['is_preview', 'created_at', 'section__course']
    search_fields = ['title', 'description', 'section__title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('section', 'title', 'description', 'order')
        }),
        ('Media', {
            'fields': ('video', 'duration', 'is_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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
    list_display = ['student', 'course', 'enrolled_at', 'completed']
    list_filter = ['completed', 'enrolled_at']
    search_fields = ['student__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at', 'last_accessed']
    fieldsets = (
        (None, {
            'fields': ('student', 'course', 'completed')
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
