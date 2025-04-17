# from django.contrib import admin
# from .models import Wishlist, Cart, CartItem

# @admin.register(Wishlist)
# class WishlistAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'total_courses', 'created_at', 'updated_at']
#     list_filter = ['created_at', 'updated_at']
#     search_fields = ['user__email', 'user__username']
#     date_hierarchy = 'created_at'
    
#     def total_courses(self, obj):
#         return obj.courses.count()
#     total_courses.short_description = 'Total Courses'

#     readonly_fields = ['created_at', 'updated_at']
    
#     fieldsets = [
#         ('User Information', {
#             'fields': ['user']
#         }),
#         ('Courses', {
#             'fields': ['courses']
#         }),
#         ('Timestamps', {
#             'fields': ['created_at', 'updated_at'],
#             'classes': ['collapse']
#         })
#     ]

# @admin.register(CartItem)
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = [
#         'id', 
#         'cart_user',
#         'course_title', 
#         'price_at_time_of_adding',
#         'added_at'
#     ]
#     list_filter = ['added_at', 'cart__user']
#     search_fields = [
#         'cart__user__email',
#         'cart__user__username',
#         'course__title'
#     ]
#     date_hierarchy = 'added_at'
    
#     def cart_user(self, obj):
#         return obj.cart.user.email
#     cart_user.short_description = 'User'
    
#     def course_title(self, obj):
#         return obj.course.title
#     course_title.short_description = 'Course'

#     readonly_fields = ['added_at']
    
#     fieldsets = [
#         ('Cart Information', {
#             'fields': ['cart']
#         }),
#         ('Course Information', {
#             'fields': ['course', 'price_at_time_of_adding']
#         }),
#         ('Timestamps', {
#             'fields': ['added_at'],
#             'classes': ['collapse']
#         })
#     ]

# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = [
#         'id', 
#         'user', 
#         'total_items', 
#         'total_price',
#         'created_at', 
#         'updated_at'
#     ]
#     list_filter = ['created_at', 'updated_at']
#     search_fields = ['user__email', 'user__username']
#     date_hierarchy = 'created_at'
    
#     readonly_fields = ['created_at', 'updated_at', 'total_price', 'total_items']
    
#     def total_price(self, obj):
#         return f"${obj.total_price}"
#     total_price.short_description = 'Total Price'

#     fieldsets = [
#         ('User Information', {
#             'fields': ['user']
#         }),
#         ('Cart Summary', {
#             'fields': ['total_items', 'total_price']
#         }),
#         ('Timestamps', {
#             'fields': ['created_at', 'updated_at'],
#             'classes': ['collapse']
#         })
#     ]

#     def has_add_permission(self, request):
#         return False  # Prevent manual cart creation

#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # Editing an existing object
#             return self.readonly_fields + ['user']
#         return self.readonly_fields

#     inlines = [
#         type('CartItemInline', (admin.TabularInline,), {
#             'model': CartItem,
#             'extra': 0,
#             'readonly_fields': ['added_at'],
#             'fields': ['course', 'price_at_time_of_adding', 'added_at']
#         })
#     ]