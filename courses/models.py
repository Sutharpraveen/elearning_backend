from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from categories.models import Category


class Course(models.Model):
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ]

    instructor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'instructor'}
    )
    category = models.ForeignKey(Category, related_name='courses', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    learning_objectives = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='Beginner'
    )
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    duration = models.DecimalField(max_digits=5, decimal_places=2)
    thumbnail = models.ImageField(upload_to='course_thumbnails/')
    intro_video = models.FileField(upload_to='course_videos/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Section(models.Model):
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - Section {self.order}: {self.title}"

class Lecture(models.Model):
    section = models.ForeignKey(Section, related_name='lectures', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to='lecture_videos/')
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    is_preview = models.BooleanField(default=False)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['section', 'order']

    def __str__(self):
        return f"{self.section.course.title} - Lecture {self.order}: {self.title}"

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('zip', 'ZIP File'),
        ('link', 'External Link'),
        ('other', 'Other')
    ]

    lecture = models.ForeignKey(Lecture, related_name='resources', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='course_resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lecture.title} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"

class Progress(models.Model):
    enrollment = models.ForeignKey(Enrollment, related_name='progress', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='progress', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_position = models.PositiveIntegerField(default=0, help_text="Last video position in seconds")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'lecture']

    def __str__(self):
        return f"{self.enrollment.student.email} - {self.lecture.title}"

class Review(models.Model):
    course = models.ForeignKey(Course, related_name='reviews', on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['course', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email}'s review for {self.course.title}"
