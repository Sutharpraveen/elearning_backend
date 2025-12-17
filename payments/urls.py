from django.urls import path
from . import views

urlpatterns = [
    # Single course payment
    path('single/create/', views.create_payment, name='single_create_payment'),
    path('single/verify/', views.verify_payment, name='single_verify_payment'),

    # Multi course payment
    path('multi/create/', views.create_multi_payment, name='multi_create_payment'),
    path('multi/verify/', views.verify_multi_payment, name='multi_verify_payment'),
]
