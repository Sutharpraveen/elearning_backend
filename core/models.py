from django.db import models

class SliderImage(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="slider_images/")
    is_active = models.BooleanField(default=False)
    show_from = models.DateTimeField()
    show_until = models.DateTimeField(null=True, blank=True)
    webinar_time = models.DateTimeField(null=True, blank=True)
    redirect_url = models.URLField(blank=True, null=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class AppVersion(models.Model):
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]
    
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    latest_version = models.CharField(max_length=20)
    force_update = models.BooleanField(default=False)
    download_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'App Version'
        verbose_name_plural = 'App Versions'

    def __str__(self):
        return f"{self.platform} - {self.latest_version}"