from rest_framework import serializers
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from users.serializers import UserProfileSerializer
from categories.serializers import SimpleCategorySerializer  # updated import
from django.db import models
from django.conf import settings
import os


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'resource_type', 'file',
            'external_link', 'created_at', 'updated_at'
        ]


class LectureSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    duration_display = serializers.SerializerMethodField()
    video_urls = serializers.SerializerMethodField()
    processing_status = serializers.CharField(read_only=True)

    class Meta:
        model = Lecture
        fields = [
            'id', 'title', 'description', 'video_file',
            'video_urls', 'processing_status',
            'duration', 'duration_display', 'file_size', 'is_preview',
            'order', 'resources', 'created_at', 'updated_at'
        ]
        read_only_fields = ['video_urls', 'processing_status', 'file_size']

    def get_duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}:{seconds:02d}"

    def get_video_urls(self, obj):
        """Return primary video URL and available qualities"""
        request = self.context.get('request')
        if not request:
            return {}

        base_url = request.build_absolute_uri('/').rstrip('/')
        video_data = {
            'primary_url': None,
            'available_qualities': [],
            'stream_type': 'mp4'  # default
        }

        # Priority: HLS > Processed qualities > Direct MP4 (fallback)
        if obj.hls_playlist and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.hls_playlist))):
            # HLS streaming (best - adaptive bitrate)
            video_data['primary_url'] = f"{base_url}{obj.hls_playlist.url}"
            video_data['stream_type'] = 'hls'
            video_data['available_qualities'] = ['1080p', '720p', '480p', '360p']  # HLS handles all qualities
        elif obj.video_720p and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.video_720p))):
            # Processed HD quality
            video_data['primary_url'] = f"{base_url}{obj.video_720p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['720p', '480p', '360p']
        elif obj.video_480p and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.video_480p))):
            # Processed SD quality
            video_data['primary_url'] = f"{base_url}{obj.video_480p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['480p', '360p']
        elif obj.video_360p and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.video_360p))):
            # Processed mobile quality
            video_data['primary_url'] = f"{base_url}{obj.video_360p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['360p']
        elif obj.video_1080p and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.video_1080p))):
            # Processed full HD quality
            video_data['primary_url'] = f"{base_url}{obj.video_1080p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['1080p']
        elif obj.video_file and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(obj.video_file))):
            # Direct MP4 upload - fallback when no processing done
            video_data['primary_url'] = f"{base_url}{obj.video_file.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['original']
        elif obj.video_720p and os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.video_720p.name)):
            video_data['primary_url'] = f"{base_url}{obj.video_720p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['720p', '480p', '360p']
        elif obj.video_480p and os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.video_480p.name)):
            video_data['primary_url'] = f"{base_url}{obj.video_480p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['480p', '360p']
        elif obj.video_360p and os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.video_360p.name)):
            video_data['primary_url'] = f"{base_url}{obj.video_360p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['360p']
        elif obj.video_1080p and os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.video_1080p.name)):
            video_data['primary_url'] = f"{base_url}{obj.video_1080p.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['1080p']
        elif hasattr(obj, 'original_video') and obj.original_video and os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.original_video.name)):
            # Legacy fallback to original video
            video_data['primary_url'] = f"{base_url}{obj.original_video.url}"
            video_data['stream_type'] = 'mp4'
            video_data['available_qualities'] = ['original']

        return video_data

    def get_duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}:{seconds:02d}"


class SectionSerializer(serializers.ModelSerializer):
    lectures = LectureSerializer(many=True, read_only=True)
    total_lectures = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'description', 'order',
            'lectures', 'total_lectures', 'total_duration',
            'created_at', 'updated_at'
        ]

    def get_total_lectures(self, obj):
        return obj.lectures.count()

    def get_total_duration(self, obj):
        total_seconds = sum(lecture.duration for lecture in obj.lectures.all())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'course', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# class CourseSerializer(serializers.ModelSerializer):
