import os
import subprocess
import json
from pathlib import Path
from django.conf import settings
from .models import Lecture

class VideoProcessor:
    """Video processing utility for transcoding and HLS generation"""

    # Video quality configurations
    QUALITIES = {
        '1080p': {'resolution': '1920x1080', 'bitrate': '5000k', 'audio_bitrate': '192k'},
        '720p': {'resolution': '1280x720', 'bitrate': '3000k', 'audio_bitrate': '128k'},
        '480p': {'resolution': '854x480', 'bitrate': '1500k', 'audio_bitrate': '128k'},
        '360p': {'resolution': '640x360', 'bitrate': '1000k', 'audio_bitrate': '96k'},
    }

    def __init__(self, lecture):
        self.lecture = lecture
        self.media_root = settings.MEDIA_ROOT
        self.lecture_id = str(lecture.id)

    def get_video_path(self, quality=None):
        """Get the file path for a specific quality or original video"""
        if quality:
            filename = f"lecture_{self.lecture_id}_{quality}.mp4"
            return os.path.join(self.media_root, 'lecture_videos', quality, filename)
        else:
            # Original video path
            if self.lecture.original_video:
                return os.path.join(self.media_root, self.lecture.original_video.name)
        return None

    def get_hls_path(self):
        """Get HLS playlist path"""
        filename = f"lecture_{self.lecture_id}_playlist.m3u8"
        return os.path.join(self.media_root, 'lecture_videos', 'hls', filename)

    def ensure_directories(self):
        """Create necessary directories for video storage"""
        directories = [
            os.path.join(self.media_root, 'lecture_videos', 'original'),
            os.path.join(self.media_root, 'lecture_videos', 'hls'),
            os.path.join(self.media_root, 'lecture_videos', '1080p'),
            os.path.join(self.media_root, 'lecture_videos', '720p'),
            os.path.join(self.media_root, 'lecture_videos', '480p'),
            os.path.join(self.media_root, 'lecture_videos', '360p'),
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def get_video_info(self, video_path):
        """Get video duration and metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                size = int(data['format']['size'])
                return duration, size
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            pass

        return 0, 0

    def transcode_video(self, input_path, output_path, quality_config):
        """Transcode video to specific quality using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,  # Input file
                '-vf', f'scale={quality_config["resolution"]}',  # Video filter for resolution
                '-b:v', quality_config['bitrate'],  # Video bitrate
                '-b:a', quality_config['audio_bitrate'],  # Audio bitrate
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-preset', 'medium',  # Encoding preset
                '-crf', '23',  # Constant Rate Factor
                '-maxrate', quality_config['bitrate'],
                '-bufsize', f'{int(quality_config["bitrate"].rstrip("k")) * 2}k',
                '-f', 'mp4',  # Output format
                '-y',  # Overwrite output files
                output_path  # Output file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            return False

    def generate_hls_playlist(self):
        """Generate HLS master playlist with multiple qualities"""
        hls_path = self.get_hls_path()
        hls_dir = os.path.dirname(hls_path)

        # Create master playlist
        master_playlist = "#EXTM3U\n#EXT-X-VERSION:6\n"

        available_qualities = []
        for quality, config in self.QUALITIES.items():
            video_path = self.get_video_path(quality)
            if os.path.exists(video_path):
                # Create segmented HLS for this quality
                quality_playlist_path = self._create_segmented_hls(video_path, quality, config)
                if quality_playlist_path:
                    available_qualities.append((quality, config, quality_playlist_path))

        if not available_qualities:
            # If no qualities available, use original video for basic HLS
            original_path = self.get_video_path()
            if os.path.exists(original_path):
                quality_playlist_path = self._create_basic_hls(original_path)
                if quality_playlist_path:
                    # Create a single quality entry
                    config = self.QUALITIES['720p']  # Default config
                    available_qualities.append(('original', config, quality_playlist_path))

        if not available_qualities:
            return False

        # Add quality entries to master playlist (sorted by bandwidth, highest first)
        available_qualities.sort(key=lambda x: self._get_bandwidth(x[1]['bitrate']), reverse=True)

        for quality, config, quality_playlist_path in available_qualities:
            bandwidth = self._get_bandwidth(config['bitrate'])
            resolution = config['resolution']
            quality_name = quality if quality != 'original' else 'Auto'
            playlist_filename = os.path.basename(quality_playlist_path)

            master_playlist += f'#EXT-X-STREAM-INF:'
            master_playlist += f'BANDWIDTH={bandwidth},'
            master_playlist += f'RESOLUTION={resolution},'
            master_playlist += f'NAME="{quality_name}"\n'
            master_playlist += f'{playlist_filename}\n'

        # Write master playlist
        with open(hls_path, 'w') as f:
            f.write(master_playlist)

        return True

    def _create_segmented_hls(self, video_path, quality, config):
        """Create segmented HLS stream for a specific quality"""
        if not os.path.exists(video_path):
            return None

        try:
            # Create output directory for segments
            segments_dir = os.path.join(self.media_root, 'lecture_videos', 'hls', f'lecture_{self.lecture_id}_{quality}')
            Path(segments_dir).mkdir(parents=True, exist_ok=True)

            # HLS segment filename pattern
            segment_pattern = os.path.join(segments_dir, 'segment_%03d.ts')
            playlist_path = os.path.join(segments_dir, f'lecture_{self.lecture_id}_{quality}.m3u8')

            # ffmpeg command for HLS segmentation
            cmd = [
                'ffmpeg',
                '-i', video_path,  # Input video
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-b:v', config['bitrate'],  # Video bitrate
                '-b:a', config['audio_bitrate'],  # Audio bitrate
                '-vf', f'scale={config["resolution"]}',  # Resolution
                '-hls_time', '10',  # Segment duration (10 seconds)
                '-hls_list_size', '0',  # Keep all segments in playlist
                '-hls_segment_filename', segment_pattern,  # Segment filename pattern
                '-f', 'hls',  # Output format
                '-y',  # Overwrite
                playlist_path  # Output playlist
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                # Return relative path for the playlist
                return f'lecture_videos/hls/lecture_{self.lecture_id}_{quality}/lecture_{self.lecture_id}_{quality}.m3u8'

        except subprocess.TimeoutExpired:
            pass

        return None

    def _get_bandwidth(self, bitrate_str):
        """Convert bitrate string to bandwidth integer"""
        if bitrate_str.endswith('k'):
            return int(bitrate_str.rstrip('k')) * 1000
        elif bitrate_str.endswith('M'):
            return int(float(bitrate_str.rstrip('M'))) * 1000000
        return int(bitrate_str)

    def process_video(self):
        """Main method to process uploaded video"""
        try:
            self.ensure_directories()

            # Get original video path
            input_path = self.get_video_path()
            if not input_path or not os.path.exists(input_path):
                return False

            # Update processing status
            self.lecture.processing_status = 'processing'
            self.lecture.save()

            # Get video info
            duration, file_size = self.get_video_info(input_path)
            self.lecture.duration = int(duration)
            self.lecture.file_size = file_size

            # Transcode to different qualities
            transcoded_qualities = []
            for quality, config in self.QUALITIES.items():
                output_path = self.get_video_path(quality)
                if self.transcode_video(input_path, output_path, config):
                    transcoded_qualities.append(quality)

            # Generate HLS playlist
            hls_generated = self.generate_hls_playlist()

            # Update lecture with processed video paths
            if '1080p' in transcoded_qualities:
                self.lecture.video_1080p = f'lecture_videos/1080p/lecture_{self.lecture_id}_1080p.mp4'
            if '720p' in transcoded_qualities:
                self.lecture.video_720p = f'lecture_videos/720p/lecture_{self.lecture_id}_720p.mp4'
            if '480p' in transcoded_qualities:
                self.lecture.video_480p = f'lecture_videos/480p/lecture_{self.lecture_id}_480p.mp4'
            if '360p' in transcoded_qualities:
                self.lecture.video_360p = f'lecture_videos/360p/lecture_{self.lecture_id}_360p.mp4'

            if hls_generated:
                self.lecture.hls_playlist = f'lecture_videos/hls/lecture_{self.lecture_id}_playlist.m3u8'

            self.lecture.processing_status = 'completed'
            self.lecture.save()

            return True

        except Exception as e:
            print(f"Video processing error: {str(e)}")
            self.lecture.processing_status = 'failed'
            self.lecture.save()
            return False

    def _create_basic_hls(self, video_path):
        """Create basic HLS from original video (fallback)"""
        try:
            # Create output directory for segments
            segments_dir = os.path.join(self.media_root, 'lecture_videos', 'hls', f'lecture_{self.lecture_id}_basic')
            Path(segments_dir).mkdir(parents=True, exist_ok=True)

            # HLS segment filename pattern
            segment_pattern = os.path.join(segments_dir, 'segment_%03d.ts')
            playlist_path = os.path.join(segments_dir, f'lecture_{self.lecture_id}_basic.m3u8')

            # ffmpeg command for basic HLS segmentation (no transcoding, just segmentation)
            cmd = [
                'ffmpeg',
                '-i', video_path,  # Input video
                '-c', 'copy',  # Copy streams without re-encoding
                '-hls_time', '10',  # Segment duration (10 seconds)
                '-hls_list_size', '0',  # Keep all segments in playlist
                '-hls_segment_filename', segment_pattern,  # Segment filename pattern
                '-f', 'hls',  # Output format
                '-y',  # Overwrite
                playlist_path  # Output playlist
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                # Return relative path for the playlist
                return f'lecture_videos/hls/lecture_{self.lecture_id}_basic/lecture_{self.lecture_id}_basic.m3u8'

        except subprocess.TimeoutExpired:
            pass

        return None

def process_lecture_video(lecture_id):
    """Background task to process video for a lecture"""
    try:
        lecture = Lecture.objects.get(id=lecture_id)
        processor = VideoProcessor(lecture)
        return processor.process_video()
    except Lecture.DoesNotExist:
        return False