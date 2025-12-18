from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Create the main router
router = DefaultRouter()
router.register(r'templates', views.CertificateTemplateViewSet, basename='certificate-template')
router.register(r'', views.CertificateViewSet, basename='certificate')

# Additional URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('verify/', views.verify_certificate, name='verify-certificate'),
    path('verify/<uuid:certificate_id>/', views.certificate_verification_page, name='certificate-verification-page'),
    path('auto-generate/', views.auto_generate_certificates, name='auto-generate-certificates'),
]
