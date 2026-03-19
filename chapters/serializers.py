from rest_framework import serializers
from .models import Chapter, ChapterSection
from courses.serializers import SectionSerializer


class ChapterSectionSerializer(serializers.ModelSerializer):
    section_details = SectionSerializer(source='section', read_only=True)

    class Meta:
        model = ChapterSection
        fields = [
            'id', 'chapter', 'section', 'section_details', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']


class ChapterSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()
    lectures_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    sections = ChapterSectionSerializer(source='chapter_sections', many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = [
            'id', 'course', 'course_title', 'title', 'description',
            'order', 'sections_count', 'lectures_count', 'total_duration',
            'sections', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_sections_count(self, obj):
        return obj.sections_count

    def get_lectures_count(self, obj):
        return obj.lectures_count

    def get_total_duration(self, obj):
        total_seconds = obj.total_duration
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"