#     instructor = UserProfileSerializer(read_only=True)
#     category = SimpleCategorySerializer(read_only=True)  # updated to prevent nested loop
#     sections = SectionSerializer(many=True, read_only=True)
#     reviews = ReviewSerializer(many=True, read_only=True)
#     category_id = serializers.IntegerField(write_only=True)
#     average_rating = serializers.SerializerMethodField()
#     total_students = serializers.SerializerMethodField()
#     total_lectures = serializers.SerializerMethodField()
#     total_duration = serializers.SerializerMethodField()

#     class Meta:
#         model = Course
#         fields = [
#             'id', 'instructor', 'category', 'category_id',
#             'title', 'slug', 'description', 'learning_objectives',
#             'requirements', 'target_audience', 'level',
#             'original_price', 'discounted_price', 'language',
#             'duration', 'thumbnail', 'intro_video', 'is_published',
#             'sections', 'reviews', 'average_rating', 'total_students',
#             'total_lectures', 'total_duration', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['instructor', 'slug', 'created_at', 'updated_at']

#     def get_average_rating(self, obj):
#         reviews = obj.reviews.all()
#         if not reviews:
#             return 0
#         return round(sum(review.rating for review in reviews) / len(reviews), 1)

#     def get_total_students(self, obj):
#         return obj.enrollments.count()

#     def get_total_lectures(self, obj):
#         return sum(section.lectures.count() for section in obj.sections.all())

#     def get_total_duration(self, obj):
#         total_seconds = sum(
#             lecture.duration
#             for section in obj.sections.all()
#             for lecture in section.lectures.all()
#         )
#         hours = total_seconds // 3600
#         minutes = (total_seconds % 3600) // 60
#         return f"{hours}h {minutes}m"

#     def validate_discounted_price(self, value):
#         original_price = float(self.initial_data.get('original_price', 0))
#         if value and value >= original_price:
#             raise serializers.ValidationError(
#                 "Discounted price must be less than original price"
#             )
#         return value



class CourseSerializer(serializers.ModelSerializer):
    instructor = UserProfileSerializer(read_only=True)
    category = SimpleCategorySerializer(read_only=True)  # updated to prevent nested loop
    reviews = ReviewSerializer(many=True, read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    average_rating = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    total_lectures = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'instructor', 'category', 'category_id',
            'title', 'slug', 'description', 'learning_objectives',
            'requirements', 'target_audience', 'level',
            'original_price', 'discounted_price', 'language',
            'duration', 'thumbnail', 'intro_video', 'is_published',
            'reviews', 'average_rating', 'total_students',
            'total_lectures', 'total_duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['instructor', 'slug', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    def get_total_students(self, obj):
        return obj.enrollments.count()

    def get_total_lectures(self, obj):
        return sum(section.lectures.count() for section in obj.sections.all())

    def get_total_duration(self, obj):
        total_seconds = sum(
            lecture.duration
            for section in obj.sections.all()
            for lecture in section.lectures.all()
        )
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def validate_discounted_price(self, value):
        original_price = float(self.initial_data.get('original_price', 0))
        if value and value >= original_price:
            raise serializers.ValidationError(
                "Discounted price must be less than original price"
            )
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'user', 'enrolled_at',
            'completed', 'completed_at', 'last_accessed',
            'progress_percentage'
        ]
        read_only_fields = ['enrolled_at', 'completed_at', 'last_accessed']

    def get_progress_percentage(self, obj):
        total_lectures = sum(section.lectures.count() for section in obj.course.sections.all())
        if total_lectures == 0:
            return 0
        completed_lectures = obj.progress.filter(completed=True).count()
        return round((completed_lectures / total_lectures) * 100, 1)


class ProgressSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)

    class Meta:
        model = Progress
        fields = [
            'id', 'lecture', 'lecture_title', 'completed',
            'last_position', 'updated_at'
        ]
        read_only_fields = ['updated_at']

    def validate_last_position(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Video position cannot be negative"
            )
        return value
