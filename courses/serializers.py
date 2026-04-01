from rest_framework import serializers
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from categories.serializers import SimpleCategorySerializer
from django.conf import settings


class InstructorMiniSerializer(serializers.Serializer):
    """Lightweight serializer for instructor info in list views. No DB queries."""
    id = serializers.IntegerField()
    full_name = serializers.SerializerMethodField()
    profile_image = serializers.ImageField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class ResourceSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ['id', 'lecture', 'title', 'file', 'file_size', 'file_extension', 'created_at']
        read_only_fields = ['created_at']

    def get_file_size(self, obj):
        try:
            return obj.file.size
        except Exception:
            return 0

    def get_file_extension(self, obj):
        import os
        return os.path.splitext(obj.file.name)[1].lower()


class LectureSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    duration_display = serializers.SerializerMethodField()
    video_urls = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = [
            'id', 'title', 'description', 'video_file',
            'video_urls', 'processing_status',
            'duration', 'duration_display', 'file_size',
            'order', 'is_preview', 'resources', 'created_at', 'updated_at'
        ]
        read_only_fields = ['video_urls', 'processing_status', 'file_size']

    def get_duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}:{seconds:02d}"

    def get_video_urls(self, obj):
        request = self.context.get('request')
        if not request:
            return {}

        base_url = request.build_absolute_uri('/').rstrip('/')

        # Access check for non-preview videos
        if not obj.is_preview:
            user = request.user
            has_access = False
            
            if user and user.is_authenticated:
                course_id = obj.section.course_id
                
                # Cache enrollment status in context to avoid N+1 queries
                cache_key = f'has_access_{course_id}'
                if cache_key not in self.context:
                    from .models import Course, Enrollment
                    is_instructor = Course.objects.filter(id=course_id, instructor=user).exists()
                    is_enrolled = Enrollment.objects.filter(user=user, course_id=course_id).exists()
                    self.context[cache_key] = is_instructor or is_enrolled
                
                has_access = self.context[cache_key]
                
            if not has_access:
                return {
                    'status': 'locked',
                    'stream_type': None,
                    'primary_url': None,
                    'message': 'Please enroll in the course to access this lecture.'
                }

        if obj.processing_status != 'completed':
            return {
                'status': obj.processing_status,
                'stream_type': None,
                'primary_url': None
            }

        video_data = {
            'status': 'ready',
            'stream_type': 'mp4',
            'hls_url': None,
            'primary_url': None,
            'qualities': {},
            'available_qualities': []
        }

        if obj.hls_playlist:
            video_data['hls_url'] = f"{base_url}{obj.hls_playlist.url}"
            video_data['primary_url'] = video_data['hls_url']
            video_data['stream_type'] = 'hls'
            video_data['available_qualities'] = ['1080p', '720p', '480p', '360p']

        quality_map = {
            '1080p': obj.video_1080p,
            '720p': obj.video_720p,
            '480p': obj.video_480p,
            '360p': obj.video_360p,
        }

        for quality, field in quality_map.items():
            if field:
                url = f"{base_url}{field.url}"
                video_data['qualities'][quality] = url
                if quality not in video_data['available_qualities']:
                    video_data['available_qualities'].append(quality)
                if not video_data['primary_url']:
                    video_data['primary_url'] = url

        if not video_data['primary_url'] and obj.video_file:
            orig_url = f"{base_url}{obj.video_file.url}"
            video_data['primary_url'] = orig_url
            video_data['qualities']['original'] = orig_url
            if 'original' not in video_data['available_qualities']:
                video_data['available_qualities'].append('original')

        return video_data


class SectionSerializer(serializers.ModelSerializer):
    lectures = LectureSerializer(many=True, read_only=True)
    total_lectures = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['id', 'title', 'order', 'lectures', 'total_lectures', 'total_duration']

    def get_total_lectures(self, obj):
        return len(obj.lectures.all())

    def get_total_duration(self, obj):
        total_seconds = sum(lecture.duration for lecture in obj.lectures.all())
        if total_seconds == 0:
            return "0m"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class ReviewListSerializer(serializers.ModelSerializer):
    """Lightweight review serializer for list views."""
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'user_name', 'created_at']

    def get_user_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username


class ReviewSerializer(serializers.ModelSerializer):
    """Full review serializer for detail/create views."""
    user_name = serializers.SerializerMethodField()
    user_image = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'course', 'rating', 'comment', 'user_name', 'user_image', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_user_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username

    def get_user_image(self, obj):
        if obj.student.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.student.profile_image.url)
        return None

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


