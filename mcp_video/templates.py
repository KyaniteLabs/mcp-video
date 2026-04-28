"""Editing templates for common video formats."""

from __future__ import annotations

from typing import Any


def tiktok_template(
    video_path: str,
    caption: str | None = None,
    music_path: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate a timeline for TikTok (9:16, 1080x1920).

    Args:
        video_path: Path to the source video.
        caption: Optional caption text at the bottom.
        music_path: Optional background music.
        output_path: Where to save the final video.
    """
    timeline: dict[str, Any] = {
        "width": 1080,
        "height": 1920,
        "tracks": [
            {
                "type": "video",
                "clips": [
                    {"source": video_path, "start": 0},
                ],
            }
        ],
        "export": {"format": "mp4", "quality": "high"},
    }

    if caption:
        timeline["tracks"].append(
            {
                "type": "text",
                "elements": [
                    {
                        "text": caption,
                        "start": 0,
                        "position": "bottom-center",
                        "style": {"size": 36, "color": "white", "shadow": True},
                    }
                ],
            }
        )

    if music_path:
        timeline["tracks"].append(
            {
                "type": "audio",
                "clips": [
                    {"source": music_path, "start": 0, "volume": 0.5, "fade_in": 1.0, "fade_out": 2.0},
                ],
            }
        )

    return timeline


def youtube_shorts_template(
    video_path: str,
    title: str | None = None,
    music_path: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate a timeline for YouTube Shorts (9:16, 1080x1920)."""
    timeline = tiktok_template(video_path, caption=title, music_path=music_path, output_path=output_path)

    # YouTube Shorts uses same format as TikTok but with a different title position
    if title:
        for track in timeline["tracks"]:
            if track["type"] == "text":
                track["elements"][0]["position"] = "top-center"
                track["elements"][0]["style"]["size"] = 42

    return timeline


def instagram_reel_template(
    video_path: str,
    caption: str | None = None,
    music_path: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate a timeline for Instagram Reels (9:16, 1080x1920)."""
    return tiktok_template(video_path, caption=caption, music_path=music_path, output_path=output_path)


def youtube_video_template(
    video_path: str,
    title: str | None = None,
    outro_path: str | None = None,
    music_path: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate a timeline for standard YouTube video (16:9, 1920x1080).

    Args:
        video_path: Path to the main video content.
        title: Optional title card text (shown for first 3 seconds).
        outro_path: Optional outro clip appended at the end.
        music_path: Optional background music.
        output_path: Where to save the final video.
    """
    clips: list[dict[str, Any]] = [{"source": video_path, "start": 0}]

    if outro_path:
        clips.append({"source": outro_path, "start": 0})

    timeline: dict[str, Any] = {
        "width": 1920,
        "height": 1080,
        "tracks": [
            {
                "type": "video",
                "clips": clips,
            }
        ],
        "export": {"format": "mp4", "quality": "high"},
    }

    if title:
        timeline["tracks"].append(
            {
                "type": "text",
                "elements": [
                    {
                        "text": title,
                        "start": 0,
                        "duration": 3,
                        "position": "top-center",
                        "style": {"size": 48, "color": "white", "shadow": True},
                    }
                ],
            }
        )

    if music_path:
        timeline["tracks"].append(
            {
                "type": "audio",
                "clips": [
                    {"source": music_path, "start": 0, "volume": 0.3, "fade_in": 2.0, "fade_out": 3.0},
                ],
            }
        )

    return timeline


def instagram_post_template(
    video_path: str,
    caption: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate a timeline for Instagram post (1:1, 1080x1080)."""
    timeline: dict[str, Any] = {
        "width": 1080,
        "height": 1080,
        "tracks": [
            {
                "type": "video",
                "clips": [
                    {"source": video_path, "start": 0},
                ],
            }
        ],
        "export": {"format": "mp4", "quality": "high"},
    }

    if caption:
        timeline["tracks"].append(
            {
                "type": "text",
                "elements": [
                    {
                        "text": caption,
                        "start": 0,
                        "position": "bottom-center",
                        "style": {"size": 32, "color": "white", "shadow": True},
                    }
                ],
            }
        )

    return timeline


def preview_template(
    template_name: str,
    video_path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return a preview of what a template would produce without rendering.

    Returns:
        Dict with ``operations``, ``estimated_duration``, ``resolution``,
        ``format``, and ``quality`` for agent review before committing.
    """
    tmpl = TEMPLATES.get(template_name)
    if tmpl is None:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(TEMPLATES.keys())}")
    timeline = tmpl(video_path, **kwargs)
    tracks = timeline.get("tracks", [])
    export = timeline.get("export", {})

    operations: list[str] = []
    video_clips: list[dict] = []
    for track in tracks:
        ttype = track.get("type")
        if ttype == "video":
            video_clips = track.get("clips", [])
            operations.append(f"resize_to_{timeline['width']}x{timeline['height']}")
        elif ttype == "text":
            operations.append(f"add_text ({len(track.get('elements', []))} overlay(s))")
        elif ttype == "audio":
            operations.append(f"mix_audio ({len(track.get('clips', []))} track(s))")

    total_duration = 0.0
    for clip in video_clips:
        dur = clip.get("duration") or clip.get("trim_end")
        if dur is None:
            dur = 10.0  # fallback
        total_duration += float(dur)

    return {
        "template": template_name,
        "operations": operations,
        "estimated_duration": round(total_duration, 1),
        "resolution": f"{timeline['width']}x{timeline['height']}",
        "format": export.get("format", "mp4"),
        "quality": export.get("quality", "high"),
        "timeline": timeline,
    }


# Template registry
TEMPLATES: dict[str, Any] = {
    "tiktok": tiktok_template,
    "youtube-shorts": youtube_shorts_template,
    "instagram-reel": instagram_reel_template,
    "youtube": youtube_video_template,
    "instagram-post": instagram_post_template,
}
