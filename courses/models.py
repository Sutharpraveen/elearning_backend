from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Course(models.Model):
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('All Levels', 'All Levels'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('unpublished', 'Unpublished'),
    ]

    instructor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'instructor'},
        related_name='courses'
    )
    category = models.ForeignKey(
        Category, 
        related_name='courses', 
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    learning_objectives = models.JSONField(default=list)  # Store as ["objective1", "objective2", ...]
    requirements = models.JSONField(default=list)  # Store as ["requirement1", "requirement2", ...]
    
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='Beginner'
    )
    
    # Price fields
    original_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discounted_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    language = models.CharField(max_length=50, default='English')
    duration = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Total course duration in hours"
    )
    
    # Media fields
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        help_text="Course thumbnail image (16:9 ratio recommended)"
    )
    promotional_video = models.FileField(
        upload_to='course_promos/',
        null=True,
        blank=True,
        help_text="Short promotional video for the course"
    )
    
    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_featured = models.BooleanField(default=False)
    
    # Statistics
    total_students = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['instructor']),
            models.Index(fields=['category']),
            models.Index(fields=['language']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Ensure discounted price is not greater than original price
        if self.discounted_price and self.discounted_price > self.original_price:
            self.discounted_price = self.original_price
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Returns the current active price (discounted if available, otherwise original)"""
        return self.discounted_price if self.discounted_price else self.original_price

    @property
    def discount_percentage(self):
        """Calculate discount percentage if discounted price is set"""
        if self.discounted_price:
            discount = ((self.original_price - self.discounted_price) / self.original_price) * 100
            return round(discount, 2)
        return 0