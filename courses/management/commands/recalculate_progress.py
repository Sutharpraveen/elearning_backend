from django.core.management.base import BaseCommand
from courses.models import Enrollment, Progress
from django.utils import timezone


class Command(BaseCommand):
    help = 'Recalculate progress percentages for all enrollments based on actual time watched'

    def handle(self, *args, **options):
        enrollments = Enrollment.objects.all()
        updated_count = 0

        self.stdout.write(f'Starting progress recalculation for {enrollments.count()} enrollments...')

        for enrollment in enrollments:
            # Calculate total course duration and watched time
            progress_records = enrollment.progress.all()
            total_duration = 0
            watched_duration = 0

            for progress in progress_records:
                lecture = progress.lecture
                total_duration += lecture.duration

                if progress.completed:
                    watched_duration += lecture.duration
                else:
                    # Partial progress - use actual watched time
                    watched_time = min(progress.last_position / 60, lecture.duration)
                    watched_duration += watched_time

            # Calculate correct progress percentage
            if total_duration > 0:
                correct_progress = min((watched_duration / total_duration) * 100, 100.0)
            else:
                correct_progress = 0.0

            # Round to 1 decimal place
            correct_progress = round(correct_progress, 1)

            # Update if different
            if abs(enrollment.progress_percentage - correct_progress) > 0.1:
                old_progress = enrollment.progress_percentage
                enrollment.progress_percentage = correct_progress

                # Mark as completed if 100%
                if correct_progress >= 100 and not enrollment.completed:
                    enrollment.completed = True
                    enrollment.completed_at = timezone.now()

                enrollment.save()
                updated_count += 1

                self.stdout.write(
                    f'Updated {enrollment.user.email} - {enrollment.course.title}: '
                    f'{old_progress}% → {correct_progress}%'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Progress recalculation completed. Updated {updated_count} enrollments.'
            )
        )



