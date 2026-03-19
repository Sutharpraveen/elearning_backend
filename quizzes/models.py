from django.db import models
from django.conf import settings
from courses.models import Course


class Quiz(models.Model):
    QUIZ_TYPES = [
        ('practice', 'Practice Quiz'),
        ('assessment', 'Assessment Quiz'),
        ('final', 'Final Exam'),
    ]

    course = models.ForeignKey(Course, related_name='quizzes', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default='practice')
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes", null=True, blank=True)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    max_attempts = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    class Meta:
        ordering = ['created_at']


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')

    # For multiple choice questions
    option_a = models.CharField(max_length=255, blank=True)
    option_b = models.CharField(max_length=255, blank=True)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)

    # Correct answer
    correct_option = models.CharField(max_length=10, blank=True)  # 'a', 'b', 'c', 'd', 'true', 'false'
    correct_answer_text = models.TextField(blank=True)  # For short answer questions

    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question {self.order}: {self.question_text[:50]}..."

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='attempts', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='quiz_attempts', on_delete=models.CASCADE)
    answers = models.JSONField(default=dict, blank=True)  # Store answers as JSON
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"

    class Meta:
        ordering = ['-started_at']