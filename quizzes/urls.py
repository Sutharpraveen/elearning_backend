from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuestionViewSet, QuizAttemptViewSet

router = DefaultRouter()
router.register('quizzes', QuizViewSet, basename='quiz')
router.register('questions', QuestionViewSet, basename='question')
router.register('attempts', QuizAttemptViewSet, basename='quiz-attempt')

urlpatterns = [
    path('', include(router.urls)),
]