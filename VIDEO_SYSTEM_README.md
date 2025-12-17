# Video Streaming System - Udemy Style

## Overview
This system provides automatic video processing with adaptive bitrate streaming (HLS) similar to Udemy and YouTube. Users get a single URL that automatically adapts quality based on their device and network conditions.

## How It Works

### 1. Video Upload
- Instructor uploads MP4 video to `original_video` field
- System automatically starts background processing

### 2. Automatic Transcoding
Creates multiple quality versions:
- **1080p**: 1920x1080 (5 Mbps) - High quality
- **720p**: 1280x720 (3 Mbps) - HD quality
- **480p**: 854x480 (1.5 Mbps) - Standard quality
- **360p**: 640x360 (1 Mbps) - Mobile quality

### 3. HLS Generation
- Creates segmented video files (.ts)
- Generates HLS playlists (.m3u8)
- Provides adaptive streaming

### 4. API Response
Users get a single primary URL:
```json
{
  "video_urls": {
    "primary_url": "https://domain.com/media/lecture_videos/hls/lecture_123_playlist.m3u8",
    "stream_type": "hls",
    "available_qualities": ["1080p", "720p", "480p", "360p"]
  }
}
```

## Technical Details

### Video Processing Flow
```
MP4 Upload → Background Processing → Multi-Quality Transcoding → HLS Segmentation → Master Playlist
```

### Directory Structure
```
lecture_videos/
├── original/           # Uploaded MP4 files
├── 1080p/             # Transcoded 1080p MP4
├── 720p/              # Transcoded 720p MP4
├── 480p/              # Transcoded 480p MP4
├── 360p/              # Transcoded 360p MP4
└── hls/               # HLS playlists and segments
    ├── lecture_123_playlist.m3u8    # Master playlist
    ├── lecture_123_1080p/
    │   ├── lecture_123_1080p.m3u8  # Quality playlist
    │   ├── segment_001.ts          # Video segments
    │   ├── segment_002.ts
    │   └── ...
    └── ...
```

### HLS Master Playlist
```m3u8
#EXTM3U
#EXT-X-VERSION:6
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,NAME="1080p"
lecture_123_1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720,NAME="720p"
lecture_123_720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=854x480,NAME="480p"
lecture_123_480p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=640x360,NAME="360p"
lecture_123_360p.m3u8
```

## Frontend Integration

### Using HLS.js (Recommended)
```javascript
const video = document.getElementById('video');

if (Hls.isSupported()) {
  const hls = new Hls();
  hls.loadSource(primaryUrl);  // Single HLS URL
  hls.attachMedia(video);

  hls.on(Hls.Events.MANIFEST_PARSED, function() {
    video.play(); // Auto quality switching
  });
}
```

### Features
- **Automatic Quality Selection**: Based on bandwidth and device
- **Seamless Switching**: No buffering during quality changes
- **Wide Compatibility**: Works on all devices and browsers
- **Quality Controls**: Manual quality selection option

## API Endpoints

### Get Lecture Content
```
GET /api/courses/{course_id}/sections/{section_id}/lectures/{lecture_id}/
```

**Response:**
```json
{
  "id": 123,
  "title": "Python Basics",
  "processing_status": "completed",
  "video_urls": {
    "primary_url": "https://domain.com/media/lecture_videos/hls/lecture_123_playlist.m3u8",
    "stream_type": "hls",
    "available_qualities": ["1080p", "720p", "480p", "360p"]
  },
  "duration": 1800,
  "file_size": 52428800
}
```

## Management Commands

### Process Videos Manually
```bash
# Process specific lecture
python manage.py process_videos --lecture-id 123

# Process all pending videos
python manage.py process_videos --all
```

## Requirements

### System Dependencies
```bash
# Install ffmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

### Python Dependencies
```
ffmpeg-python==0.2.0
```

## Benefits

### For Users
- **Single URL**: No quality selection needed
- **Adaptive Streaming**: Automatic quality adjustment
- **Fast Loading**: Optimal quality for connection
- **Cross-Device**: Works on mobile, tablet, desktop

### For Platform
- **Bandwidth Efficient**: Serves appropriate quality
- **Scalable**: CDN-friendly segmented delivery
- **Professional**: Industry-standard video delivery
- **Reliable**: Fallback options if HLS fails

## Udemy Comparison

| Feature | Your Platform | Udemy |
|---------|---------------|-------|
| Single URL | ✅ | ✅ |
| Auto Quality | ✅ | ✅ |
| HLS Streaming | ✅ | ✅ |
| Mobile Support | ✅ | ✅ |
| Quality Options | ✅ | ✅ |
| CDN Ready | ✅ | ✅ |

## Next Steps

1. **CDN Integration**: Use CloudFront/AWS S3 for video delivery
2. **Thumbnail Generation**: Auto-generate video thumbnails
3. **Progress Sync**: Sync video progress across devices
4. **Analytics**: Video engagement metrics
5. **Subtitles**: Multi-language subtitle support

---

**Result**: Your video system now works exactly like Udemy - users get one URL, system handles everything automatically! 🎥✨


