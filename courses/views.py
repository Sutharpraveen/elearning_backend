import logging
import uuid
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg, Case, When, IntegerField, Value
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied

from .models import Course, Section, Lecture, Resource, Enrollment, Progress, Review
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, SectionSerializer, LectureSerializer,
    ResourceSerializer, EnrollmentSerializer, ProgressSerializer, ReviewSerializer
)
from .tasks import process_lecture_video_task
from users.models import CustomUser
from categories.models import Category

logger = logging.getLogger(__name__)


class IsEnrolled(BasePermission):
    """Allow access to course instructor or enrolled students."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Protect List APIs (like /sections/ and /lectures/) by checking course_pk in URL
        course_pk = view.kwargs.get('course_pk')
        if course_pk:
            try:
                course = Course.objects.get(pk=course_pk)
                if course.instructor != request.user and not Enrollment.objects.filter(user=request.user, course=course).exists():
                    return False
            except Course.DoesNotExist:
                return False
                
        return True

    def has_object_permission(self, request, view, obj):
        course = None
        if isinstance(obj, Course):
            course = obj
        elif hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'section'):
            course = obj.section.course
        elif hasattr(obj, 'lecture'):
            course = obj.lecture.section.course

        if not course:
            return False

        if course.instructor == request.user:
            return True

        return Enrollment.objects.filter(user=request.user, course=course).exists()


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'level', 'language', 'instructor__username', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['created_at', 'title', 'original_price']

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        queryset = Course.objects.select_related('instructor', 'category')

        if self.action == 'list':
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating'),
                annotated_students_count=Count('enrollments', distinct=True),
                annotated_lectures_count=Count('sections__lectures', distinct=True),
                annotated_review_count=Count('reviews', distinct=True),
            )
        else:
            queryset = queryset.prefetch_related(
                'sections__lectures__resources',
                'reviews__student',
            ).annotate(
                avg_rating=Avg('reviews__rating'),
                annotated_students_count=Count('enrollments', distinct=True),
            )

        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
                queryset = queryset.none()
        return queryset

    def perform_create(self, serializer):
        title = serializer.validated_data['title']
        base_slug = slugify(title)

        unique_slug = base_slug
        while Course.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        serializer.save(instructor=self.request.user, slug=unique_slug)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course
        )
        return Response({
            'status': 'success',
            'message': 'enrolled' if created else 'already enrolled'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        course = self.get_object()

        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if not enrollment:
            return Response({
                'status': 'error',
                'message': 'You must be enrolled in this course to leave a review'
            }, status=status.HTTP_403_FORBIDDEN)

        if Review.objects.filter(student=request.user, course=course).exists():
            return Response({
                'status': 'error',
                'message': 'You have already reviewed this course. You can update your existing review.'
            }, status=status.HTTP_400_BAD_REQUEST)

        min_progress_required = 50
        if enrollment.progress_percentage < min_progress_required:
            return Response({
                'status': 'error',
                'message': f'You must complete at least {min_progress_required}% of the course before leaving a review',
                'current_progress': enrollment.progress_percentage
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(student=request.user, course=course)
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
        course = self.get_object()
        review = Review.objects.filter(student=request.user, course=course).first()

        if not review:
            return Response({
                'status': 'error',
                'message': 'You have not reviewed this course yet'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            updated_review = serializer.save()
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
        course = self.get_object()
        reviews = course.reviews.all().order_by('-created_at')
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
        course = self.get_object()
        review = Review.objects.filter(student=request.user, course=course).first()

        if not review:
            return Response({
                'status': 'error',
                'message': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)

        review.delete()
        course_serializer = self.get_serializer(course)
        return Response({
            'status': 'success',
            'message': 'Review deleted successfully',
            'course': course_serializer.data
        })

    @action(detail=True, methods=['get'])
    def my_review(self, request, pk=None):
        course = self.get_object()
        review = Review.objects.filter(student=request.user, course=course).first()

        if review:
            return Response({
                'status': 'success',
                'has_review': True,
                'review': ReviewSerializer(review).data
            })
        return Response({
            'status': 'success',
            'has_review': False,
            'message': 'You have not reviewed this course yet'
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def top_rated_courses(request):
    """Fetch courses with high ratings and good review counts."""
    try:
        try:
            min_reviews = int(request.GET.get('min_reviews', 5))
            limit = int(request.GET.get('limit', 10))
        except ValueError:
            min_reviews = 5
            limit = 10

        courses = Course.objects.filter(
            is_published=True
        ).select_related('instructor', 'category').annotate(
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating'),
            total_students=Count('enrollments')
        ).filter(
            review_count__gte=min_reviews,
            avg_rating__gte=4.0
        ).order_by('-avg_rating', '-review_count')[:limit]

        courses_data = []
        for course in courses:
            current_avg = round(float(course.avg_rating or 0), 1)

            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if hasattr(course.instructor, 'profile_image') and course.instructor.profile_image else None
                },
                'category': {
                    'id': course.category.id,
                    'name': course.category.name
                },
                'average_rating': current_avg,
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
        logger.error("Error in top_rated_courses: %s", e)
        return Response({
            'status': 'error',
            'message': 'Could not load top rated courses. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def rating_statistics(request):
    """Fetch platform-wide rating statistics in a single optimized query."""
    try:
        total_courses = Course.objects.filter(is_published=True).count()
        total_students = Enrollment.objects.count()

        stats = Review.objects.aggregate(
            overall_avg=Avg('rating'),
            total_revs=Count('id')
        )

        total_reviews = stats['total_revs'] or 0
        platform_avg_rating = round(stats['overall_avg'] or 0, 1)

        rating_data = Review.objects.values('rating').annotate(count=Count('rating'))

        rating_counts = {f'{i}_star': 0 for i in range(1, 6)}
        for item in rating_data:
            rating_counts[f"{item['rating']}_star"] = item['count']

        rating_percentages = {
            rating: round((count / total_reviews * 100), 1) if total_reviews > 0 else 0
            for rating, count in rating_counts.items()
        }

        courses_with_reviews_count = Course.objects.filter(
            is_published=True,
            reviews__isnull=False
        ).distinct().count()

        return Response({
            'status': 'success',
            'platform_statistics': {
                'total_courses': total_courses,
                'total_reviews': total_reviews,
                'total_students': total_students,
                'average_rating': platform_avg_rating,
                'courses_with_reviews': courses_with_reviews_count
            },
            'rating_distribution': rating_counts,
            'rating_percentages': rating_percentages
        })

    except Exception as e:
        logger.error("Error in rating_statistics: %s", e)
        return Response({
            'status': 'error',
            'message': 'Could not load rating statistics.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]

    def get_queryset(self):
        return Section.objects.filter(
            course_id=self.kwargs['course_pk']
        ).order_by('order')

    def perform_create(self, serializer):
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])

        if course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can add sections.")

        serializer.save(course=course)

    def perform_update(self, serializer):
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        if course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can update sections.")
        serializer.save()


class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Lecture.objects.filter(
            section_id=self.kwargs['section_pk'],
            section__course_id=self.kwargs['course_pk']
        ).order_by('order')

    def perform_create(self, serializer):
        section = get_object_or_404(Section, pk=self.kwargs['section_pk'])
        if section.course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can add lectures.")

        with transaction.atomic():
            lecture = serializer.save(section=section)

        self._start_video_processing(lecture)

    def perform_update(self, serializer):
        lecture_obj = self.get_object()
        if lecture_obj.section.course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can update lectures.")

        with transaction.atomic():
            lecture = serializer.save()

        if 'video_file' in self.request.FILES or 'original_video' in self.request.FILES:
            self._start_video_processing(lecture)

    def _start_video_processing(self, lecture):
        """Dispatch video processing to Celery if a video file exists."""
        video_exists = (hasattr(lecture, 'video_file') and lecture.video_file) or \
                       (hasattr(lecture, 'original_video') and lecture.original_video)

        if video_exists:
            lecture.processing_status = 'processing'
            lecture.save()

            transaction.on_commit(lambda: process_lecture_video_task.delay(lecture.id))

            logger.info("Video processing task dispatched for lecture: %s", lecture.title)
        else:
            lecture.processing_status = 'ready'
            lecture.save()


class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Resource.objects.filter(
            lecture_id=self.kwargs['lecture_pk']
        ).select_related('lecture')

    def perform_create(self, serializer):
        lecture = get_object_or_404(Lecture, pk=self.kwargs['lecture_pk'])
        course = lecture.section.course

        if course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can add resources.")

        serializer.save(lecture=lecture)

    def perform_update(self, serializer):
        resource = self.get_object()
        if resource.lecture.section.course.instructor != self.request.user:
            raise PermissionDenied("Only the course instructor can update resources.")
        serializer.save()


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related(
            'course', 'course__instructor', 'course__category'
        ).prefetch_related('progress')

    @action(detail=False, methods=['get'])
    def continue_learning(self, request):
        """Fetch in-progress courses with detailed progress for resume functionality."""
        enrollments = self.get_queryset().filter(completed=False).order_by('-last_accessed')

        response_data = []
        for enrollment in enrollments:
            last_progress = enrollment.progress.filter(completed=False).order_by('-updated_at').first()

            next_lecture = None
            for section in enrollment.course.sections.all().order_by('order'):
                for lecture in section.lectures.all().order_by('order'):
                    prog_exists = any(p.lecture_id == lecture.id and p.completed for p in enrollment.progress.all())
                    if not prog_exists:
                        next_lecture = lecture
                        break
                if next_lecture:
                    break

            enrollment_data = EnrollmentSerializer(enrollment, context={'request': request}).data

            total_completed = enrollment.progress.filter(completed=True).count()
            total_lectures_count = sum(section.lectures.count() for section in enrollment.course.sections.all())

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
                'total_completed_lectures': total_completed,
                'total_lectures': total_lectures_count,
            }

            response_data.append(enrollment_data)

        return Response({
            'status': 'success',
            'count': len(response_data),
            'data': response_data
        })


class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(enrollment__user=self.request.user)

    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        """Get detailed progress for a specific course."""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'status': 'error', 'message': 'course_id is required'}, status=400)

        enrollment = get_object_or_404(
            Enrollment.objects.select_related('course').prefetch_related(
                'course__sections',
                'course__sections__lectures',
                'progress'
            ),
            user=request.user,
            course_id=course_id
        )

        sections_data = []
        total_lectures = 0
        completed_lectures = 0
        total_duration = 0
        watched_duration = 0

        all_progress = {p.lecture_id: p for p in enrollment.progress.all()}

        for section in enrollment.course.sections.all().order_by('order'):
            section_lectures = []
            section_completed = 0
            section_duration = 0
            section_watched = 0
            lectures = section.lectures.all().order_by('order')
            section_total = lectures.count()

            for lecture in lectures:
                prog_obj = all_progress.get(lecture.id)
                is_done = prog_obj.completed if prog_obj else False

                section_lectures.append({
                    'id': lecture.id,
                    'title': lecture.title,
                    'duration': lecture.duration,
                    'completed': is_done,
                    'last_position': prog_obj.last_position if prog_obj else 0,
                    'updated_at': prog_obj.updated_at.isoformat() if prog_obj else None
                })

                total_lectures += 1
                total_duration += lecture.duration
                section_duration += lecture.duration

                if is_done:
                    completed_lectures += 1
                    section_completed += 1
                    watched_duration += lecture.duration
                    section_watched += lecture.duration
                elif prog_obj:
                    watched_duration += min(prog_obj.last_position / 60, lecture.duration)
                    section_watched += min(prog_obj.last_position / 60, lecture.duration)

            sections_data.append({
                'id': section.id,
                'title': section.title,
                'lectures': section_lectures,
                'completed_lectures': section_completed,
                'total_lectures': section_total,
                'progress_percentage': round((section_completed / section_total * 100), 1) if section_total > 0 else 0,
                'total_duration': section_duration,
                'watched_duration': round(section_watched, 1)
            })

        progress_percentage = min(round((completed_lectures / total_lectures * 100), 1) if total_lectures > 0 else 0, 100.0)

        if progress_percentage >= 100:
            if not enrollment.completed:
                enrollment.completed = True
                enrollment.completed_at = timezone.now()
                enrollment.save()
        else:
            if enrollment.completed:
                enrollment.completed = False
                enrollment.completed_at = None
                enrollment.save()

        return Response({
            'status': 'success',
            'data': {
                'course_id': enrollment.course.id,
                'progress_percentage': progress_percentage,
                'total_lectures': total_lectures,
                'completed_lectures': completed_lectures,
                'total_duration': total_duration,
                'watched_duration': round(watched_duration, 1),
                'sections': sections_data
            }
        })

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update lecture progress with atomic transaction for data safety."""
        progress = self.get_object()
        completed = request.data.get('completed', progress.completed)
        last_position = request.data.get('last_position', progress.last_position)

        try:
            with transaction.atomic():
                progress.completed = completed
                progress.last_position = last_position
                progress.save()

                enrollment = progress.enrollment
                enrollment.last_accessed = timezone.now()

                total_lectures = Lecture.objects.filter(section__course=enrollment.course).count()
                completed_count = Progress.objects.filter(enrollment=enrollment, completed=True).count()

                if total_lectures > 0 and completed_count >= total_lectures:
                    if not enrollment.completed:
                        enrollment.completed = True
                        enrollment.completed_at = timezone.now()
                else:
                    if enrollment.completed:
                        enrollment.completed = False
                        enrollment.completed_at = None

                enrollment.save()

            return Response({
                'status': 'success',
                'data': {
                    'lecture_id': progress.lecture.id,
                    'completed': progress.completed,
                    'course_completed': enrollment.completed
                }
            })
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def home_page_courses(request):
    """Home page API with sorting, filtering, and pagination."""
    try:
        page = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 12)), 50)
        category = request.GET.get('category')
        level = request.GET.get('level')
        search = request.GET.get('search')
        sort_by = request.GET.get('sort', 'newest')

        courses = Course.objects.filter(is_published=True).select_related(
            'instructor', 'category'
        ).annotate(
            total_students=Count('enrollments', distinct=True),
            avg_rating=Avg('reviews__rating')
        )

        if category:
            courses = courses.filter(category__name__icontains=category)
        if level:
            courses = courses.filter(level__iexact=level)

        try:
            if request.GET.get('price_min'):
                courses = courses.filter(discounted_price__gte=float(request.GET.get('price_min')))
            if request.GET.get('price_max'):
                courses = courses.filter(discounted_price__lte=float(request.GET.get('price_max')))
        except (ValueError, TypeError):
            pass

        if search:
            courses = courses.filter(_course_search_q(search))
            courses = courses.annotate(_search_rank=_udemy_search_rank_case(search))
            sort_map = {
                'newest': ('_search_rank', '-created_at'),
                'oldest': ('_search_rank', 'created_at'),
                'price_low': ('_search_rank', 'discounted_price'),
                'price_high': ('_search_rank', '-discounted_price'),
                'rating': ('_search_rank', '-avg_rating'),
                'popular': ('_search_rank', '-total_students'),
                'relevance': ('_search_rank', '-total_students', '-avg_rating'),
            }
            courses = courses.order_by(*sort_map.get(sort_by, sort_map['relevance']))
        else:
            sort_map = {
                'newest': '-created_at',
                'oldest': 'created_at',
                'price_low': 'discounted_price',
                'price_high': '-discounted_price',
                'rating': '-avg_rating',
                'popular': '-total_students',
            }
            courses = courses.order_by(sort_map.get(sort_by, '-created_at'))

        paginator = Paginator(courses, page_size)
        try:
            page_obj = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        courses_data = []
        for course in page_obj:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'original_price': str(course.original_price),
                'discounted_price': str(course.discounted_price) if course.discounted_price else None,
                'level': course.level,
                'total_students': course.total_students,
                'average_rating': round(float(course.avg_rating or 0), 1),
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if hasattr(course.instructor, 'profile_image') and course.instructor.profile_image else None
                },
                'category': {'id': course.category.id, 'name': course.category.name},
                'created_at': course.created_at.isoformat(),
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
                }
            }
        })

    except Exception as e:
        logger.error("Home page error: %s", e)
        return Response({'status': 'error', 'message': 'Could not load courses.'}, status=500)


