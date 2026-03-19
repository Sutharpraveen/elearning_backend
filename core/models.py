from django.db import models
from django.utils import timezone


class SliderImage(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="slider_images/")
    is_active = models.BooleanField(default=False)

    show_from = models.DateTimeField(help_text="When to start showing this banner")
    show_until = models.DateTimeField(null=True, blank=True, help_text="When to stop showing (null = always visible)")

    webinar_time = models.DateTimeField(null=True, blank=True)
    redirect_url = models.URLField(blank=True, null=True)

    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='sliders')
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='sliders')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_currently_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.show_from > now:
            return False
        if self.show_until and self.show_until < now:
            return False
        return True

    class Meta:
        ordering = ['-created_at']


class AppVersion(models.Model):
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]

    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    latest_version = models.CharField(max_length=20)
    force_update = models.BooleanField(default=False, help_text="Block app usage until user updates")
    download_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'App Version'
        verbose_name_plural = 'App Versions'

    def __str__(self):
        return f"{self.platform} - {self.latest_version}"
