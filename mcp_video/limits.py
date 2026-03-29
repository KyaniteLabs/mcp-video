"""Resource limits and validation constants for mcp-video."""

# Video limits
MAX_VIDEO_DURATION = 14400       # 4 hours in seconds
MAX_RESOLUTION = 7680            # 8K width/height
MAX_FILE_SIZE_MB = 4096          # 4 GB

# Processing limits
MAX_CONCURRENT_PROCESSES = 4
DEFAULT_FFMPEG_TIMEOUT = 600     # 10 minutes
MAX_BATCH_SIZE = 50
MAX_SUBTITLE_ENTRIES = 1000
MAX_STORYBOARD_FRAMES = 50
MAX_EXPORT_FRAMES_FPS = 60

# Audio limits
MAX_AUDIO_DURATION = 3600        # 1 hour
MIN_FREQUENCY = 20               # Human hearing lower bound
MAX_FREQUENCY = 20000            # Human hearing upper bound
MIN_SAMPLE_RATE = 8000
MAX_SAMPLE_RATE = 96000

# Text/font limits
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 500

# Numeric parameter bounds
MIN_SPEED_FACTOR = 0.01
MAX_SPEED_FACTOR = 100.0
MIN_FADE_DURATION = 0.0
MAX_FADE_DURATION = 3600.0
