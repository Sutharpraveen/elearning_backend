from rest_framework import serializers
from .models import SliderImage, AppVersion
from courses.serializers import CourseSerializer
from categories.serializers import CategorySerializer

class SliderImageSerializer(serializers.ModelSerializer):
    course_details = CourseSerializer(source='course', read_only=True)
    category_details = CategorySerializer(source='category', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SliderImage
        fields = [
            'id',
            'title',
            'image',
            'image_url',
            'is_active',
            'show_from',
            'show_until',
            'webinar_time',
            'redirect_url',
            'course',
            'course_details',
            'category',
            'category_details',
            'created_at',
            'updated_at'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = [
            'id',
            'platform',
            'latest_version',
            'force_update',
            'download_url',
            'created_at',
            'updated_at'
        ]