def _single_keyword_course_q(keyword):
    """One keyword: course text + instructor name/headline + category (Udemy-style breadth)."""
    if not keyword:
        return Q(pk=0)  # no match
    return (
        Q(title__icontains=keyword) |
        Q(description__icontains=keyword) |
        Q(learning_objectives__icontains=keyword) |
        Q(requirements__icontains=keyword) |
        Q(target_audience__icontains=keyword) |
        Q(instructor__first_name__icontains=keyword) |
        Q(instructor__last_name__icontains=keyword) |
        Q(instructor__username__icontains=keyword) |
        Q(instructor__headline__icontains=keyword) |
        Q(category__name__icontains=keyword) |
        Q(category__description__icontains=keyword)
    )


def _udemy_search_rank_case(search_text):
    """Relevance: 0 best — order_by this field ascending. Title first, then instructor name."""
    q = (search_text or '').strip()
    if not q:
        return Value(99)
    tokens = [t for t in q.split() if t]
    whens = [
        When(title__istartswith=q, then=Value(0)),
        When(title__icontains=q, then=Value(1)),
    ]
    if len(tokens) >= 2:
        whens.append(
            When(
                Q(instructor__first_name__icontains=tokens[0])
                & Q(instructor__last_name__icontains=tokens[-1]),
                then=Value(2),
            )
        )
        inst_rank = 3
    else:
        inst_rank = 2
    whens.append(
        When(
            Q(instructor__first_name__icontains=q)
            | Q(instructor__last_name__icontains=q)
            | Q(instructor__username__icontains=q)
            | Q(instructor__headline__icontains=q),
            then=Value(inst_rank),
        )
    )
    cat_rank = inst_rank + 1
    whens.append(When(category__name__icontains=q, then=Value(cat_rank)))
    return Case(*whens, default=Value(cat_rank + 1), output_field=IntegerField())


