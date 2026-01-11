from rest_framework import serializers
from .models import Category
from courses.models import Course

# Serializer for Course inside Category
class CourseInCategorySerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    total_lectures = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'thumbnail',
            'instructor_name',
            'description',
            'level',
            'original_price',
            'discounted_price',
            'rating',
            'total_lectures',
            'total_students',
            'duration',
            'created_at',
            'updated_at'
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


# ✅ Base Category Serializer with shared methods
class BaseCategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    total_courses = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'image',
            'image_url',
            'total_courses',
            'created_at',
            'updated_at'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_total_courses(self, obj):
        return obj.courses.count()


# ✅ Full Category Serializer with courses included
class CategorySerializer(BaseCategorySerializer):
    courses = CourseInCategorySerializer(many=True, read_only=True)

    class Meta(BaseCategorySerializer.Meta):
        fields = BaseCategorySerializer.Meta.fields + ['courses']


# ✅ Simplified Category List Serializer (for listings only)
class CategoryListSerializer(BaseCategorySerializer):
    pass


# ✅ Detailed Category Serializer (with extra stats)
class CategoryDetailSerializer(BaseCategorySerializer):
    courses = CourseInCategorySerializer(many=True, read_only=True)
    total_students = serializers.SerializerMethodField()
    total_instructors = serializers.SerializerMethodField()

    class Meta(BaseCategorySerializer.Meta):
        fields = BaseCategorySerializer.Meta.fields + [
            'total_students',
            'total_instructors',
            'courses'
        ]

    def get_total_students(self, obj):
        return sum(course.enrollments.count() for course in obj.courses.all())

    def get_total_instructors(self, obj):
        return obj.courses.values('instructor').distinct().count()



# Simple serializer to avoid infinite nesting
class SimpleCategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    total_courses = serializers.SerializerMethodField()  # 👈 New field

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'image_url', 'total_courses']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_total_courses(self, obj):
        return obj.courses.count()  # assumes related_name='courses' in Course model

