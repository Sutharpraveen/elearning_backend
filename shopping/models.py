from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

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
        return sum(item.price_at_time_of_adding for item in self.items.filter(is_saved_for_later=False)) or Decimal('0')

    @property
    def item_discount_amount(self):
        """Discount from individual item prices"""
        return sum(item.savings for item in self.items.filter(is_saved_for_later=False)) or Decimal('0')

    @property
    def coupon_discount_amount(self):
        """Discount from coupon"""
        if self.coupon_code and self.coupon_discount > 0:
            try:
                coupon = Coupon.objects.get(code=self.coupon_code)
                discount_amount = (Decimal(str(self.subtotal)) * Decimal(str(self.coupon_discount))) / Decimal('100')
                # Apply maximum discount limit if set
                if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
                    return coupon.max_discount_amount
                return discount_amount
            except Coupon.DoesNotExist:
                return Decimal('0')
        return Decimal('0')

    @property
    def total_discount_amount(self):
        """Total discount including item and coupon discounts"""
        return Decimal(str(self.item_discount_amount)) + Decimal(str(self.coupon_discount_amount))

    @property
    def total_price(self):
        return Decimal(str(self.subtotal)) - Decimal(str(self.coupon_discount_amount))

    @property
    def total_items(self):
        return self.items.filter(is_saved_for_later=False).count()

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

class AppVersion(models.Model):
    version = models.CharField(max_length=50)
    platform = models.CharField(max_length=20, choices=[
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web')
    ])
    is_force_update = models.BooleanField(default=False)
    release_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} v{self.version}"