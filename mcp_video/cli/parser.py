"""Argument parser construction for the mcp-video CLI."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build and return the mcp-video CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-video",
        description="mcp-video — Video editing for AI agents (and humans)",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as MCP server (default mode)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    subparsers = parser.add_subparsers(dest="command", help="CLI commands")

    # doctor
    doctor_p = subparsers.add_parser("doctor", help="Diagnose core and optional integration dependencies")
    doctor_p.add_argument("--json", action="store_true", help="Output diagnostics as JSON")

    # info
    info_p = subparsers.add_parser("info", help="Get video metadata")
    info_p.add_argument("input", help="Input video file")

    # extract-frame
    eframe_p = subparsers.add_parser("extract-frame", help="Extract a single frame from a video")
    eframe_p.add_argument("input", help="Input video file")
    eframe_p.add_argument(
        "-t", "--time", dest="timestamp", type=float, help="Time in seconds (default: 10 pct of duration)"
    )
    eframe_p.add_argument("-o", "--output", help="Output image path")

    # trim
    trim_p = subparsers.add_parser("trim", help="Trim a video")
    trim_p.add_argument("input", help="Input video file")
    trim_p.add_argument("-s", "--start", default="0", help="Start time")
    trim_p.add_argument("-d", "--duration", help="Duration")
    trim_p.add_argument("-e", "--end", help="End time")
    trim_p.add_argument("-o", "--output", help="Output file path")

    # merge
    merge_p = subparsers.add_parser("merge", help="Merge multiple clips")
    merge_p.add_argument("inputs", nargs="+", help="Input video files")
    merge_p.add_argument(
        "-t",
        "--transition",
        default=None,
        choices=["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"],
    )
    merge_p.add_argument(
        "--transitions",
        nargs="+",
        choices=["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"],
        help="Per-pair transition types (overrides --transition)",
    )
    merge_p.add_argument("-td", "--transition-duration", type=float, default=1.0, help="Transition duration in seconds")
    merge_p.add_argument("-o", "--output", help="Output file path")

    # add_text
    text_p = subparsers.add_parser("add-text", help="Overlay text on a video")
    text_p.add_argument("input", help="Input video file")
    text_p.add_argument("text", help="Text to overlay")
    text_p.add_argument(
        "-p",
        "--position",
        default="top-center",
        choices=[
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "center-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ],
    )
    text_p.add_argument("--font", help="Path to font file")
    text_p.add_argument("--size", type=int, default=48, help="Font size in pixels")
    text_p.add_argument("--color", default="white", help="Text color")
    text_p.add_argument("--no-shadow", action="store_true", help="Disable text shadow")
    text_p.add_argument("--start-time", type=float, help="When text appears (seconds)")
    text_p.add_argument("--duration", type=float, help="How long text is visible (seconds)")
    text_p.add_argument("-o", "--output", help="Output file path")

    # add_audio
    audio_p = subparsers.add_parser("add-audio", help="Add or replace audio track")
    audio_p.add_argument("video", help="Input video file")
    audio_p.add_argument("audio", help="Audio file (MP3, WAV, etc.)")
    audio_p.add_argument("-v", "--volume", type=float, default=1.0, help="Audio volume (0.0-2.0)")
    audio_p.add_argument("--fade-in", type=float, default=0.0, help="Fade in duration")
    audio_p.add_argument("--fade-out", type=float, default=0.0, help="Fade out duration")
    audio_p.add_argument("--mix", action="store_true", help="Mix with existing audio instead of replacing")
    audio_p.add_argument("--start-time", type=float, help="When audio starts (seconds)")
    audio_p.add_argument("-o", "--output", help="Output file path")

    # resize
    resize_p = subparsers.add_parser("resize", help="Resize a video")
    resize_p.add_argument("input", help="Input video file")
    resize_p.add_argument("-w", "--width", type=int, help="Target width")
    resize_p.add_argument("--height", type=int, help="Target height")
    resize_p.add_argument(
        "-a", "--aspect-ratio", choices=["16:9", "9:16", "1:1", "4:3", "4:5", "21:9"], help="Preset aspect ratio"
    )
    resize_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    resize_p.add_argument("-o", "--output", help="Output file path")

    # speed
    speed_p = subparsers.add_parser("speed", help="Change playback speed")
    speed_p.add_argument("input", help="Input video file")
    speed_p.add_argument("-f", "--factor", type=float, default=1.0, help="Speed multiplier (0.5=slow, 2.0=fast)")
    speed_p.add_argument("-o", "--output", help="Output file path")

    # convert
    convert_p = subparsers.add_parser("convert", help="Convert video format")
    convert_p.add_argument("input", help="Input video file")
    convert_p.add_argument(
        "-f",
        "--format",
        "--fmt",
        dest="fmt",
        default="mp4",
        choices=["mp4", "webm", "gif", "mov"],
        help="Output format",
    )
    convert_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    convert_p.add_argument("-o", "--output", help="Output file path")

    # thumbnail
    thumb_p = subparsers.add_parser("thumbnail", help="Extract a single frame")
    thumb_p.add_argument("input", help="Input video file")
    thumb_p.add_argument("-t", "--timestamp", type=float, help="Time in seconds (default: 10%% of duration)")
    thumb_p.add_argument("-o", "--output", help="Output image path")

    # preview
    preview_p = subparsers.add_parser("preview", help="Generate a fast low-res preview")
    preview_p.add_argument("input", help="Input video file")
    preview_p.add_argument("-o", "--output", help="Output file path")
    preview_p.add_argument("-s", "--scale", type=int, default=4, help="Downscale factor (default: 4)")

    # storyboard
    storyboard_p = subparsers.add_parser("storyboard", help="Extract key frames as storyboard")
    storyboard_p.add_argument("input", help="Input video file")
    storyboard_p.add_argument("-o", "--output-dir", help="Output directory")
    storyboard_p.add_argument("-n", "--frames", type=int, default=8, help="Number of frames (default: 8)")

    # subtitles
    subs_p = subparsers.add_parser("subtitles", help="Burn subtitles into video")
    subs_p.add_argument("input", help="Input video file")
    subs_p.add_argument("subtitle", help="Subtitle file (.srt or .vtt)")
    subs_p.add_argument(
        "--style", help="Subtitle style as FFmpeg force_style string (e.g. FontSize=24,PrimaryColour=&H00FFFFFF)"
    )
    subs_p.add_argument("-o", "--output", help="Output file path")

    # watermark
    wm_p = subparsers.add_parser("watermark", help="Add image watermark")
    wm_p.add_argument("input", help="Input video file")
    wm_p.add_argument("image", help="Watermark image (PNG recommended)")
    wm_p.add_argument(
        "-p",
        "--position",
        default="bottom-right",
        choices=[
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ],
    )
    wm_p.add_argument("--opacity", type=float, default=0.7, help="Watermark opacity (0.0-1.0)")
    wm_p.add_argument("--margin", type=int, default=20, help="Margin from edge in pixels")
    wm_p.add_argument("--crf", type=int, help="Override CRF value (0-51)")
    wm_p.add_argument(
        "--preset", choices=["ultrafast", "fast", "medium", "slow", "veryslow"], help="FFmpeg encoding preset"
    )
    wm_p.add_argument("-o", "--output", help="Output file path")

    # crop
    crop_p = subparsers.add_parser("crop", help="Crop a video to a region")
    crop_p.add_argument("input", help="Input video file")
    crop_p.add_argument("-w", "--width", type=int, required=True, help="Crop width in pixels")
    crop_p.add_argument("--height", type=int, required=True, help="Crop height in pixels")
    crop_p.add_argument("-x", type=int, default=None, help="X offset (default: center)")
    crop_p.add_argument("-y", type=int, default=None, help="Y offset (default: center)")
    crop_p.add_argument("-o", "--output", help="Output file path")

    # rotate
    rotate_p = subparsers.add_parser("rotate", help="Rotate and/or flip a video")
    rotate_p.add_argument("input", help="Input video file")
    rotate_p.add_argument(
        "-a", "--angle", type=int, default=0, choices=[0, 90, 180, 270], help="Rotation angle in degrees"
    )
    rotate_p.add_argument("--flip-h", action="store_true", help="Flip horizontally")
    rotate_p.add_argument("--flip-v", action="store_true", help="Flip vertically")
    rotate_p.add_argument("-o", "--output", help="Output file path")

    # fade
    fade_p = subparsers.add_parser("fade", help="Add fade in/out to video")
    fade_p.add_argument("input", help="Input video file")
    fade_p.add_argument("--fade-in", type=float, default=0.0, help="Fade in duration (seconds)")
    fade_p.add_argument("--fade-out", type=float, default=0.0, help="Fade out duration (seconds)")
    fade_p.add_argument("--crf", type=int, help="Override CRF value (0-51)")
    fade_p.add_argument(
        "--preset", choices=["ultrafast", "fast", "medium", "slow", "veryslow"], help="FFmpeg encoding preset"
    )
    fade_p.add_argument("-o", "--output", help="Output file path")

    # export
    export_p = subparsers.add_parser("export", help="Export video with quality settings")
    export_p.add_argument("input", help="Input video file")
    export_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    export_p.add_argument(
        "-f",
        "--format",
        "--fmt",
        dest="fmt",
        default="mp4",
        choices=["mp4", "webm", "gif", "mov"],
        help="Output format",
    )
    export_p.add_argument("-o", "--output", help="Output file path")

    # extract_audio
    extract_p = subparsers.add_parser("extract-audio", help="Extract audio from video")
    extract_p.add_argument("input", help="Input video file")
    extract_p.add_argument(
        "-f", "--format", "--fmt", dest="audio_format", default="mp3", choices=["mp3", "aac", "wav", "ogg", "flac"]
    )
    extract_p.add_argument("-o", "--output", help="Output audio file path")

    # edit (timeline)
    edit_p = subparsers.add_parser("edit", help="Execute timeline-based edit from JSON")
    edit_p.add_argument("timeline", help="Path to timeline JSON file")
    edit_p.add_argument("-o", "--output", help="Output file path")

    # filter
    filter_p = subparsers.add_parser("filter", help="Apply a visual filter")
    filter_p.add_argument("input", help="Input video file")
    filter_p.add_argument(
        "-t",
        "--type",
        dest="filter_type",
        required=True,
        choices=[
            "blur",
            "sharpen",
            "brightness",
            "contrast",
            "saturation",
            "grayscale",
            "sepia",
            "invert",
            "vignette",
            "color_preset",
            "denoise",
            "deinterlace",
            "ken_burns",
            "reverb",
            "compressor",
            "pitch_shift",
            "noise_reduction",
        ],
        help="Filter type",
    )
    filter_p.add_argument("--params", help="Filter parameters as JSON")
    filter_p.add_argument("--crf", type=int, help="Override CRF value (0-51)")
    filter_p.add_argument(
        "--preset", choices=["ultrafast", "fast", "medium", "slow", "veryslow"], help="FFmpeg encoding preset"
    )
    filter_p.add_argument("-o", "--output", help="Output file path")

    # blur (convenience)
    blur_p = subparsers.add_parser("blur", help="Apply blur effect")
    blur_p.add_argument("input", help="Input video file")
    blur_p.add_argument("-r", "--radius", type=int, default=5, help="Blur radius (default: 5)")
    blur_p.add_argument("-s", "--strength", type=int, default=1, help="Blur strength (default: 1)")
    blur_p.add_argument("-o", "--output", help="Output file path")

    # reverse
    reverse_p = subparsers.add_parser("reverse", help="Reverse video playback")
    reverse_p.add_argument("input", help="Input video file")
    reverse_p.add_argument("-o", "--output", help="Output file path")

    # chroma-key
    chroma_p = subparsers.add_parser("chroma-key", help="Remove solid color background (green screen)")
    chroma_p.add_argument("input", help="Input video file")
    chroma_p.add_argument("--color", default="0x00FF00", help="Color to remove in hex (default: 0x00FF00 for green)")
    chroma_p.add_argument("--similarity", type=float, default=0.01, help="Color similarity threshold (default: 0.01)")
    chroma_p.add_argument("--blend", type=float, default=0.0, help="Blend amount (default: 0.0)")
    chroma_p.add_argument("-o", "--output", help="Output file path")

    # color-grade (convenience)
    grade_p = subparsers.add_parser("color-grade", help="Apply color grading preset")
    grade_p.add_argument("input", help="Input video file")
    grade_p.add_argument(
        "-p", "--preset", default="warm", choices=["warm", "cool", "vintage", "cinematic", "noir"], help="Color preset"
    )
    grade_p.add_argument("-o", "--output", help="Output file path")

    # normalize-audio
    norm_p = subparsers.add_parser("normalize-audio", help="Normalize audio loudness")
    norm_p.add_argument("input", help="Input video file")
    norm_p.add_argument("-l", "--lufs", type=float, default=-16.0, help="Target LUFS (default: -16 for YouTube)")
    norm_p.add_argument("--lra", type=float, help="Loudness Range target for broadcast compliance")
    norm_p.add_argument("-o", "--output", help="Output file path")

    # overlay-video
    overlay_p = subparsers.add_parser("overlay-video", help="Picture-in-picture overlay")
    overlay_p.add_argument("background", help="Background video file")
    overlay_p.add_argument("overlay", help="Overlay video file")
    overlay_p.add_argument(
        "-p",
        "--position",
        default="top-right",
        choices=[
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "center-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ],
    )
    overlay_p.add_argument("-w", "--width", type=int, help="Overlay width")
    overlay_p.add_argument("--height", type=int, help="Overlay height")
    overlay_p.add_argument("--opacity", type=float, default=0.8, help="Overlay opacity (0.0-1.0)")
    overlay_p.add_argument("--start-time", type=float, help="When overlay appears (seconds)")
    overlay_p.add_argument("--duration", type=float, help="How long overlay is visible (seconds)")
    overlay_p.add_argument("--crf", type=int, help="Override CRF value (0-51)")
    overlay_p.add_argument(
        "--preset", choices=["ultrafast", "fast", "medium", "slow", "veryslow"], help="FFmpeg encoding preset"
    )
    overlay_p.add_argument("-o", "--output", help="Output file path")

    # split-screen
    split_p = subparsers.add_parser("split-screen", help="Place two videos side by side or top/bottom")
    split_p.add_argument("left", help="First video file")
    split_p.add_argument("right", help="Second video file")
    split_p.add_argument(
        "-l", "--layout", default="side-by-side", choices=["side-by-side", "top-bottom"], help="Layout type"
    )
    split_p.add_argument("-o", "--output", help="Output file path")

    # batch
    batch_p = subparsers.add_parser("batch", help="Apply operation to multiple files")
    batch_p.add_argument("inputs", nargs="+", help="Input video files")
    batch_p.add_argument("-o", "--output-dir", help="Output directory for processed files")
    batch_p.add_argument(
        "--operation",
        required=True,
        choices=[
            "trim",
            "resize",
            "convert",
            "filter",
            "blur",
            "color_grade",
            "watermark",
            "speed",
            "fade",
            "normalize_audio",
        ],
        help="Operation to apply",
    )
    batch_p.add_argument("--params", help="Operation parameters as JSON")

    # detect-scenes
    scenes_p = subparsers.add_parser("detect-scenes", help="Detect scene changes in a video")
    scenes_p.add_argument("input", help="Input video file")
    scenes_p.add_argument(
        "-t", "--threshold", type=float, default=0.3, help="Detection sensitivity (0.0-1.0, default: 0.3)"
    )
    scenes_p.add_argument(
        "--min-duration", type=float, default=1.0, help="Minimum scene duration in seconds (default: 1.0)"
    )

    # create-from-images
    imgseq_p = subparsers.add_parser("create-from-images", help="Create video from image sequence")
    imgseq_p.add_argument("inputs", nargs="+", help="Input image files")
    imgseq_p.add_argument("-f", "--fps", type=float, default=30.0, help="Frames per second (default: 30)")
    imgseq_p.add_argument("-o", "--output", help="Output video file path")

    # export-frames
    frames_p = subparsers.add_parser("export-frames", help="Export video frames as images")
    frames_p.add_argument("input", help="Input video file")
    frames_p.add_argument("-o", "--output-dir", help="Output directory for frames")
    frames_p.add_argument("-f", "--fps", type=float, default=1.0, help="Frames per second to extract (default: 1)")
    frames_p.add_argument("--image-format", default="jpg", choices=["jpg", "png"], help="Image format (default: jpg)")

    # compare-quality
    quality_p = subparsers.add_parser("compare-quality", help="Compare video quality between two files")
    quality_p.add_argument("original", help="Original/reference video file")
    quality_p.add_argument("distorted", help="Processed/distorted video file")
    quality_p.add_argument(
        "--metrics", nargs="+", choices=["psnr", "ssim"], help="Metrics to compute (default: psnr ssim)"
    )

    # read-metadata
    read_meta_p = subparsers.add_parser("read-metadata", help="Read metadata tags from a file")
    read_meta_p.add_argument("input", help="Input video/audio file")

    # write-metadata
    write_meta_p = subparsers.add_parser("write-metadata", help="Write metadata tags to a file")
    write_meta_p.add_argument("input", help="Input video/audio file")
    write_meta_p.add_argument("--tags", required=True, help='Metadata as JSON, e.g. \'{"title": "My Video"}\'')
    write_meta_p.add_argument("-o", "--output", help="Output file path")

    # stabilize
    stab_p = subparsers.add_parser("stabilize", help="Stabilize a shaky video")
    stab_p.add_argument("input", help="Input video file")
    stab_p.add_argument("-s", "--smoothing", type=float, default=15, help="Smoothing strength (default: 15)")
    stab_p.add_argument("-z", "--zooming", type=float, default=0, help="Zoom to avoid black borders (default: 0)")
    stab_p.add_argument("-o", "--output", help="Output file path")

    # apply-mask
    mask_p = subparsers.add_parser("apply-mask", help="Apply an image mask to a video")
    mask_p.add_argument("input", help="Input video file")
    mask_p.add_argument("mask", help="Mask image file (white=visible, black=transparent)")
    mask_p.add_argument("--feather", type=int, default=5, help="Edge feather in pixels (default: 5)")
    mask_p.add_argument("-o", "--output", help="Output file path")

    # audio-waveform
    waveform_p = subparsers.add_parser("audio-waveform", help="Extract audio waveform data")
    waveform_p.add_argument("input", help="Input video/audio file")
    waveform_p.add_argument("-b", "--bins", type=int, default=50, help="Number of time segments (default: 50)")
    waveform_p.add_argument("-o", "--output", help="Output file path (optional, data is returned as JSON)")

    # generate-subtitles
    gen_subs_p = subparsers.add_parser("generate-subtitles", help="Generate SRT subtitles from text entries")
    gen_subs_p.add_argument("input", help="Input video file")
    gen_subs_p.add_argument(
        "--entries", required=True, help='Subtitle entries as JSON: \'[{"start":0,"end":2,"text":"Hello"}]\''
    )
    gen_subs_p.add_argument("--burn", action="store_true", help="Burn subtitles into video")
    gen_subs_p.add_argument("-o", "--output", help="Output directory/path (default: auto-generated)")

    # templates (list available templates)
    subparsers.add_parser("templates", help="List available video templates")

    # template (apply a template)
    template_p = subparsers.add_parser("template", help="Apply a video template")
    template_p.add_argument(
        "name",
        choices=["tiktok", "youtube-shorts", "instagram-reel", "youtube", "instagram-post"],
        help="Template name",
    )
    template_p.add_argument("input", help="Input video file")
    template_p.add_argument("--caption", help="Caption text (for tiktok, instagram)")
    template_p.add_argument("--title", help="Title text (for youtube-shorts, youtube)")
    template_p.add_argument("--music", help="Background music file")
    template_p.add_argument("--outro", help="Outro video file (for youtube)")
    template_p.add_argument("-o", "--output", help="Output file path")

    # ------------------------------------------------------------------
    # Remotion commands
    # ------------------------------------------------------------------

    # remotion-render
    remotion_render_p = subparsers.add_parser("remotion-render", help="Render a Remotion composition to video")
    remotion_render_p.add_argument("project_path", help="Path to Remotion project")
    remotion_render_p.add_argument("composition_id", help="Composition ID to render")
    remotion_render_p.add_argument("-o", "--output", help="Output video file path")
    remotion_render_p.add_argument(
        "--codec",
        default="h264",
        choices=["h264", "h265", "vp8", "vp9", "prores", "gif"],
        help="Video codec (default: h264)",
    )
    remotion_render_p.add_argument("--crf", type=int, default=18, help="CRF quality (default: 18)")
    remotion_render_p.add_argument("--width", type=int, help="Output width in pixels")
    remotion_render_p.add_argument("--height", type=int, help="Output height in pixels")
    remotion_render_p.add_argument("--fps", type=float, default=30.0, help="Frames per second (default: 30)")
    remotion_render_p.add_argument("--concurrency", type=int, default=1, help="Number of concurrent render threads")
    remotion_render_p.add_argument("--frames", help="Frame range (e.g. '0-90' or '10-50')")
    remotion_render_p.add_argument("--props", help="Input props as JSON")
    remotion_render_p.add_argument("--scale", type=float, default=1.0, help="Render scale factor")

    # remotion-compositions
    remotion_comps_p = subparsers.add_parser("remotion-compositions", help="List compositions in a Remotion project")
    remotion_comps_p.add_argument("project_path", help="Path to Remotion project")
    remotion_comps_p.add_argument("--composition-id", help="Filter by specific composition ID")
    remotion_comps_p.add_argument("--json", action="store_true", help="Output raw JSON")
    remotion_comps_p.add_argument("-o", "--output", help="Output file path")

    # remotion-studio
    remotion_studio_p = subparsers.add_parser("remotion-studio", help="Launch Remotion Studio for live preview")
    remotion_studio_p.add_argument("project_path", help="Path to Remotion project")
    remotion_studio_p.add_argument("-p", "--port", type=int, default=3000, help="Studio port (default: 3000)")
    remotion_studio_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # remotion-still
    remotion_still_p = subparsers.add_parser("remotion-still", help="Render a single frame as image")
    remotion_still_p.add_argument("project_path", help="Path to Remotion project")
    remotion_still_p.add_argument("composition_id", help="Composition ID to render")
    remotion_still_p.add_argument("-o", "--output", help="Output image file path")
    remotion_still_p.add_argument("--frame", type=int, default=0, help="Frame number to render (default: 0)")
    remotion_still_p.add_argument(
        "--image-format", default="png", choices=["png", "jpeg", "webp"], help="Image format (default: png)"
    )

    # remotion-create
    remotion_create_p = subparsers.add_parser("remotion-create", help="Scaffold a new Remotion project")
    remotion_create_p.add_argument("name", help="Project name")
    remotion_create_p.add_argument("-d", "--output-dir", help="Output directory (default: current directory)")
    remotion_create_p.add_argument(
        "-t", "--template", default="blank", choices=["blank", "hello-world"], help="Project template (default: blank)"
    )

    # remotion-scaffold
    remotion_scaffold_p = subparsers.add_parser("remotion-scaffold", help="Generate composition from spec")
    remotion_scaffold_p.add_argument("project_path", help="Path to Remotion project")
    remotion_scaffold_p.add_argument("--spec", required=True, help="Composition spec as JSON")
    remotion_scaffold_p.add_argument("--slug", required=True, help="Slug for the composition (used for filenames)")

    # remotion-validate
    remotion_validate_p = subparsers.add_parser("remotion-validate", help="Validate a Remotion project")
    remotion_validate_p.add_argument("project_path", help="Path to Remotion project")
    remotion_validate_p.add_argument("--composition-id", help="Specific composition ID to validate")

    # remotion-pipeline
    remotion_pipeline_p = subparsers.add_parser("remotion-pipeline", help="Render + post-process in one step")
    remotion_pipeline_p.add_argument("project_path", help="Path to Remotion project")
    remotion_pipeline_p.add_argument("composition_id", help="Composition ID to render")
    remotion_pipeline_p.add_argument("--post-process", required=True, help="Post-processing operations as JSON list")
    remotion_pipeline_p.add_argument("-o", "--output", help="Final output file path")

    # ------------------------------------------------------------------
    # Effect commands
    # ------------------------------------------------------------------

    # effect-vignette
    vig_p = subparsers.add_parser("effect-vignette", help="Apply vignette effect (darkened edges)")
    vig_p.add_argument("input", help="Input video file")
    vig_p.add_argument("-o", "--output", help="Output file path")
    vig_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Darkness amount 0-1 (default: 0.5)")
    vig_p.add_argument("-r", "--radius", type=float, default=0.8, help="Vignette radius 0-1 (default: 0.8)")
    vig_p.add_argument("-s", "--smoothness", type=float, default=0.5, help="Edge softness 0-1 (default: 0.5)")

    # effect-glow
    glow_p = subparsers.add_parser("effect-glow", help="Apply bloom/glow effect to highlights")
    glow_p.add_argument("input", help="Input video file")
    glow_p.add_argument("-o", "--output", help="Output file path")
    glow_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Glow strength 0-1 (default: 0.5)")
    glow_p.add_argument("-r", "--radius", type=int, default=10, help="Blur radius in pixels (default: 10)")
    glow_p.add_argument("-t", "--threshold", type=float, default=0.7, help="Brightness threshold 0-1 (default: 0.7)")

    # effect-noise
    noise_p = subparsers.add_parser("effect-noise", help="Apply film grain or digital noise")
    noise_p.add_argument("input", help="Input video file")
    noise_p.add_argument("-o", "--output", help="Output file path")
    noise_p.add_argument("-i", "--intensity", type=float, default=0.05, help="Noise amount 0-1 (default: 0.05)")
    noise_p.add_argument(
        "-m", "--mode", default="film", choices=["film", "digital", "color"], help="Noise type (default: film)"
    )
    noise_p.add_argument("--static", action="store_true", help="Use static noise instead of animated")

    # effect-scanlines
    scan_p = subparsers.add_parser("effect-scanlines", help="Apply CRT-style scanlines overlay")
    scan_p.add_argument("input", help="Input video file")
    scan_p.add_argument("-o", "--output", help="Output file path")
    scan_p.add_argument("--line-height", type=int, default=2, help="Pixels per scanline (default: 2)")
    scan_p.add_argument("--opacity", type=float, default=0.3, help="Line opacity 0-1 (default: 0.3)")
    scan_p.add_argument("--flicker", type=float, default=0.1, help="Brightness variation 0-1 (default: 0.1)")

    # effect-chromatic-aberration
    chroma_p = subparsers.add_parser("effect-chromatic-aberration", help="Apply RGB channel separation")
    chroma_p.add_argument("input", help="Input video file")
    chroma_p.add_argument("-o", "--output", help="Output file path")
    chroma_p.add_argument("-i", "--intensity", type=float, default=2.0, help="Pixel offset amount (default: 2.0)")
    chroma_p.add_argument("-a", "--angle", type=float, default=0, help="Separation direction in degrees (default: 0)")

    # ------------------------------------------------------------------
    # Transition commands
    # ------------------------------------------------------------------

    # transition-glitch
    tglitch_p = subparsers.add_parser("transition-glitch", help="Apply glitch transition between two clips")
    tglitch_p.add_argument("clip1", help="First video clip")
    tglitch_p.add_argument("clip2", help="Second video clip")
    tglitch_p.add_argument("-o", "--output", help="Output file path")
    tglitch_p.add_argument(
        "-d", "--duration", type=float, default=0.5, help="Transition duration in seconds (default: 0.5)"
    )
    tglitch_p.add_argument("-i", "--intensity", type=float, default=0.3, help="Glitch intensity 0-1 (default: 0.3)")

    # transition-morph
    tmorph_p = subparsers.add_parser("transition-morph", help="Apply morph transition between two clips")
    tmorph_p.add_argument("clip1", help="First video clip")
    tmorph_p.add_argument("clip2", help="Second video clip")
    tmorph_p.add_argument("-o", "--output", help="Output file path")
    tmorph_p.add_argument(
        "-d", "--duration", type=float, default=0.6, help="Transition duration in seconds (default: 0.6)"
    )
    tmorph_p.add_argument("--mesh-size", type=int, default=10, help="Mesh warp intensity (default: 10)")

    # transition-pixelate
    tpxl_p = subparsers.add_parser("transition-pixelate", help="Apply pixelate transition between two clips")
    tpxl_p.add_argument("clip1", help="First video clip")
    tpxl_p.add_argument("clip2", help="Second video clip")
    tpxl_p.add_argument("-o", "--output", help="Output file path")
    tpxl_p.add_argument(
        "-d", "--duration", type=float, default=0.4, help="Transition duration in seconds (default: 0.4)"
    )
    tpxl_p.add_argument("--pixel-size", type=int, default=50, help="Pixel size (default: 50)")

    # ------------------------------------------------------------------
    # AI commands
    # ------------------------------------------------------------------

    # video-ai-transcribe
    aitrans_p = subparsers.add_parser("video-ai-transcribe", help="Transcribe speech to text using Whisper")
    aitrans_p.add_argument("input", help="Input video file")
    aitrans_p.add_argument("-o", "--output", help="Output SRT file path")
    aitrans_p.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model (default: base)",
    )
    aitrans_p.add_argument("--language", help="Language code (auto-detect if omitted)")

    # video-analyze
    analyze_p = subparsers.add_parser(
        "video-analyze",
        help="Comprehensive video analysis: transcript, metadata, scenes, audio, quality, chapters, colors",
    )
    analyze_p.add_argument("input", help="Input video file")
    analyze_p.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper model (default: base)",
    )
    analyze_p.add_argument("--language", help="Language code for transcription (auto-detect if omitted)")
    analyze_p.add_argument(
        "--scene-threshold", type=float, default=0.3, help="Scene change sensitivity 0.0-1.0 (default: 0.3)"
    )
    analyze_p.add_argument("--no-transcript", action="store_true", help="Skip speech-to-text transcription")
    analyze_p.add_argument("--no-scenes", action="store_true", help="Skip scene detection")
    analyze_p.add_argument("--no-audio", action="store_true", help="Skip audio waveform analysis")
    analyze_p.add_argument("--no-quality", action="store_true", help="Skip visual quality check")
    analyze_p.add_argument("--no-chapters", action="store_true", help="Skip chapter generation")
    analyze_p.add_argument("--no-colors", action="store_true", help="Skip color extraction")
    analyze_p.add_argument("--output-srt", help="Write SRT subtitle file to this path")
    analyze_p.add_argument("--output-txt", help="Write plain-text transcript to this path")
    analyze_p.add_argument("--output-md", help="Write Markdown transcript to this path")
    analyze_p.add_argument("--output-json", help="Write full JSON transcript to this path")

    # video-ai-upscale
    aiup_p = subparsers.add_parser("video-ai-upscale", help="Upscale video using AI super-resolution")
    aiup_p.add_argument("input", help="Input video file")
    aiup_p.add_argument("-o", "--output", help="Output file path")
    aiup_p.add_argument("-s", "--scale", type=int, default=2, choices=[2, 4], help="Upscale factor (default: 2)")
    aiup_p.add_argument("--model", default="realesrgan", help="Model name (default: realesrgan)")

    # video-ai-stem-separation
    aistem_p = subparsers.add_parser("video-ai-stem-separation", help="Separate audio into stems using Demucs")
    aistem_p.add_argument("input", help="Input video file")
    aistem_p.add_argument("-o", "--output-dir", required=True, help="Output directory for stem files")
    aistem_p.add_argument("--stems", nargs="+", help="Stems to extract (default: vocals drums bass other)")
    aistem_p.add_argument("--model", default="htdemucs", help="Demucs model (default: htdemucs)")

    # video-ai-scene-detect
    aiscene_p = subparsers.add_parser("video-ai-scene-detect", help="Detect scene changes using perceptual hashing")
    aiscene_p.add_argument("input", help="Input video file")
    aiscene_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Detection threshold (default: 0.3)")
    aiscene_p.add_argument("--use-ai", action="store_true", help="Use perceptual hashing for better accuracy")

    # video-ai-color-grade
    aigrade_p = subparsers.add_parser("video-ai-color-grade", help="Auto color grade video")
    aigrade_p.add_argument("input", help="Input video file")
    aigrade_p.add_argument("-o", "--output", help="Output file path")
    aigrade_p.add_argument("--reference", help="Reference video for color matching")
    aigrade_p.add_argument(
        "--style",
        default="auto",
        choices=["auto", "cinematic", "vintage", "warm", "cool", "dramatic"],
        help="Color style (default: auto)",
    )

    # video-ai-remove-silence
    airms_p = subparsers.add_parser("video-ai-remove-silence", help="Remove silent sections from video")
    airms_p.add_argument("input", help="Input video file")
    airms_p.add_argument("-o", "--output", help="Output file path")
    airms_p.add_argument("--silence-threshold", type=float, default=-50, help="Silence threshold in dB (default: -50)")
    airms_p.add_argument(
        "--min-silence-duration", type=float, default=0.5, help="Min silence duration in seconds (default: 0.5)"
    )
    airms_p.add_argument(
        "--keep-margin", type=float, default=0.1, help="Keep margin around silence in seconds (default: 0.1)"
    )

    # ------------------------------------------------------------------
    # Audio synthesis commands
    # ------------------------------------------------------------------

    # audio-synthesize
    asynth_p = subparsers.add_parser("audio-synthesize", help="Generate audio using waveform synthesis")
    asynth_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    asynth_p.add_argument(
        "-w",
        "--waveform",
        default="sine",
        choices=["sine", "square", "sawtooth", "triangle", "noise"],
        help="Waveform type (default: sine)",
    )
    asynth_p.add_argument("-f", "--frequency", type=float, default=440.0, help="Frequency in Hz (default: 440)")
    asynth_p.add_argument("-d", "--duration", type=float, default=1.0, help="Duration in seconds (default: 1.0)")
    asynth_p.add_argument("-v", "--volume", type=float, default=0.5, help="Volume 0-1 (default: 0.5)")
    asynth_p.add_argument("--effects", help='Effects as JSON, e.g. \'{"reverb": {"room_size": 0.5}}\'')

    # audio-compose
    acomp_p = subparsers.add_parser("audio-compose", help="Layer multiple audio tracks with mixing")
    acomp_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    acomp_p.add_argument("-d", "--duration", type=float, required=True, help="Total duration in seconds")
    acomp_p.add_argument(
        "--tracks", required=True, help="Tracks as JSON: [{'file': 'a.wav', 'volume': 0.5, 'start': 0}]"
    )

    # audio-preset
    apreset_p = subparsers.add_parser("audio-preset", help="Generate preset sound design elements")
    apreset_p.add_argument(
        "preset",
        help="Preset name: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down, drone-low, drone-mid, drone-tech, drone-ominous, chime-success, chime-error, chime-notification, typing, scan, processing, data-flow, upload, download",
    )
    apreset_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    apreset_p.add_argument(
        "--pitch", default="mid", choices=["low", "mid", "high"], help="Pitch variation (default: mid)"
    )
    apreset_p.add_argument("-d", "--duration", type=float, help="Override default duration (seconds)")
    apreset_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Effect intensity 0-1 (default: 0.5)")

    # audio-sequence
    aseq_p = subparsers.add_parser("audio-sequence", help="Compose audio events into a timed sequence")
    aseq_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    aseq_p.add_argument(
        "--sequence", required=True, help="Sequence as JSON: [{'type': 'tone', 'at': 0, 'duration': 1, 'freq': 440}]"
    )

    # audio-effects
    aefx_p = subparsers.add_parser("audio-effects", help="Apply audio effects chain to a WAV file")
    aefx_p.add_argument("input", help="Input WAV file")
    aefx_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    aefx_p.add_argument("--effects", required=True, help="Effects as JSON: [{'type': 'lowpass', 'cutoff': 1000}]")

    # ------------------------------------------------------------------
    # Motion graphics commands
    # ------------------------------------------------------------------

    # video-text-animated
    tanim_p = subparsers.add_parser("video-text-animated", help="Add animated text to video")
    tanim_p.add_argument("input", help="Input video file")
    tanim_p.add_argument("text", help="Text to display")
    tanim_p.add_argument("-o", "--output", help="Output file path")
    tanim_p.add_argument(
        "-a",
        "--animation",
        default="fade",
        choices=["fade", "slide-up", "typewriter", "glitch"],
        help="Animation type (default: fade)",
    )
    tanim_p.add_argument("--font", default="Arial", help="Font family (default: Arial)")
    tanim_p.add_argument("--size", type=int, default=48, help="Font size in pixels (default: 48)")
    tanim_p.add_argument("--color", default="white", help="Text color (default: white)")
    tanim_p.add_argument(
        "-p",
        "--position",
        default="center",
        choices=["center", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"],
        help="Text position (default: center)",
    )
    tanim_p.add_argument("--start", type=float, default=0, help="Start time in seconds (default: 0)")
    tanim_p.add_argument("--duration", type=float, default=3.0, help="Display duration in seconds (default: 3.0)")

    # video-mograph-count
    mcount_p = subparsers.add_parser("video-mograph-count", help="Generate animated number counter video")
    mcount_p.add_argument("start", type=int, help="Starting number")
    mcount_p.add_argument("end", type=int, help="Ending number")
    mcount_p.add_argument("-d", "--duration", type=float, required=True, help="Animation duration in seconds")
    mcount_p.add_argument("-o", "--output", required=True, help="Output video file path")
    mcount_p.add_argument("--style", help='Style as JSON: {"font": "Arial", "size": 160, "color": "white"}')
    mcount_p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")

    # video-mograph-progress
    mprog_p = subparsers.add_parser("video-mograph-progress", help="Generate progress bar / loading animation")
    mprog_p.add_argument("-d", "--duration", type=float, required=True, help="Animation duration in seconds")
    mprog_p.add_argument("-o", "--output", required=True, help="Output video file path")
    mprog_p.add_argument(
        "--style", default="bar", choices=["bar", "circle", "dots"], help="Progress style (default: bar)"
    )
    mprog_p.add_argument("--color", default="#CCFF00", help="Progress color hex (default: #CCFF00)")
    mprog_p.add_argument("--track-color", default="#333333", help="Track background color hex (default: #333333)")
    mprog_p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")

    # ------------------------------------------------------------------
    # Layout commands
    # ------------------------------------------------------------------

    # video-layout-grid
    lgrid_p = subparsers.add_parser("video-layout-grid", help="Arrange multiple videos in a grid")
    lgrid_p.add_argument("inputs", nargs="+", help="Input video files")
    lgrid_p.add_argument(
        "-l", "--layout", default="2x2", choices=["2x2", "3x1", "1x3", "2x3"], help="Grid layout (default: 2x2)"
    )
    lgrid_p.add_argument("-o", "--output", required=True, help="Output file path")
    lgrid_p.add_argument("--gap", type=int, default=10, help="Gap between clips in pixels (default: 10)")
    lgrid_p.add_argument("--padding", type=int, default=20, help="Padding around grid in pixels (default: 20)")
    lgrid_p.add_argument("--background", default="#141414", help="Background color hex (default: #141414)")

    # video-layout-pip
    lpip_p = subparsers.add_parser("video-layout-pip", help="Picture-in-picture overlay with border")
    lpip_p.add_argument("main", help="Main video file")
    lpip_p.add_argument("pip", help="Picture-in-picture video file")
    lpip_p.add_argument("-o", "--output", required=True, help="Output file path")
    lpip_p.add_argument(
        "-p",
        "--position",
        default="bottom-right",
        choices=["top-left", "top-right", "bottom-left", "bottom-right"],
        help="PIP position (default: bottom-right)",
    )
    lpip_p.add_argument(
        "-s", "--size", type=float, default=0.25, help="PIP size as fraction of main 0-1 (default: 0.25)"
    )
    lpip_p.add_argument("--margin", type=int, default=20, help="Margin from edges in pixels (default: 20)")
    lpip_p.add_argument("--border", action="store_true", default=True, help="Add border around PIP (default: True)")
    lpip_p.add_argument("--no-border", dest="border", action="store_false", help="Disable border around PIP")
    lpip_p.add_argument("--border-color", default="#CCFF00", help="Border color hex (default: #CCFF00)")
    lpip_p.add_argument("--border-width", type=int, default=2, help="Border width in pixels (default: 2)")
    lpip_p.add_argument(
        "--rounded-corners", action="store_true", default=True, help="Apply rounded corners to PIP (default: True)"
    )
    lpip_p.add_argument(
        "--no-rounded-corners", dest="rounded_corners", action="store_false", help="Disable rounded corners"
    )

    # ------------------------------------------------------------------
    # Audio-Video commands
    # ------------------------------------------------------------------

    # video-add-generated-audio
    addgen_p = subparsers.add_parser("video-add-generated-audio", help="Add procedurally generated audio to video")
    addgen_p.add_argument("input", help="Input video file")
    addgen_p.add_argument(
        "--audio-config", required=True, help='Audio config as JSON: {"drone": {"frequency": 100}, "events": [...]}'
    )
    addgen_p.add_argument("-o", "--output", help="Output file path")

    # video-audio-spatial
    aspat_p = subparsers.add_parser("video-audio-spatial", help="Apply 3D spatial audio positioning")
    aspat_p.add_argument("input", help="Input video file")
    aspat_p.add_argument("-o", "--output", help="Output file path")
    aspat_p.add_argument(
        "--positions", required=True, help='Positions as JSON: [{"time": 0, "azimuth": 0, "elevation": 0}]'
    )
    aspat_p.add_argument(
        "--method", default="hrtf", choices=["hrtf", "vbap", "simple"], help="Spatialization method (default: hrtf)"
    )

    # ------------------------------------------------------------------
    # Quality / Info commands
    # ------------------------------------------------------------------

    # video-auto-chapters
    achap_p = subparsers.add_parser("video-auto-chapters", help="Auto-detect scene changes and create chapters")
    achap_p.add_argument("input", help="Input video file")
    achap_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Scene detection threshold (default: 0.3)")

    # video-extract-frame
    eframe_p = subparsers.add_parser("video-extract-frame", help="Extract a single frame (alias for thumbnail)")
    eframe_p.add_argument("input", help="Input video file")
    eframe_p.add_argument("-t", "--timestamp", type=float, help="Time in seconds (default: 10%% of duration)")
    eframe_p.add_argument("-o", "--output", help="Output image path")

    # video-info-detailed
    idetail_p = subparsers.add_parser("video-info-detailed", help="Get extended video metadata with scene detection")
    idetail_p.add_argument("input", help="Input video file")

    # video-quality-check
    qcheck_p = subparsers.add_parser("video-quality-check", help="Run visual quality checks on a video")
    qcheck_p.add_argument("input", help="Input video file")
    qcheck_p.add_argument("--fail-on-warning", action="store_true", help="Treat warnings as failures")

    # video-design-quality-check
    dqcheck_p = subparsers.add_parser("video-design-quality-check", help="Run design quality analysis on a video")
    dqcheck_p.add_argument("input", help="Input video file")
    dqcheck_p.add_argument("--auto-fix", action="store_true", help="Automatically fix issues where possible")
    dqcheck_p.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    # video-fix-design-issues
    dfix_p = subparsers.add_parser("video-fix-design-issues", help="Auto-fix design issues in a video")
    dfix_p.add_argument("input", help="Input video file")
    dfix_p.add_argument("-o", "--output", help="Output file path (auto-generated if omitted)")

    # ------------------------------------------------------------------
    # Image analysis commands
    # ------------------------------------------------------------------

    # image-extract-colors
    imgcol_p = subparsers.add_parser("image-extract-colors", help="Extract dominant colors from an image")
    imgcol_p.add_argument("input", help="Input image file")
    imgcol_p.add_argument(
        "-n", "--n-colors", type=int, default=5, help="Number of colors to extract (default: 5, max: 20)"
    )

    # image-generate-palette
    imgpal_p = subparsers.add_parser("image-generate-palette", help="Generate color harmony palette from image")
    imgpal_p.add_argument("input", help="Input image file")
    imgpal_p.add_argument(
        "--harmony",
        default="complementary",
        choices=["complementary", "analogous", "triadic", "split_complementary"],
        help="Harmony type (default: complementary)",
    )
    imgpal_p.add_argument("-n", "--n-colors", type=int, default=5, help="Number of base colors (default: 5, max: 20)")

    # image-analyze-product
    imgprod_p = subparsers.add_parser(
        "image-analyze-product", help="Analyze a product image (colors + optional AI description)"
    )
    imgprod_p.add_argument("input", help="Input image file")
    imgprod_p.add_argument(
        "--use-ai", action="store_true", help="Use Claude Vision for description (requires ANTHROPIC_API_KEY)"
    )
    imgprod_p.add_argument(
        "-n", "--n-colors", type=int, default=5, help="Number of colors to extract (default: 5, max: 20)"
    )

    return parser
