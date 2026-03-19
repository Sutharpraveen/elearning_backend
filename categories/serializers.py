from rest_framework import serializers
from .models import Category
from courses.models import Course


class CourseInCategorySerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    total_lectures = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'thumbnail', 'instructor_name',
            'description', 'level', 'original_price',
            'discounted_price', 'rating', 'total_lectures',
            'total_students', 'duration', 'created_at', 'updated_at'
        ]

    def get_total_lectures(self, obj):
        return sum(section.lectures.count() for section in obj.sections.all())

    def get_total_students(self, obj):
        return obj.enrollments.count()

    def get_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / reviews.count(), 2)
        return 0.0


class SimpleCategorySerializer(serializers.ModelSerializer):
    total_courses = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'total_courses']

    def get_total_courses(self, obj):
        return getattr(obj, 'annotated_total_courses', obj.courses.count())


class CategoryListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    total_courses = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'image_url', 'total_courses', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_total_courses(self, obj):
        return getattr(obj, 'annotated_total_courses', obj.courses.count())


class CategoryDetailSerializer(CategoryListSerializer):
    courses = CourseInCategorySerializer(many=True, read_only=True)

    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + ['courses']