def _course_search_q(text):
    """OR across words: e.g. 'music theory' matches category Music OR title with Theory."""
    if not text:
        return Q()
    tokens = [t.strip() for t in text.split() if t.strip()]
    if not tokens:
        return Q()
    if len(tokens) == 1:
        return _single_keyword_course_q(tokens[0])
    q = Q()
    any_token = False
    for token in tokens:
        q |= _single_keyword_course_q(token)
        any_token = True
    if not any_token:
        return _single_keyword_course_q(text.strip())
    return q


def _category_tokens_q(text):
    """Categories whose name or description matches any word in text."""
    if not text:
        return Q(pk=0)
    tokens = [t.strip() for t in text.split() if t.strip()]
    if not tokens:
        return Q(name__icontains=text) | Q(description__icontains=text)
    q = Q()
    for token in tokens:
        q |= Q(name__icontains=token) | Q(description__icontains=token)
    return q


@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    """Search courses, instructors, and categories.

    Query params:
      - q: keyword(s) — matches title, description, objectives, category name/description, instructor
      - category_id: only courses in this category (can combine with q)
      - category: filter by category name (icontains), e.g. ?category=Python
    At least one of q, category_id, or category is required.
    """
    try:
        query = request.GET.get('q', '').strip()
        category_name_filter = request.GET.get('category', '').strip()
        category_id_raw = request.GET.get('category_id')
        category_id = None
        if category_id_raw not in (None, ''):
            try:
                category_id = int(category_id_raw)
            except (ValueError, TypeError):
                return Response(
                    {'status': 'error', 'message': 'category_id must be a number.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not query and category_id is None and not category_name_filter:
            return Response(
                {
                    'status': 'error',
                    'message': 'Provide q (search text) and/or category_id or category (name).',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        courses_qs = Course.objects.filter(is_published=True).select_related(
            'instructor', 'category'
        ).annotate(
            total_students=Count('enrollments', distinct=True),
            avg_rating=Avg('reviews__rating')
        )

        if category_id is not None:
            courses_qs = courses_qs.filter(category_id=category_id)
        if category_name_filter:
            courses_qs = courses_qs.filter(category__name__icontains=category_name_filter)

        if query:
            courses_qs = courses_qs.filter(_course_search_q(query))
            courses_qs = courses_qs.annotate(_search_rank=_udemy_search_rank_case(query)).order_by(
                '_search_rank', '-total_students', '-avg_rating'
            )
        else:
            courses_qs = courses_qs.order_by('-total_students', '-avg_rating')

        courses = courses_qs[:20]

        instructors_data = []
        if query:
            query_tokens = [t for t in query.split() if t]
            instructor_match_q = (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(expertise__icontains=query) |
                Q(username__icontains=query) |
                Q(headline__icontains=query) |
                Q(bio__icontains=query)
            )
            # Better full-name support: "first last" or "last first"
            if len(query_tokens) >= 2:
                first_tok = query_tokens[0]
                last_tok = query_tokens[-1]
                instructor_match_q |= (
                    Q(first_name__icontains=first_tok) & Q(last_name__icontains=last_tok)
                ) | (
                    Q(first_name__icontains=last_tok) & Q(last_name__icontains=first_tok)
                )

            instructors = CustomUser.objects.filter(
                Q(role='instructor') & instructor_match_q
            ).annotate(
                total_courses=Count('course', filter=Q(course__is_published=True), distinct=True),
                total_students_count=Count(
                    'course__enrollments', filter=Q(course__is_published=True), distinct=True
                )
            )[:10]

            for instructor in instructors:
                instructors_data.append({
                    'id': instructor.id,
                    'type': 'instructor',
                    'name': instructor.get_full_name(),
                    'profile_image': (
                        instructor.profile_image.url
                        if (hasattr(instructor, 'profile_image') and instructor.profile_image)
                        else None
                    ),
                    'headline': getattr(instructor, 'headline', ''),
                    'expertise': getattr(instructor, 'expertise', ''),
                    'total_courses': instructor.total_courses,
                    'total_students': instructor.total_students_count,
                })

        matching_categories = []
        if query:
            cats = (
                Category.objects.filter(_category_tokens_q(query))
                .annotate(
                    published_course_count=Count(
                        'courses', filter=Q(courses__is_published=True), distinct=True
                    )
                )
                .order_by('-published_course_count')[:15]
            )
            for cat in cats:
                matching_categories.append({
                    'id': cat.id,
                    'type': 'category',
                    'name': cat.name,
                    'description': (cat.description or '')[:200],
                    'total_courses': cat.published_course_count,
                })

        courses_data = []
        for course in courses:
            courses_data.append({
                'id': course.id,
                'type': 'course',
                'title': course.title,
                'slug': course.slug,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'original_price': str(course.original_price),
                'discounted_price': str(course.discounted_price) if course.discounted_price else None,
                'average_rating': round(float(course.avg_rating or 0), 1),
                'total_students': course.total_students,
                'instructor': {
                    'id': course.instructor.id,
                    'name': course.instructor.get_full_name(),
                    'profile_image': course.instructor.profile_image.url if (
                        hasattr(course.instructor, 'profile_image') and course.instructor.profile_image
                    ) else None,
                },
                'category': {'id': course.category.id, 'name': course.category.name},
            })

        combined_results = courses_data + instructors_data

        return Response({
            'status': 'success',
            'query': query,
            'filters': {
                'category_id': category_id,
                'category': category_name_filter or None,
            },
            'matching_categories': matching_categories,
            'total_matching_categories': len(matching_categories),
            'total_results': len(combined_results),
            'results': combined_results,
        })

    except Exception as e:
        logger.error("Search API Error: %s", e)
        return Response({'status': 'error', 'message': 'Search failed.'}, status=500)
