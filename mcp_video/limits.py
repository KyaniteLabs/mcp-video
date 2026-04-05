"""Resource limits and validation constants for mcp-video."""

# Video limits
MAX_VIDEO_DURATION = 14400  # 4 hours in seconds
MAX_RESOLUTION = 7680  # 8K width/height
MAX_FILE_SIZE_MB = 4096  # 4 GB

# Processing limits
MAX_CONCURRENT_PROCESSES = 4
DEFAULT_FFMPEG_TIMEOUT = 600  # 10 minutes
MAX_BATCH_SIZE = 50
MAX_SUBTITLE_ENTRIES = 1000
MAX_STORYBOARD_FRAMES = 50
MAX_EXPORT_FRAMES_FPS = 60

# Audio limits
MAX_AUDIO_DURATION = 3600  # 1 hour
MIN_FREQUENCY = 20  # Human hearing lower bound
MAX_FREQUENCY = 20000  # Human hearing upper bound
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

# Encoding parameter bounds
MAX_CRF = 51
MIN_CRF = 0

# Network / concurrency bounds
MAX_PORT = 65535
MIN_PORT = 1
MAX_CONCURRENCY = 16

# Audio loudness bounds (LUFS)
MAX_LUFS = -5
MIN_LUFS = -70

# Normalized 0-1 parameter bounds
MAX_INTENSITY = 1.0
MIN_INTENSITY = 0.0
MAX_OPACITY = 1.0
MIN_OPACITY = 0.0
MAX_SIMILARITY = 1.0
MIN_SIMILARITY = 0.0
MAX_BLEND = 1.0
MIN_BLEND = 0.0

# Pixel / processing bounds
MIN_PIXEL_SIZE = 2
MAX_SPEED_CHAIN_COUNT = 20
MAX_SCENES_PER_SECOND = 30  # max reasonable scene changes
