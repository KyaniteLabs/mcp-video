# ffmpeg_helpers.py as Single Source of Truth

All FFmpeg subprocess calls, path validation, filter escaping, and ffprobe queries are centralized in `ffmpeg_helpers.py`. No other module may duplicate `_run_ffmpeg()`, `_validate_input_path()`, `_escape_ffmpeg_filter_value()`, `_get_video_duration()`, or `_run_ffprobe_json()`. This prevents security bugs (unescaped user input) and behavior divergence.
