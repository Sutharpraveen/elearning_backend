from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Quiz, Question, QuizAttempt
from .serializers import QuizSerializer, QuestionSerializer, QuizAttemptSerializer
from courses.models import Course, Enrollment


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(course__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id, instructor=self.request.user)
        serializer.save(course=course)

    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        """Start a quiz attempt"""
        quiz = self.get_object()
        user = request.user

        # Check if user is enrolled in the course
        if not Enrollment.objects.filter(user=user, course=quiz.course).exists():
            return Response(
                {'error': 'You must be enrolled in the course to take this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user already has an incomplete attempt
        existing_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=user,
            completed=False
        ).first()

        if existing_attempt:
            serializer = QuizAttemptSerializer(existing_attempt)
            return Response({
                'message': 'Continuing existing attempt',
                'attempt': serializer.data
            })

        # Create new attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=user
        )

        serializer = QuizAttemptSerializer(attempt)
        return Response({
            'message': 'Quiz attempt started',
            'attempt': serializer.data
        })


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(quiz__course__instructor=self.request.user)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit answer for a question"""
        attempt = self.get_object()
        question_id = request.data.get('question_id')
        selected_option = request.data.get('selected_option')

        if not question_id or selected_option is None:
            return Response(
                {'error': 'question_id and selected_option are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if attempt is still active
        if attempt.completed:
            return Response(
                {'error': 'This quiz attempt is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the question
        try:
            question = Question.objects.get(id=question_id, quiz=attempt.quiz)
        except Question.DoesNotExist:
            return Response(
                {'error': 'Question not found in this quiz'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Store the answer
        if not hasattr(attempt, 'answers'):
            attempt.answers = {}

        attempt.answers[str(question_id)] = {
            'selected_option': selected_option,
            'is_correct': selected_option == question.correct_option
        }
        attempt.save()

        return Response({'message': 'Answer submitted successfully'})

    @action(detail=True, methods=['post'])
    def complete_attempt(self, request, pk=None):
        """Complete the quiz attempt and calculate score"""
        attempt = self.get_object()

        if attempt.completed:
            return Response(
                {'error': 'This quiz attempt is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate score
        total_questions = attempt.quiz.questions.count()
        correct_answers = 0

        if hasattr(attempt, 'answers') and attempt.answers:
            for question_id, answer_data in attempt.answers.items():
                if answer_data.get('is_correct', False):
                    correct_answers += 1

        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        # Update attempt
        attempt.completed = True
        attempt.score = score_percentage
        attempt.save()

        return Response({
            'message': 'Quiz completed successfully',
            'score': score_percentage,
            'correct_answers': correct_answers,
            'total_questions': total_questions
        })