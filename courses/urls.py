from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, SectionViewSet, LectureViewSet,
    ResourceViewSet, EnrollmentViewSet
)

router = DefaultRouter()
router.register('', CourseViewSet, basename='course')

urlpatterns = [
    # Course routes
    path('', include(router.urls)),
    
    # Section routes
    path('<int:course_id>/sections/', SectionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='course-sections'),
    path('<int:course_id>/sections/<int:pk>/', SectionViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='course-section-detail'),
    
    # Lecture routes
    path('<int:course_id>/sections/<int:section_id>/lectures/', LectureViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='section-lectures'),
    path('<int:course_id>/sections/<int:section_id>/lectures/<int:pk>/', LectureViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='section-lecture-detail'),
    
    # Resource routes
    path('<int:course_id>/sections/<int:section_id>/lectures/<int:lecture_id>/resources/', 
        ResourceViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), name='lecture-resources'),
    path('<int:course_id>/sections/<int:section_id>/lectures/<int:lecture_id>/resources/<int:pk>/',
        ResourceViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), name='lecture-resource-detail'),
    
    # Enrollment routes
    path('enrollments/', EnrollmentViewSet.as_view({
        'get': 'list'
    }), name='enrollments'),
    path('enrollments/<int:pk>/', EnrollmentViewSet.as_view({
        'get': 'retrieve'
    }), name='enrollment-detail'),
]
