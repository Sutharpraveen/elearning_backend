from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, SectionViewSet, LectureViewSet,
    ResourceViewSet, EnrollmentViewSet, ProgressViewSet
)

# Main router
router = DefaultRouter()
router.register('courses', CourseViewSet, basename='course')
router.register('enrollments', EnrollmentViewSet, basename='enrollments')
router.register('progress', ProgressViewSet, basename='progress')

urlpatterns = [
    # Main routes
    path('', include(router.urls)),

    # Nested routes using re_path for regex matching
    re_path(r'^(?P<course_pk>\d+)/sections/$', SectionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='course-sections-list'),

    re_path(r'^(?P<course_pk>\d+)/sections/(?P<pk>\d+)/$', SectionViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='course-sections-detail'),

    re_path(r'^(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/$', LectureViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='section-lectures-list'),

    re_path(r'^(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<pk>\d+)/$', LectureViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='section-lectures-detail'),

    re_path(r'^(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<lecture_pk>\d+)/resources/$', ResourceViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='lecture-resources-list'),

    re_path(r'^(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<lecture_pk>\d+)/resources/(?P<pk>\d+)/$', ResourceViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='lecture-resources-detail'),
]
