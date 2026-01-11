from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.text import slugify
from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from .serializers import (
    CourseSerializer, SectionSerializer, LectureSerializer,
    ResourceSerializer, EnrollmentSerializer, ProgressSerializer, ReviewSerializer
)
from django.utils import timezone
from .video_utils import process_lecture_video_universal
from users.models import CustomUser
from django.db.models import Q, Count, Avg
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
    search_fields = ['title', 'description', 'level', 'language', 'instructor__username', 'instructor__first_name', 'instructor__last_name']
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
            user=request.user,
            course=course
        )
        return Response({'status': 'enrolled' if created else 'already enrolled'})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        course = self.get_object()

        # Check if user is enrolled in the course
        try:
            enrollment = Enrollment.objects.get(user=request.user, course=course)
        except Enrollment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You must be enrolled in this course to leave a review'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if user has already reviewed this course
        existing_review = Review.objects.filter(student=request.user, course=course).first()
        if existing_review:
            return Response({
                'status': 'error',
                'message': 'You have already reviewed this course. You can update your existing review.',
                'existing_review': ReviewSerializer(existing_review).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Optional: Check minimum progress before allowing review
        min_progress_required = 50  # 50% course completion required
        if enrollment.progress_percentage < min_progress_required:
            return Response({
                'status': 'error',
                'message': f'You must complete at least {min_progress_required}% of the course before leaving a review',
                'current_progress': enrollment.progress_percentage
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(student=request.user, course=course)

            # Return updated course data with new average rating
            course_serializer = self.get_serializer(course)
            return Response({
                'status': 'success',
                'message': 'Review submitted successfully',
                'review': ReviewSerializer(review).data,
                'course': course_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Invalid review data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'])
    def update_review(self, request, pk=None):
        """Update existing review"""
        course = self.get_object()

        try:
            review = Review.objects.get(student=request.user, course=course)
        except Review.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You have not reviewed this course yet'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            updated_review = serializer.save()

            # Return updated course data
            course_serializer = self.get_serializer(course)
            return Response({
                'status': 'success',
                'message': 'Review updated successfully',
                'review': ReviewSerializer(updated_review).data,
                'course': course_serializer.data
            })

        return Response({
            'status': 'error',
            'message': 'Invalid review data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a course"""
        course = self.get_object()
        reviews = course.reviews.all().order_by('-created_at')

        # Pagination
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'status': 'success',
            'count': reviews.count(),
            'reviews': serializer.data
        })

    @action(detail=True, methods=['delete'])
    def delete_review(self, request, pk=None):
        """Delete user's review"""
        course = self.get_object()

        try:
            review = Review.objects.get(student=request.user, course=course)
            review.delete()

            # Return updated course data
            course_serializer = self.get_serializer(course)
            return Response({
                'status': 'success',
                'message': 'Review deleted successfully',
                'course': course_serializer.data
            })

        except Review.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def my_review(self, request, pk=None):
        """Get user's review for this course"""
        course = self.get_object()

        try:
            review = Review.objects.get(student=request.user, course=course)
            return Response({
                'status': 'success',
                'has_review': True,
                'review': ReviewSerializer(review).data
            })
        except Review.DoesNotExist:
            return Response({
                'status': 'success',
                'has_review': False,
                'message': 'You have not reviewed this course yet'
            })


@api_view(['GET'])
@permission_classes([AllowAny])
def top_rated_courses(request):
    """
    Get top-rated courses with high ratings and good review counts
    """
    try:
        min_reviews = request.GET.get('min_reviews', 5)  # Minimum reviews to be considered
        limit = request.GET.get('limit', 10)  # Number of courses to return

        # Get courses with good ratings and sufficient reviews
        courses = Course.objects.filter(
            is_published=True
        ).annotate(
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating'),
            total_students=Count('enrollments')
        ).filter(
            review_count__gte=min_reviews,
            avg_rating__gte=4.0  # Only 4+ star courses
        ).order_by('-avg_rating', '-review_count')[:int(limit)]

        courses_data = []
        for course in courses:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if course.instructor.profile_image else None
                },
                'category': {
                    'id': course.category.id,
                    'name': course.category.name
                },
                'average_rating': round(float(course.avg_rating), 1),
                'review_count': course.review_count,
                'total_students': course.total_students,
                'original_price': str(course.original_price),
                'discounted_price': str(course.discounted_price) if course.discounted_price else None,
                'level': course.level
            })

        return Response({
            'status': 'success',
            'count': len(courses_data),
            'courses': courses_data
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to fetch top-rated courses: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def rating_statistics(request):
    """
    Get overall rating statistics for the platform
    """
    try:
        # Overall platform statistics
        total_courses = Course.objects.filter(is_published=True).count()
        total_reviews = Review.objects.count()
        total_students = Enrollment.objects.count()

        # Rating distribution
        rating_counts = {}
        for rating in range(1, 6):
            rating_counts[f'{rating}_star'] = Review.objects.filter(rating=rating).count()

        # Average rating across all courses
        courses_with_reviews = Course.objects.filter(
            is_published=True,
            reviews__isnull=False
        ).distinct().annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

        platform_avg_rating = 0
        if courses_with_reviews:
            total_ratings = sum(course.avg_rating * course.review_count for course in courses_with_reviews)
            total_review_count = sum(course.review_count for course in courses_with_reviews)
            platform_avg_rating = round(total_ratings / total_review_count, 1) if total_review_count > 0 else 0

        return Response({
            'status': 'success',
            'platform_statistics': {
                'total_courses': total_courses,
                'total_reviews': total_reviews,
                'total_students': total_students,
                'average_rating': platform_avg_rating,
                'courses_with_reviews': len(courses_with_reviews)
            },
            'rating_distribution': rating_counts,
            'rating_percentages': {
                f'{rating}_star': round((count / total_reviews * 100), 1) if total_reviews > 0 else 0
                for rating, count in rating_counts.items()
            }
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to fetch rating statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
            def process_video_background():
                try:
                    result = process_lecture_video_universal(lecture.id)
                    print(f"Video processing completed for lecture {lecture.title}: {result}")
                except Exception as e:
                    print(f"Background video processing error for lecture {lecture.title}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            thread = threading.Thread(target=process_video_background)
            thread.daemon = False  # Don't make it daemon so it completes
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
            def process_video_background():
                try:
                    result = process_lecture_video_universal(lecture.id)
                    print(f"Video processing completed for lecture {lecture.title}: {result}")
                except Exception as e:
                    print(f"Background video processing error for lecture {lecture.title}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            thread = threading.Thread(target=process_video_background)
            thread.daemon = False  # Don't make it daemon so it completes
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

    @action(detail=False, methods=['get'])
    def continue_learning(self, request):
        """
        Get courses for continue learning with detailed progress info
        """
        enrollments = self.get_queryset().filter(completed=False).order_by('-last_accessed')

        response_data = []
        for enrollment in enrollments:
            # Get last accessed lecture
            last_progress = enrollment.progress.filter(
                completed=False
            ).order_by('-updated_at').first()

            # Get next lecture (first incomplete lecture)
            next_lecture = None
            for section in enrollment.course.sections.order_by('order'):
                for lecture in section.lectures.order_by('order'):
                    progress = enrollment.progress.filter(lecture=lecture).first()
                    if not progress or not progress.completed:
                        next_lecture = lecture
                        break
                if next_lecture:
                    break

            enrollment_data = EnrollmentSerializer(enrollment, context={'request': request}).data

            # Add continue learning specific data
            enrollment_data['continue_learning'] = {
                'next_lecture': {
                    'id': next_lecture.id if next_lecture else None,
                    'title': next_lecture.title if next_lecture else None,
                    'duration': next_lecture.duration if next_lecture else None,
                    'duration_display': f"{next_lecture.duration//60}:{next_lecture.duration%60:02d}" if next_lecture else None,
                } if next_lecture else None,
                'last_watched_lecture': {
                    'id': last_progress.lecture.id if last_progress else None,
                    'title': last_progress.lecture.title if last_progress else None,
                    'last_position': last_progress.last_position if last_progress else None,
                    'completed': last_progress.completed if last_progress else False,
                } if last_progress else None,
                'total_completed_lectures': enrollment.progress.filter(completed=True).count(),
                'total_lectures': sum(section.lectures.count() for section in enrollment.course.sections.all()),
            }

            response_data.append(enrollment_data)

        return Response({
            'status': 'success',
            'count': len(response_data),
            'data': response_data
        })

class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]  # Requires authentication for all actions

    def get_queryset(self):
        return Progress.objects.filter(enrollment__user=self.request.user)

    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        """Get detailed progress for a specific course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({
                'status': 'error',
                'message': 'course_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course_id=course_id
            )
        except Enrollment.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You are not enrolled in this course'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get all sections and lectures with progress
        sections_data = []
        total_lectures = 0
        completed_lectures = 0
        total_duration = 0
        watched_duration = 0

        for section in enrollment.course.sections.all().order_by('order'):
            section_lectures = []
            section_completed = 0
            section_total = section.lectures.count()
            section_duration = 0
            section_watched = 0

            for lecture in section.lectures.all().order_by('order'):
                progress_obj = enrollment.progress.filter(lecture=lecture).first()
                lecture_progress = {
                    'id': lecture.id,
                    'title': lecture.title,
                    'duration': lecture.duration,
                    'completed': progress_obj.completed if progress_obj else False,
                    'last_position': progress_obj.last_position if progress_obj else 0,
                    'updated_at': progress_obj.updated_at.isoformat() if progress_obj else None
                }

                section_lectures.append(lecture_progress)
                total_lectures += 1
                total_duration += lecture.duration
                section_duration += lecture.duration

                if progress_obj and progress_obj.completed:
                    completed_lectures += 1
                    section_completed += 1
                    watched_duration += lecture.duration
                    section_watched += lecture.duration
                elif progress_obj:
                    # Partial progress - estimate watched time
                    watched_duration += min(progress_obj.last_position / 60, lecture.duration)
                    section_watched += min(progress_obj.last_position / 60, lecture.duration)

            # Calculate section progress based on completed lectures
            section_progress_percentage = round((section_completed / section_total) * 100, 1) if section_total > 0 else 0

            sections_data.append({
                'id': section.id,
                'title': section.title,
                'lectures': section_lectures,
                'completed_lectures': section_completed,
                'total_lectures': section_total,
                'progress_percentage': section_progress_percentage,
                'total_duration': section_duration,
                'watched_duration': section_watched
            })

        # Calculate progress based on completed lectures (clearer for users)
        progress_percentage = round((completed_lectures / total_lectures) * 100, 1) if total_lectures > 0 else 0

        # Ensure progress doesn't exceed 100%
        progress_percentage = min(progress_percentage, 100.0)

        # Mark as completed if 100% progress
        if progress_percentage >= 100 and not enrollment.completed:
            enrollment.completed = True
            enrollment.completed_at = timezone.now()
            enrollment.save()

        return Response({
            'status': 'success',
            'data': {
                'course_id': enrollment.course.id,
                'course_title': enrollment.course.title,
                'enrolled_at': enrollment.enrolled_at.isoformat(),
                'last_accessed': enrollment.last_accessed.isoformat() if enrollment.last_accessed else None,
                'completed': enrollment.completed,
                'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                'progress_percentage': progress_percentage,
                'total_lectures': total_lectures,
                'completed_lectures': completed_lectures,
                'remaining_lectures': total_lectures - completed_lectures,
                'total_duration': total_duration,
                'watched_duration': watched_duration,
                'sections': sections_data
            }
        })

    @action(detail=False, methods=['get'])
    def continue_learning(self, request):
        """Find the next lecture to watch (Udemy-style continue learning)"""
        try:
            # Get all user's enrollments
            enrollments = Enrollment.objects.filter(
                user=request.user,
                completed=False
            ).select_related('course')

            if not enrollments:
                return Response({
                    'status': 'success',
                    'message': 'No active courses to continue',
                    'data': None
                })

            # Find the most recently accessed enrollment
            enrollment = max(enrollments, key=lambda e: e.last_accessed or e.enrolled_at)

            # Find next lecture to watch
            next_lecture = None
            next_section = None

            for section in enrollment.course.sections.all().order_by('order'):
                for lecture in section.lectures.all().order_by('order'):
                    progress_obj = enrollment.progress.filter(lecture=lecture).first()

                    # If lecture not started or not completed, this is next
                    if not progress_obj or not progress_obj.completed:
                        next_lecture = lecture
                        next_section = section
                        break

                if next_lecture:
                    break

            # If all lectures completed but course not marked complete, mark it
            if not next_lecture and not enrollment.completed:
                total_lectures = sum(section.lectures.count() for section in enrollment.course.sections.all())
                completed_lectures = enrollment.progress.filter(completed=True).count()

                if completed_lectures == total_lectures:
                    enrollment.completed = True
                    enrollment.completed_at = timezone.now()
                    enrollment.save()

                    return Response({
                        'status': 'success',
                        'message': 'Course completed!',
                        'data': {
                            'course_completed': True,
                            'completed_at': enrollment.completed_at.isoformat(),
                            'progress_percentage': 100.0
                        }
                    })

            if next_lecture:
                progress_obj = enrollment.progress.filter(lecture=next_lecture).first()

                return Response({
                    'status': 'success',
                    'data': {
                        'course': {
                            'id': enrollment.course.id,
                            'title': enrollment.course.title,
                            'thumbnail': enrollment.course.thumbnail.url if enrollment.course.thumbnail else None
                        },
                        'next_lecture': {
                            'id': next_lecture.id,
                            'title': next_lecture.title,
                            'section_title': next_section.title,
                            'duration': next_lecture.duration,
                            'last_position': progress_obj.last_position if progress_obj else 0,
                            'completed': progress_obj.completed if progress_obj else False
                        },
                        'progress_percentage': enrollment.progress_percentage,
                        'last_accessed': enrollment.last_accessed.isoformat() if enrollment.last_accessed else None
                    }
                })
            else:
                return Response({
                    'status': 'success',
                    'message': 'All lectures completed',
                    'data': {
                        'course_completed': enrollment.completed,
                        'progress_percentage': 100.0
                    }
                })

        except Exception as e:
            import traceback
            print(f"Continue learning error: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'Failed to get continue learning data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


@api_view(['GET'])
@permission_classes([AllowAny])
def home_page_courses(request):
    """
    Home page API that returns all published courses with pagination
    Similar to Udemy/Coursera home page course listings
    """
    try:
        from django.core.paginator import Paginator

        # Get query parameters
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 12)  # Default 12 courses per page
        category = request.GET.get('category')
        level = request.GET.get('level')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        search = request.GET.get('search')
        sort_by = request.GET.get('sort', 'created_at')  # Default sort by newest

        # Base queryset - only published courses
        courses = Course.objects.filter(is_published=True).select_related('instructor', 'category')

        # Apply filters
        if category:
            courses = courses.filter(category__name__icontains=category)

        if level:
            courses = courses.filter(level__iexact=level)

        if price_min:
            try:
                price_min = float(price_min)
                courses = courses.filter(discounted_price__gte=price_min)
            except ValueError:
                pass

        if price_max:
            try:
                price_max = float(price_max)
                courses = courses.filter(discounted_price__lte=price_max)
            except ValueError:
                pass

        if search:
            courses = courses.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(instructor__first_name__icontains=search) |
                Q(instructor__last_name__icontains=search) |
                Q(category__name__icontains=search)
            )

        # Apply sorting
        sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_low': 'discounted_price',
            'price_high': '-discounted_price',
            'rating': '-average_rating',
            'popular': '-total_students'
        }

        sort_field = sort_options.get(sort_by, '-created_at')
        courses = courses.order_by(sort_field)

        # Add annotations for better performance
        courses = courses.annotate(
            total_students=Count('enrollments'),
            avg_rating=Avg('reviews__rating')
        )

        # Pagination
        try:
            page_size = min(int(page_size), 50)  # Max 50 per page
            paginator = Paginator(courses, page_size)
            page_obj = paginator.page(page)
        except Exception:
            return Response({
                'status': 'error',
                'message': 'Invalid page number'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare course data
        courses_data = []
        for course in page_obj.object_list:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'description': course.description[:150] + '...' if len(course.description) > 150 else course.description,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'original_price': str(course.original_price),
                'discounted_price': str(course.discounted_price) if course.discounted_price else None,
                'level': course.level,
                'language': course.language,
                'duration': str(course.duration),
                'total_students': course.total_students,
                'average_rating': round(float(course.avg_rating), 1) if course.avg_rating else 0,
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if course.instructor.profile_image else None
                },
                'category': {
                    'id': course.category.id,
                    'name': course.category.name
                },
                'created_at': course.created_at.isoformat(),
                'is_featured': getattr(course, 'is_featured', False),  # For future featured courses
                'tags': getattr(course, 'tags', [])  # For future tags feature
            })

        return Response({
            'status': 'success',
            'data': {
                'courses': courses_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_courses': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                    'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                    'page_size': page_size
                },
                'filters_applied': {
                    'category': category,
                    'level': level,
                    'price_min': price_min,
                    'price_max': price_max,
                    'search': search,
                    'sort_by': sort_by
                }
            }
        })

    except Exception as e:
        import traceback
        print(f"Home page courses error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'message': f'Failed to load courses: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    """
    Udemy-style comprehensive search API that searches across courses and instructors
    """
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({
                'status': 'error',
                'message': 'Search query is required. Use ?q=your_search_term'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Search courses
        courses = Course.objects.filter(
            Q(is_published=True) & (
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(learning_objectives__icontains=query) |
                Q(requirements__icontains=query) |
                Q(target_audience__icontains=query) |
                Q(level__icontains=query) |
                Q(language__icontains=query) |
                Q(instructor__first_name__icontains=query) |
                Q(instructor__last_name__icontains=query) |
                Q(instructor__username__icontains=query) |
                Q(category__name__icontains=query)
            )
        ).select_related('instructor', 'category').annotate(
            total_students=Count('enrollments'),
            avg_rating=Avg('reviews__rating')
        )[:20]  # Limit results

        # Search instructors
        instructors = CustomUser.objects.filter(
            Q(role='instructor') & (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(bio__icontains=query) |
                Q(headline__icontains=query) |
                Q(expertise__icontains=query)
            )
        ).annotate(
            total_courses=Count('course', filter=Q(course__is_published=True)),
            total_students=Count('course__enrollments', filter=Q(course__is_published=True))
        )[:10]  # Limit results

        # Prepare response data
        courses_data = []
        for course in courses:
            courses_data.append({
                'id': course.id,
                'type': 'course',
                'title': course.title,
                'slug': course.slug,
                'description': course.description[:200] + '...' if len(course.description) > 200 else course.description,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'original_price': str(course.original_price),
                'discounted_price': str(course.discounted_price) if course.discounted_price else None,
                'level': course.level,
                'language': course.language,
                'duration': str(course.duration),
                'total_students': course.total_students,
                'average_rating': round(float(course.avg_rating), 1) if course.avg_rating else 0,
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if course.instructor.profile_image else None,
                    'headline': course.instructor.headline
                },
                'category': {
                    'id': course.category.id,
                    'name': course.category.name
                },
                'created_at': course.created_at.isoformat()
            })

        instructors_data = []
        for instructor in instructors:
            instructors_data.append({
                'id': instructor.id,
                'type': 'instructor',
                'name': instructor.get_full_name(),
                'username': instructor.username,
                'email': instructor.email,
                'profile_image': instructor.profile_image.url if instructor.profile_image else None,
                'headline': instructor.headline,
                'bio': instructor.bio[:300] + '...' if instructor.bio and len(instructor.bio) > 300 else instructor.bio,
                'expertise': instructor.expertise,
                'total_courses': instructor.total_courses,
                'total_students': instructor.total_students,
                'profile_completion': instructor.profile_completion_percentage if hasattr(instructor, 'profile_completion_percentage') else 0,
                'social_links': instructor.social_links,
                'website': instructor.website
            })

        # Combine and sort results (courses first, then instructors)
        combined_results = courses_data + instructors_data

        return Response({
            'status': 'success',
            'query': query,
            'total_results': len(combined_results),
            'courses_count': len(courses_data),
            'instructors_count': len(instructors_data),
            'results': combined_results
        })

    except Exception as e:
        import traceback
        print(f"Search error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'message': f'Search failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
