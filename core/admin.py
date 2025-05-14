from django.contrib import admin
from .models import SliderImage, AppVersion

@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'is_active',
        'show_from',
        'show_until',
        'webinar_time',
        'course',
        'category',
        'created_at'
    ]
    list_filter = ['is_active', 'course', 'category']
    search_fields = ['title', 'course__title', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    date_hierarchy = 'show_from'
    ordering = ['-created_at']

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ('Basic Information', {
                'fields': ['title', 'image', 'is_active']
            }),
            ('Display Settings', {
                'fields': ['show_from', 'show_until', 'webinar_time']
            }),
            ('Links and Relations', {
                'fields': ['redirect_url', 'course', 'category']
            }),
        ]
        if obj:  # editing existing object
            base_fieldsets.append(
                ('Timestamps', {
                    'fields': ['created_at', 'updated_at'],
                    'classes': ['collapse']
                })
            )
        return base_fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = [
        'platform',
        'latest_version',
        'force_update',
        'download_url',
        'created_at'
    ]
    list_filter = ['platform', 'force_update']
    search_fields = ['platform', 'latest_version']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['force_update']
    ordering = ['-created_at']

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ('Version Information', {
                'fields': [
                    'platform',
                    'latest_version',
                    'force_update',
                    'download_url'
                ]
            }),
        ]
        if obj:
            base_fieldsets.append(
                ('Timestamps', {
                    'fields': ['created_at', 'updated_at'],
                    'classes': ['collapse']
                })
            )
        return base_fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []
