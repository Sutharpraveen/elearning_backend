from django.core.management.base import BaseCommand
from courses.models import Lecture
from courses.video_utils import process_lecture_video

class Command(BaseCommand):
    help = 'Process videos for lectures that are pending or failed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lecture-id',
            type=int,
            help='Process video for specific lecture ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all pending/failed videos',
        )

    def handle(self, *args, **options):
        if options['lecture_id']:
            # Process specific lecture
            try:
                lecture = Lecture.objects.get(id=options['lecture_id'])
                self.stdout.write(f'Processing video for lecture: {lecture.title}')

                if process_lecture_video(lecture.id):
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully processed video for lecture {lecture.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to process video for lecture {lecture.id}')
                    )
            except Lecture.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Lecture with ID {options["lecture_id"]} does not exist')
                )

        elif options['all']:
            # Process all pending/failed videos
            lectures = Lecture.objects.filter(
                processing_status__in=['pending', 'failed']
            ).exclude(original_video='')

            if not lectures:
                self.stdout.write('No videos to process')
                return

            self.stdout.write(f'Found {lectures.count()} videos to process')

            success_count = 0
            fail_count = 0

            for lecture in lectures:
                self.stdout.write(f'Processing: {lecture.title} (ID: {lecture.id})')

                if process_lecture_video(lecture.id):
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Processed: {lecture.title}')
                    )
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed: {lecture.title}')
                    )

            self.stdout.write(
                self.style.SUCCESS(f'Completed: {success_count} successful, {fail_count} failed')
            )

        else:
            self.stdout.write(
                self.style.WARNING('Please specify --lecture-id or --all')
            )

