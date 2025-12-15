from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course
from django.utils import timezone
from django.conf import settings

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




class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    users_used = models.ManyToManyField(User, blank=True, related_name='used_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% off"

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            self.used_count < self.usage_limit
        )

    class Meta:
        ordering = ['-created_at']


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def subtotal(self):
        return sum(item.price_at_time_of_adding for item in self.items.all())

    @property
    def item_discount_amount(self):
        """Discount from individual item prices"""
        return sum(item.savings for item in self.items.all())

    @property
    def coupon_discount_amount(self):
        """Discount from coupon"""
        if self.coupon_code and self.coupon_discount > 0:
            return (self.subtotal * self.coupon_discount) / 100
        return 0

    @property
    def total_discount_amount(self):
        """Total discount including item and coupon discounts"""
        return self.item_discount_amount + self.coupon_discount_amount

    @property
    def total_price(self):
        return self.subtotal - self.total_discount_amount

    @property
    def total_items(self):
        return self.items.count()

    class Meta:
        ordering = ['-created_at']

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    price_at_time_of_adding = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    is_saved_for_later = models.BooleanField(default=False)
    savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'course')

    def __str__(self):
        return f"{self.course.title} in {self.cart.user.username}'s cart"

    def save(self, *args, **kwargs):
        if not self.savings:
            self.savings = self.original_price - self.price_at_time_of_adding
        super().save(*args, **kwargs)