import os
import subprocess
import json
import logging
import threading
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Lecture
import shutil

logger = logging.getLogger(__name__)

# Determine paths for local ffmpeg/ffprobe binaries uploaded to the project root, fallback to system
local_ffmpeg = os.path.join(settings.BASE_DIR, 'ffmpeg')
local_ffprobe = os.path.join(settings.BASE_DIR, 'ffprobe')
FFMPEG_CMD = local_ffmpeg if os.path.exists(local_ffmpeg) else (shutil.which('ffmpeg') or 'ffmpeg')
FFPROBE_CMD = local_ffprobe if os.path.exists(local_ffprobe) else (shutil.which('ffprobe') or 'ffprobe')

class UniversalVideoProcessor:
    """
    Universal video processor: Handles any format, creates 360p-1080p MP4s 
    and generates HLS (m3u8) Master Playlist for Adaptive Streaming.
    """

    SUPPORTED_INPUT_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    
    OUTPUT_QUALITIES = {
        '360p': {'height': 360, 'bitrate': '800k', 'audio_bitrate': '96k'},
        '480p': {'height': 480, 'bitrate': '1200k', 'audio_bitrate': '128k'},
        '720p': {'height': 720, 'bitrate': '2500k', 'audio_bitrate': '128k'},
        '1080p': {'height': 1080, 'bitrate': '4500k', 'audio_bitrate': '192k'},
    }

    def __init__(self, lecture):
        self.lecture = lecture
        self.media_root = settings.MEDIA_ROOT
        self.lecture_id = str(lecture.id)
        # Directory setup
        self.output_dir = os.path.join(self.media_root, 'lecture_videos')
        self.hls_base = os.path.join(self.output_dir, 'hls')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.hls_base, exist_ok=True)

    def get_video_info(self, video_path):
        """Get video duration and metadata using ffprobe"""
        try:
            cmd = [
                FFPROBE_CMD, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format'].get('duration', 0))
                size = int(data['format'].get('size', 0))
                return duration, size
        except Exception as e:
            logger.error(f"FFprobe error: {e}")
        return 0, 0

    def create_quality_version(self, input_path, output_path, config):
        """Create a specific quality MP4 version"""
        try:
            cmd = [
                FFMPEG_CMD, '-i', input_path,
                '-vf', f'scale=-2:{config["height"]}',
                '-c:v', 'libx264', '-profile:v', 'main', '-level', '3.1',
                '-b:v', config['bitrate'], '-maxrate', config['bitrate'],
                '-bufsize', f'{int(config["bitrate"].rstrip("k")) * 2}k',
                '-c:a', 'aac', '-b:a', config['audio_bitrate'],
                '-preset', 'medium', '-crf', '23',
                '-movflags', '+faststart', '-f', 'mp4', '-y', output_path
            ]
            # Timeout increased to 30 mins for high-quality renders
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout processing {config['height']}p for lecture {self.lecture_id}")
            return False

    def create_hls_streams(self):
        """Create HLS segments and Master Playlist (.m3u8)"""
        master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n"
        available_qualities = []

        for quality_name, config in self.OUTPUT_QUALITIES.items():
            mp4_path = os.path.join(self.output_dir, f'lecture_{self.lecture_id}_{quality_name}.mp4')

            if os.path.exists(mp4_path):
                hls_dir_name = f'lecture_{self.lecture_id}_{quality_name}'
                hls_dir_path = os.path.join(self.hls_base, hls_dir_name)
                os.makedirs(hls_dir_path, exist_ok=True)

                playlist_name = f'lecture_{self.lecture_id}_{quality_name}.m3u8'
                playlist_path = os.path.join(hls_dir_path, playlist_name)

                cmd = [
                    FFMPEG_CMD, '-i', mp4_path,
                    '-codec:', 'copy', '-start_number', '0',
                    '-hls_time', '10', '-hls_list_size', '0',
                    '-f', 'hls', '-y', playlist_path
                ]

                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=600)
                    if result.returncode == 0:
                        bandwidth = int(config['bitrate'].rstrip('k')) * 1000
                        master_playlist += f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION=-2x{config["height"]},NAME="{quality_name}"\n'
                        master_playlist += f'{hls_dir_name}/{playlist_name}\n'
                        available_qualities.append(quality_name)
                except Exception as e:
                    logger.error(f"HLS segment failed for {quality_name}: {e}")

        if available_qualities:
            master_filename = f'lecture_{self.lecture_id}_master.m3u8'
            master_path = os.path.join(self.hls_base, master_filename)
            with open(master_path, 'w') as f:
                f.write(master_playlist)
            return f'lecture_videos/hls/{master_filename}'
        return None

    def process_video(self):
        """Execute the full processing pipeline"""
        try:
            logger.info(f"Processing started for lecture: {self.lecture_id}")
            
            # Get input file path
            if self.lecture.video_file:
                input_path = self.lecture.video_file.path
            else:
                logger.error("No video file found in lecture object")
                return False

            # 1. Update status to 'processing'
            duration, file_size = self.get_video_info(input_path)
            self.lecture.duration = int(duration)
            self.lecture.file_size = file_size
            self.lecture.processing_status = 'processing'
            self.lecture.save()

            processed_qualities = []
            
            # 2. Generate MP4 Qualities
            for quality_name, config in self.OUTPUT_QUALITIES.items():
                output_filename = f'lecture_{self.lecture_id}_{quality_name}.mp4'
                output_path = os.path.join(self.output_dir, output_filename)
                
                if self.create_quality_version(input_path, output_path, config):
                    # Link to model fields
                    field_name = f'video_{quality_name.lower()}'
                    if hasattr(self.lecture, field_name):
                        setattr(self.lecture, field_name, f'lecture_videos/{output_filename}')
                    processed_qualities.append(quality_name)

            if not processed_qualities:
                raise Exception("Failed to generate any quality versions")

            # 3. Generate HLS Playlist
            hls_path = self.create_hls_streams()
            if hls_path:
                self.lecture.hls_playlist = hls_path

            # 4. Finish
            self.lecture.processing_status = 'completed'
            self.lecture.save()
            logger.info(f"Processing completed for {self.lecture_id}. Qualities: {processed_qualities}")
            return True

        except Exception as e:
            logger.exception(f"Fatal error in video processing: {e}")
            self.lecture.processing_status = 'failed'
            self.lecture.save()
            return False

def process_lecture_video_universal(lecture_id):
    """Wrapper function to be called from a background thread"""
    try:
        lecture = Lecture.objects.get(id=lecture_id)
        processor = UniversalVideoProcessor(lecture)
        return processor.process_video()
    except Exception as e:
        logger.error(f"Wrapper error: {e}")
        return False