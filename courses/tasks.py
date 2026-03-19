import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task

    @shared_task(bind=True, max_retries=2, default_retry_delay=60)
    def process_lecture_video_task(self, lecture_id):
        """Celery task for processing lecture videos in the background."""
        try:
            from .video_utils import process_lecture_video_universal
            result = process_lecture_video_universal(lecture_id)
            if result:
                logger.info("Video processing completed for lecture %s", lecture_id)
            else:
                logger.error("Video processing failed for lecture %s", lecture_id)
            return result
        except Exception as exc:
            logger.exception("Video processing error for lecture %s: %s", lecture_id, exc)
            raise self.retry(exc=exc)

except ImportError:
    import threading

    class _FakeDelayable:
        """Fallback that uses threading when Celery is not installed."""
        def __init__(self, func):
            self._func = func

        def delay(self, *args, **kwargs):
            thread = threading.Thread(target=self._func, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            return thread

    def _process_lecture_video_sync(lecture_id):
        try:
            from .video_utils import process_lecture_video_universal
            result = process_lecture_video_universal(lecture_id)
            if result:
                logger.info("Video processing completed for lecture %s", lecture_id)
            else:
                logger.error("Video processing failed for lecture %s", lecture_id)
        except Exception:
            logger.exception("Video processing error for lecture %s", lecture_id)

    process_lecture_video_task = _FakeDelayable(_process_lecture_video_sync)
