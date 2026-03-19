from django.db import models
from courses.models import Course, Section


class Chapter(models.Model):
    course = models.ForeignKey(Course, related_name='chapters', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    class Meta:
        ordering = ['order']

    @property
    def sections_count(self):
        """Get total number of sections in this chapter"""
        return self.sections.count()

    @property
    def lectures_count(self):
        """Get total number of lectures in this chapter"""
        return sum(section.lectures.count() for section in self.sections.all())

    @property
    def total_duration(self):
        """Get total duration of all lectures in this chapter"""
        total_seconds = sum(
            lecture.duration for section in self.sections.all()
            for lecture in section.lectures.all()
        )
        return total_seconds


class ChapterSection(models.Model):
    """Intermediate model to link sections to chapters"""
    chapter = models.ForeignKey(Chapter, related_name='chapter_sections', on_delete=models.CASCADE)
    section = models.OneToOneField(Section, related_name='chapter_section', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chapter.title} - {self.section.title}"

    class Meta:
        ordering = ['order']
        unique_together = ['chapter', 'section']