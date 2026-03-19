from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, SectionViewSet, LectureViewSet,
    ResourceViewSet, EnrollmentViewSet, ProgressViewSet,
    global_search, home_page_courses, top_rated_courses, rating_statistics
)

# 1. Main router for simple endpoints
router = DefaultRouter()
router.register('courses', CourseViewSet, basename='course')
router.register('enrollments', EnrollmentViewSet, basename='enrollments')
router.register('progress', ProgressViewSet, basename='progress')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # 2. Custom API Endpoints (Home & Search)
    path('search/', global_search, name='global-search'),
    path('home/', home_page_courses, name='home-page-courses'),
    path('top-rated/', top_rated_courses, name='top-rated-courses'),
    path('rating-statistics/', rating_statistics, name='rating-statistics'),

    # 3. Manual Nested Routes (Udemy-Style)
    
    # Sections: /courses/1/sections/
    re_path(r'^courses/(?P<course_pk>\d+)/sections/$', SectionViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='course-sections-list'),

    re_path(r'^courses/(?P<course_pk>\d+)/sections/(?P<pk>\d+)/$', SectionViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    }), name='course-sections-detail'),

    # Lectures: /courses/1/sections/2/lectures/
    re_path(r'^courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/$', LectureViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='section-lectures-list'),

    re_path(r'^courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<pk>\d+)/$', LectureViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    }), name='section-lectures-detail'),

    # Resources: /courses/1/sections/2/lectures/3/resources/
    re_path(r'^courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<lecture_pk>\d+)/resources/$', ResourceViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='lecture-resources-list'),

    re_path(r'^courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<lecture_pk>\d+)/resources/(?P<pk>\d+)/$', ResourceViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    }), name='lecture-resources-detail'),
]