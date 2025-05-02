from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.text import slugify
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from .serializers import (
    CourseSerializer, SectionSerializer, LectureSerializer,
    ResourceSerializer, EnrollmentSerializer, ProgressSerializer, ReviewSerializer
)

# Create your views here.

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    #permission_classes = [IsAuthenticatedOrReadOnly]
    permission_classes = [IsAuthenticated]  # Allows read-only access to unauthenticated users
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'level', 'language']
    ordering_fields = ['created_at', 'title', 'original_price']


    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
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
    
    # ✅ New action to get courses by category ID
    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>\d+)')
    def by_category(self, request, category_id=None):
        courses = self.queryset.filter(category_id=category_id, is_published=True)
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)

class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Section.objects.filter(course_id=self.kwargs['course_pk'])

    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        if course.instructor != self.request.user:
            raise PermissionError("You don't have permission to modify this course")
        serializer.save(course=course)

class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Lecture.objects.filter(
            section_id=self.kwargs['section_pk'],
            section__course_id=self.kwargs['course_pk']
        )

class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Resource.objects.filter(lecture_id=self.kwargs['lecture_pk'])

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Progress.objects.filter(enrollment__student=self.request.user)
