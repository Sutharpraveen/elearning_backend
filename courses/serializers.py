from rest_framework import serializers
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from users.serializers import UserProfileSerializer
from categories.serializers import SimpleCategorySerializer  # updated import
from django.db import models


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

    class Meta:
        model = Lecture
        fields = [
            'id', 'title', 'description', 'video',
            'duration', 'duration_display', 'is_preview',
            'order', 'resources', 'created_at', 'updated_at'
        ]

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
    student = UserProfileSerializer(read_only=True)
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'student', 'rating', 'comment',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['student']

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%B %d, %Y")


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserProfileSerializer(read_only=True)
    category = SimpleCategorySerializer(read_only=True)  # updated to prevent nested loop
    sections = SectionSerializer(many=True, read_only=True)
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
            'sections', 'reviews', 'average_rating', 'total_students',
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
    student = UserProfileSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'student', 'enrolled_at',
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
