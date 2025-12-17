from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.text import slugify
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from .serializers import (
    CourseSerializer, SectionSerializer, LectureSerializer,
    ResourceSerializer, EnrollmentSerializer, ProgressSerializer, ReviewSerializer
)
from django.utils import timezone
from .video_utils import process_lecture_video_universal
import threading


class IsEnrolled(BasePermission):
    """
    Custom permission to only allow enrolled users to access course content
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # For Section, Lecture, Resource objects, check enrollment
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'section') and hasattr(obj.section, 'course'):
            course = obj.section.course
        elif hasattr(obj, 'lecture') and hasattr(obj.lecture, 'section') and hasattr(obj.lecture.section, 'course'):
            course = obj.lecture.section.course
        else:
            return False

        return Enrollment.objects.filter(user=request.user, course=course).exists()

# Create your views here.

# class CourseViewSet(viewsets.ModelViewSet):
#     queryset = Course.objects.all()
#     serializer_class = CourseSerializer
#     #permission_classes = [IsAuthenticatedOrReadOnly]
#     permission_classes = [IsAuthenticated]  # Allows read-only access to unauthenticated users
#     parser_classes = (MultiPartParser, FormParser)
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['title', 'description', 'level', 'language']
#     ordering_fields = ['created_at', 'title', 'original_price']


#     def get_queryset(self):
#         queryset = super().get_queryset()
#         category_id = self.request.query_params.get('category')
#         if category_id:
#             queryset = queryset.filter(category_id=category_id)
#         return queryset

#     def perform_create(self, serializer):
#         title = serializer.validated_data['title']
#         slug = slugify(title)
#         serializer.save(instructor=self.request.user, slug=slug)

#     @action(detail=True, methods=['post'])
#     def enroll(self, request, pk=None):
#         course = self.get_object()
#         enrollment, created = Enrollment.objects.get_or_create(
#             student=request.user,
#             course=course
#         )
#         return Response({'status': 'enrolled' if created else 'already enrolled'})

#     @action(detail=True, methods=['post'])
#     def review(self, request, pk=None):
#         course = self.get_object()
#         serializer = ReviewSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(student=request.user, course=course)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     # ✅ New action to get courses by category ID
#     @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>\d+)')
#     def by_category(self, request, category_id=None):
#         courses = self.queryset.filter(category_id=category_id, is_published=True)
#         serializer = self.get_serializer(courses, many=True)
#         return Response(serializer.data)



class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]  # Allows read-only access to unauthenticated users
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'level', 'language']
    ordering_fields = ['created_at', 'title', 'original_price']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(category_id=category_id)
            except ValueError:
                queryset = queryset.none()
        return queryset

    def perform_create(self, serializer):
        title = serializer.validated_data['title']
        slug = slugify(title)
        serializer.save(instructor=self.request.user, slug=slug)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        return Response({'status': 'enrolled' if created else 'already enrolled'})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        course = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user, course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>\\d+)')
    def by_category(self, request, category_id=None):
        courses = self.queryset.filter(category_id=category_id, is_published=True)
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]  # Requires authentication and enrollment

    def get_queryset(self):
        return Section.objects.filter(course_id=self.kwargs['course_pk'])

    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        if course.instructor != self.request.user:
            raise PermissionError("You don't have permission to modify this course")
        serializer.save(course=course)

class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]  # Requires authentication and enrollment
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Lecture.objects.filter(
            section_id=self.kwargs['section_pk'],
            section__course_id=self.kwargs['course_pk']
        )

    def perform_create(self, serializer):
        lecture = serializer.save()

        # If any video was uploaded, start universal processing
        if (hasattr(lecture, 'video_file') and lecture.video_file) or \
           (hasattr(lecture, 'original_video') and lecture.original_video):
            # Start universal video processing in background thread
            thread = threading.Thread(target=process_lecture_video_universal, args=(lecture.id,))
            thread.daemon = True
            thread.start()
            print(f"Universal video processing started for lecture: {lecture.title}")
        else:
            # No video uploaded, mark as ready
            lecture.processing_status = 'ready'
            lecture.save()

    def perform_update(self, serializer):
        lecture = serializer.save()

        # If any video was uploaded/updated, start universal processing
        if ((hasattr(lecture, 'video_file') and lecture.video_file) or \
            (hasattr(lecture, 'original_video') and lecture.original_video)) and \
           lecture.processing_status != 'processing':

            # Start universal video processing in background thread
            thread = threading.Thread(target=process_lecture_video_universal, args=(lecture.id,))
            thread.daemon = True
            thread.start()
            print(f"Universal video processing started for updated lecture: {lecture.title}")
        else:
            # No video change, keep current status
            pass

class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]  # Requires authentication and enrollment
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Resource.objects.filter(lecture_id=self.kwargs['lecture_pk'])

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)

class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Progress.objects.filter(enrollment__user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        try:
            progress = self.get_object()
            completed = request.data.get('completed', progress.completed)
            last_position = request.data.get('last_position', progress.last_position)

            # Update progress
            progress.completed = completed
            progress.last_position = last_position
            progress.save()

            # Update enrollment's last_accessed
            enrollment = progress.enrollment
            enrollment.last_accessed = timezone.now()
            enrollment.save()

            # Check if all lectures are completed
            total_lectures = sum(section.lectures.count() for section in enrollment.course.sections.all())
            completed_lectures = enrollment.progress.filter(completed=True).count()

            if completed_lectures == total_lectures and not enrollment.completed:
                enrollment.completed = True
                enrollment.completed_at = timezone.now()
                enrollment.save()

            return Response({
                'status': 'success',
                'message': 'Progress updated successfully',
                'data': {
                    'progress_id': progress.id,
                    'lecture_id': progress.lecture.id,
                    'completed': progress.completed,
                    'last_position': progress.last_position,
                    'course_completed': enrollment.completed
                }
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
