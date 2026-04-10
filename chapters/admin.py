from django.contrib import admin
from .models import Chapter, ChapterSection


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'course']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']


@admin.register(ChapterSection)
class ChapterSectionAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'section', 'order']
    list_filter = ['chapter__course']
    search_fields = ['chapter__title', 'section__title']
    ordering = ['chapter', 'order']
