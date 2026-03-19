from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chapter, ChapterSection
from .serializers import ChapterSerializer
from courses.models import Course


class ChapterViewSet(viewsets.ModelViewSet):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(course__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id, instructor=self.request.user)
        serializer.save(course=course)

    @action(detail=True, methods=['post'])
    def reorder_sections(self, request, pk=None):
        """Reorder sections within a chapter"""
        chapter = self.get_object()
        section_orders = request.data.get('section_orders', [])

        if not isinstance(section_orders, list):
            return Response(
                {'error': 'section_orders must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update section orders (ChapterSection links Chapter to Section)
        for order_data in section_orders:
            section_id = order_data.get('section_id')
            new_order = order_data.get('order')
            if section_id is None or new_order is None:
                continue
            try:
                ch_sec = chapter.chapter_sections.get(section_id=section_id)
                ch_sec.order = new_order
                ch_sec.save()
            except (ValueError, ChapterSection.DoesNotExist):
                continue

        return Response({'message': 'Sections reordered successfully'})

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get chapter analytics"""
        chapter = self.get_object()

        # Calculate basic analytics (Chapter has chapter_sections -> Section)
        total_sections = chapter.chapter_sections.count()
        total_lectures = sum(cs.section.lectures.count() for cs in chapter.chapter_sections.select_related('section'))

        # Calculate completion rates (simplified)
        completion_data = {
            'chapter_id': chapter.id,
            'chapter_title': chapter.title,
            'total_sections': total_sections,
            'total_lectures': total_lectures,
            'completion_rate': 0,  # Would need more complex logic
        }

        return Response(completion_data)