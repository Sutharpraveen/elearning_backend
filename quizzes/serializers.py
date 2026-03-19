from rest_framework import serializers
from .models import Quiz, Question, QuizAttempt


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'quiz', 'question_text', 'question_type',
            'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'correct_answer_text', 'points',
            'order', 'created_at'
        ]
        read_only_fields = ['created_at']


class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'course_title', 'title', 'description',
            'quiz_type', 'time_limit', 'passing_score', 'max_attempts',
            'questions_count', 'total_points', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(question.points for question in obj.questions.all())


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    total_questions = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'user', 'user_name',
            'answers', 'score', 'completed', 'total_questions',
            'correct_answers', 'started_at', 'completed_at'
        ]
        read_only_fields = ['score', 'completed', 'started_at', 'completed_at']

    def get_total_questions(self, obj):
        return obj.quiz.questions.count()

    def get_correct_answers(self, obj):
        if not hasattr(obj, 'answers') or not obj.answers:
            return 0

        correct_count = 0
        for question_id, answer_data in obj.answers.items():
            if answer_data.get('is_correct', False):
                correct_count += 1

        return correct_count