# ============================
# COURSE LIST (Lightweight) - Used in search, home, browse
# ============================
class CourseListSerializer(serializers.ModelSerializer):
    """Fast serializer for course listings. No nested sections/lectures/reviews."""
    instructor = InstructorMiniSerializer(read_only=True)
    category = SimpleCategorySerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    total_lectures = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description',
            'level', 'original_price', 'discounted_price', 'language',
            'thumbnail', 'is_published',
            'instructor', 'category',
            'average_rating', 'total_students', 'total_lectures', 'review_count',
            'created_at'
        ]

    def get_average_rating(self, obj):
        avg = getattr(obj, 'avg_rating', None)
        if avg is not None:
            return round(float(avg), 1)
        return 0.0

    def get_total_students(self, obj):
        return getattr(obj, 'annotated_students_count', 0)

    def get_total_lectures(self, obj):
        return getattr(obj, 'annotated_lectures_count', 0)

    def get_review_count(self, obj):
        return getattr(obj, 'annotated_review_count', 0)


# ============================
# COURSE DETAIL (Full) - Used for single course page
# ============================
class CourseDetailSerializer(serializers.ModelSerializer):
    """Full serializer for course detail page with all nested data."""
    instructor = InstructorMiniSerializer(read_only=True)
    category = SimpleCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    sections = SectionSerializer(many=True, read_only=True)
    reviews = ReviewListSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    total_lectures = serializers.SerializerMethodField()
    total_duration_display = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'instructor', 'category', 'category_id',
            'title', 'slug', 'description', 'learning_objectives',
            'requirements', 'target_audience', 'level',
            'original_price', 'discounted_price', 'language',
            'duration', 'thumbnail', 'intro_video', 'is_published',
            'sections', 'reviews', 'average_rating', 'total_students',
            'total_lectures', 'total_duration_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['instructor', 'slug', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        avg = getattr(obj, 'avg_rating', None)
        if avg is not None:
            return round(float(avg), 1)
        reviews = obj.reviews.all()
        if not reviews:
            return 0.0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_total_students(self, obj):
        return getattr(obj, 'annotated_students_count', obj.enrollments.count())

    def get_total_lectures(self, obj):
        return obj.total_lectures_count

    def get_total_duration_display(self, obj):
        total_hours = float(obj.duration or 0)
        hours = int(total_hours)
        minutes = int((total_hours - hours) * 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def validate_discounted_price(self, value):
        try:
            original_price = float(self.initial_data.get('original_price', 0))
            if value and float(value) >= original_price:
                raise serializers.ValidationError("Discounted price must be less than original price.")
        except (ValueError, TypeError):
            pass
        return value


# ============================
# ENROLLMENT SERIALIZERS
# ============================
class EnrollmentCourseSerializer(serializers.ModelSerializer):
    """Minimal course info for enrollment list. No nested sections/lectures."""
    instructor_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', default='')
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'thumbnail', 'level',
            'instructor_name', 'category_name', 'average_rating'
        ]

    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip() or obj.instructor.username

    def get_average_rating(self, obj):
        avg = getattr(obj, 'avg_rating', None)
        if avg is not None:
            return round(float(avg), 1)
        return 0.0


class EnrollmentSerializer(serializers.ModelSerializer):
    course = EnrollmentCourseSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'enrolled_at',
            'completed', 'completed_at', 'last_accessed',
            'progress_percentage'
        ]
        read_only_fields = ['enrolled_at', 'completed_at', 'last_accessed']

    def get_progress_percentage(self, obj):
        return obj.progress_percentage


class ProgressSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)
    lecture_duration = serializers.IntegerField(source='lecture.duration', read_only=True)

    class Meta:
        model = Progress
        fields = [
            'id', 'lecture', 'lecture_title', 'lecture_duration',
            'completed', 'last_position', 'updated_at'
        ]
        read_only_fields = ['updated_at']

    def validate_last_position(self, value):
        if value < 0:
            raise serializers.ValidationError("Video position cannot be negative.")
        lecture_id = self.initial_data.get('lecture')
        if lecture_id:
            try:
                lecture = Lecture.objects.get(id=lecture_id)
                if value > lecture.duration:
                    return lecture.duration
            except Lecture.DoesNotExist:
                pass
        return value
