# from django.contrib import admin
# from .models import Category

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'display_image' ,'description', 'created_at', 'updated_at']
#     list_filter = ['created_at', 'updated_at']
#     search_fields = ['name', 'description']
#     readonly_fields = ['created_at', 'updated_at']
#     list_per_page = 25
    
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'description')
#         }),
#         ('Media', {
#             'fields': ('image',)
#         })
#     )

#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # editing an existing object
#             return self.readonly_fields
#         return []

#     def get_fieldsets(self, request, obj=None):
#         fieldsets = list(super().get_fieldsets(request, obj))
#         if obj:  # Only show timestamps when editing an existing object
#             fieldsets.append(
#                 ('Timestamps', {
#                     'fields': ('created_at', 'updated_at'),
#                     'classes': ('collapse',)
#                 })
#             )
#         return fieldsets


from django.contrib import admin
from django.utils.html import format_html # Ye import zaroori hai HTML dikhane ke liye
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # list_display mein 'course_count' bhi add kiya hai
    list_display = ['display_image', 'name', 'course_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )

    # 🖼️ 1. Image Preview Logic
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:10px; object-fit:cover;" />', obj.image.url)
        return format_html('<span style="color: #999;">No Image</span>')
    
    display_image.short_description = 'Preview'

    # 📊 2. Quick Course Count logic
    def course_count(self, obj):
        count = obj.courses.count()
        if count > 0:
            return format_html('<b>{} Courses</b>', count)
        return "0 Courses"
    
    course_count.short_description = 'Total Courses'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj:
            fieldsets.append(
                ('Timestamps', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',)
                })
            )
        return fieldsets