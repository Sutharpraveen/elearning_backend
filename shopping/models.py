from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course

User = get_user_model()

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    courses = models.ManyToManyField(Course, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.email}"

    class Meta:
        ordering = ['-created_at']

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    courses = models.ManyToManyField(Course, through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total_price(self):
        return sum(item.price_at_time_of_adding for item in self.cart_items.all())

    @property
    def total_items(self):
        return self.cart_items.count()

    class Meta:
        ordering = ['-created_at']

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    price_at_time_of_adding = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'course')
        ordering = ['-added_at']

    def save(self, *args, **kwargs):
        if not self.price_at_time_of_adding:
            self.price_at_time_of_adding = self.course.price
        super().save(*args, **kwargs)