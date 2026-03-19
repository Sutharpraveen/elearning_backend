import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import CustomUser
from categories.models import Category

# --- 1. COURSE MODEL ---
class Course(models.Model):
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ]

    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'})
    category = models.ForeignKey(Category, related_name='courses', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    learning_objectives = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    duration = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) # Total hours
    thumbnail = models.ImageField(upload_to='course_thumbnails/')
    intro_video = models.FileField(upload_to='course_videos/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if Course.objects.filter(slug=base_slug).exists():
                self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            else:
                self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def total_lectures_count(self):
        return Lecture.objects.filter(section__course=self).count()

# --- 2. SECTION MODEL ---
class Section(models.Model):
    course = models.ForeignKey(Course, related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# --- 3. LECTURE MODEL ---
class Lecture(models.Model):
    PROCESSING_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    section = models.ForeignKey(Section, related_name='lectures', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Video Files
    video_file = models.FileField(upload_to='lecture_videos/original/', null=True, blank=True)
    video_360p = models.FileField(upload_to='lecture_videos/360p/', null=True, blank=True)
    video_480p = models.FileField(upload_to='lecture_videos/480p/', null=True, blank=True)
    video_720p = models.FileField(upload_to='lecture_videos/720p/', null=True, blank=True)
    video_1080p = models.FileField(upload_to='lecture_videos/1080p/', null=True, blank=True)
    hls_playlist = models.FileField(upload_to='lecture_videos/hls/', null=True, blank=True)
    
    # Metadata
    processing_status = models.CharField(max_length=20, choices=PROCESSING_CHOICES, default='pending')
    duration = models.PositiveIntegerField(default=0) # Seconds
    file_size = models.BigIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

# --- 4. RESOURCE MODEL ---
class Resource(models.Model):
    lecture = models.ForeignKey(Lecture, related_name='resources', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50, blank=True, null=True) # Added for Admin compatibility
    file = models.FileField(upload_to='lecture_resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title

# --- 5. ENROLLMENT MODEL ---
class Enrollment(models.Model):
    user = models.ForeignKey(CustomUser, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    # null=True, blank=True lagaya hai taaki migration error na aaye
    last_accessed = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ['user', 'course']

    @property
    def progress_percentage(self):
        total = self.course.total_lectures_count
        if total == 0: return 0.0
        completed = self.progress.filter(completed=True).count()
        return round((completed / total) * 100, 1)

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

# --- 6. PROGRESS MODEL ---
class Progress(models.Model):
    enrollment = models.ForeignKey(Enrollment, related_name='progress', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_position = models.PositiveIntegerField(default=0) 
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'lecture']

# --- 7. REVIEW MODEL ---
class Review(models.Model):
    course = models.ForeignKey(Course, related_name='reviews', on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ['course', 'student']