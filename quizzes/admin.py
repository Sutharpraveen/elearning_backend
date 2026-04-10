from django.contrib import admin
from .models import Quiz, Question, QuizAttempt


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'quiz_type', 'passing_score', 'max_attempts', 'is_active', 'created_at']
    list_filter = ['quiz_type', 'is_active', 'course']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz__course']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'completed', 'started_at', 'completed_at']
    list_filter = ['completed', 'quiz__course']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at', 'answers']
    ordering = ['-started_at']
