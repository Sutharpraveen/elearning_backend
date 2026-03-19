# from django.contrib import admin
# from .models import SliderImage, AppVersion

# @admin.register(SliderImage)
# class SliderImageAdmin(admin.ModelAdmin):
#     list_display = [
#         'title',
#         'is_active',
#         'show_from',
#         'show_until',
#         'webinar_time',
#         'course',
#         'category',
#         'created_at'
#     ]
#     list_filter = ['is_active', 'course', 'category']
#     search_fields = ['title', 'course__title', 'category__name']
#     readonly_fields = ['created_at', 'updated_at']
#     list_editable = ['is_active']
#     date_hierarchy = 'show_from'
#     ordering = ['-created_at']

#     def get_fieldsets(self, request, obj=None):
#         base_fieldsets = [
#             ('Basic Information', {
#                 'fields': ['title', 'image', 'is_active']
#             }),
#             ('Display Settings', {
#                 'fields': ['show_from', 'show_until', 'webinar_time']
#             }),
#             ('Links and Relations', {
#                 'fields': ['redirect_url', 'course', 'category']
#             }),
#         ]
#         if obj:  # editing existing object
#             base_fieldsets.append(
#                 ('Timestamps', {
#                     'fields': ['created_at', 'updated_at'],
#                     'classes': ['collapse']
#                 })
#             )
#         return base_fieldsets

#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return self.readonly_fields
#         return []

# @admin.register(AppVersion)
# class AppVersionAdmin(admin.ModelAdmin):
#     list_display = [
#         'platform',
#         'latest_version',
#         'force_update',
#         'download_url',
#         'created_at'
#     ]
#     list_filter = ['platform', 'force_update']
#     search_fields = ['platform', 'latest_version']
#     readonly_fields = ['created_at', 'updated_at']
#     list_editable = ['force_update']
#     ordering = ['-created_at']

#     def get_fieldsets(self, request, obj=None):
#         base_fieldsets = [
#             ('Version Information', {
#                 'fields': [
#                     'platform',
#                     'latest_version',
#                     'force_update',
#                     'download_url'
#                 ]
#             }),
#         ]
#         if obj:
#             base_fieldsets.append(
#                 ('Timestamps', {
#                     'fields': ['created_at', 'updated_at'],
#                     'classes': ['collapse']
#                 })
#             )
#         return base_fieldsets

#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return self.readonly_fields
#         return []



from django.contrib import admin
from django.utils.html import format_html # Image preview ke liye
from .models import SliderImage, AppVersion

@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    # 'display_preview' add kiya taaki banner admin mein hi dikh jaye
    list_display = [
        'display_preview', 
        'title',
        'is_active',
        'course',
        'category',
        'show_from',
        'show_until',
    ]
    list_filter = ['is_active', 'course', 'category', 'show_from']
    search_fields = ['title', 'course__title', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active'] # List se hi active/inactive kar sakte hain
    date_hierarchy = 'show_from'
    ordering = ['-created_at']

    # 🖼️ Image Preview Logic
    def display_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="120" style="border-radius:8px; border: 1px solid #ddd;"/>', obj.image.url)
        return "No Banner"
    display_preview.short_description = 'Banner Preview'

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            ('Basic Information', {
                'fields': ['title', 'image', 'is_active']
            }),
            ('Display Schedule', {
                'fields': ['show_from', 'show_until', 'webinar_time'],
                'description': 'Banner kab dikhana hai aur webinar ka time kya hai.'
            }),
            ('Target & Linking', {
                'fields': ['redirect_url', 'course', 'category'],
                'description': 'Slider par click karne se kahan jana hai.'
            }),
        ]
        if obj:
            base_fieldsets.append(
                ('System Info', {
                    'fields': ['created_at', 'updated_at'],
                    'classes': ['collapse']
                })
            )
        return base_fieldsets

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = [
        'platform_icon',
        'latest_version',
        'force_update',
        'created_at'
    ]
    list_filter = ['platform', 'force_update']
    list_editable = ['force_update']
    
    # 📱 Platform ke liye sundar icons
    def platform_icon(self, obj):
        icon = "📱" if obj.platform == 'android' else "🍎"
        return format_html('<b>{} {}</b>', icon, obj.platform.upper())
    platform_icon.short_description = 'Platform'

    def get_fieldsets(self, request, obj=None):
        return [
            ('Version Control', {
                'fields': ['platform', 'latest_version', 'force_update', 'download_url']
            }),
        ]