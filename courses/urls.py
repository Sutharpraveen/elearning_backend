from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, SectionViewSet, LectureViewSet,
    ResourceViewSet, EnrollmentViewSet
)

router = DefaultRouter()
router.register('courses', CourseViewSet, basename='course')
router.register('courses/(?P<course_pk>\d+)/sections', SectionViewSet, basename='course-sections')
router.register('courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures', LectureViewSet, basename='section-lectures')
router.register('courses/(?P<course_pk>\d+)/sections/(?P<section_pk>\d+)/lectures/(?P<lecture_pk>\d+)/resources', ResourceViewSet, basename='lecture-resources')
router.register('enrollments', EnrollmentViewSet, basename='enrollments')

urlpatterns = [
    # Automatically generated routes by the router
    path('', include(router.urls)),
]
