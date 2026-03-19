from rest_framework import serializers
from .models import SliderImage, AppVersion


class SliderImageSerializer(serializers.ModelSerializer):
    course_details = serializers.SerializerMethodField()
    category_details = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    is_live = serializers.ReadOnlyField(source='is_currently_live')

    class Meta:
        model = SliderImage
        fields = [
            'id', 'title', 'image', 'image_url', 'is_active', 'is_live',
            'show_from', 'show_until', 'webinar_time', 'redirect_url',
            'course', 'course_details', 'category', 'category_details',
            'created_at', 'updated_at'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def get_course_details(self, obj):
        if obj.course:
            return {"id": obj.course.id, "title": obj.course.title}
        return None

    def get_category_details(self, obj):
        if obj.category:
            return {"id": obj.category.id, "name": obj.category.name}
        return None


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'
