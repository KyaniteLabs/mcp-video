"""Tests for editing templates — no FFmpeg needed (validate JSON output)."""

import pytest

from mcp_video.templates import (
    TEMPLATES,
    instagram_post_template,
    instagram_reel_template,
    tiktok_template,
    youtube_video_template,
    youtube_shorts_template,
)


class TestTikTokTemplate:
    def test_basic_structure(self):
        tl = tiktok_template("/tmp/video.mp4")
        assert isinstance(tl, dict)
        assert tl["width"] == 1080
        assert tl["height"] == 1920
        assert tl["export"]["format"] == "mp4"
        assert tl["export"]["quality"] == "high"

    def test_video_track_present(self):
        tl = tiktok_template("/tmp/video.mp4")
        video_tracks = [t for t in tl["tracks"] if t["type"] == "video"]
        assert len(video_tracks) == 1
        assert video_tracks[0]["clips"][0]["source"] == "/tmp/video.mp4"

    def test_with_caption(self):
        tl = tiktok_template("/tmp/video.mp4", caption="Follow me!")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 1
        assert text_tracks[0]["elements"][0]["text"] == "Follow me!"
        assert text_tracks[0]["elements"][0]["position"] == "bottom-center"

    def test_with_music(self):
        tl = tiktok_template("/tmp/video.mp4", music_path="/tmp/music.mp3")
        audio_tracks = [t for t in tl["tracks"] if t["type"] == "audio"]
        assert len(audio_tracks) == 1
        assert audio_tracks[0]["clips"][0]["source"] == "/tmp/music.mp3"
        assert audio_tracks[0]["clips"][0]["volume"] == 0.5

    def test_caption_style(self):
        tl = tiktok_template("/tmp/video.mp4", caption="Test")
        text_track = [t for t in tl["tracks"] if t["type"] == "text"][0]
        style = text_track["elements"][0]["style"]
        assert style["size"] == 36
        assert style["color"] == "white"
        assert style["shadow"] is True


class TestYouTubeShortsTemplate:
    def test_basic_structure(self):
        tl = youtube_shorts_template("/tmp/video.mp4")
        assert tl["width"] == 1080
        assert tl["height"] == 1920

    def test_title_position_top_center(self):
        tl = youtube_shorts_template("/tmp/video.mp4", title="My Short")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 1
        assert text_tracks[0]["elements"][0]["position"] == "top-center"
        assert text_tracks[0]["elements"][0]["style"]["size"] == 42

    def test_without_title(self):
        tl = youtube_shorts_template("/tmp/video.mp4")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 0


class TestInstagramReelTemplate:
    def test_basic_structure(self):
        tl = instagram_reel_template("/tmp/video.mp4")
        assert tl["width"] == 1080
        assert tl["height"] == 1920

    def test_with_caption(self):
        tl = instagram_reel_template("/tmp/video.mp4", caption="Reel caption")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 1
        assert text_tracks[0]["elements"][0]["position"] == "bottom-center"


class TestYouTubeVideoTemplate:
    def test_basic_structure(self):
        tl = youtube_video_template("/tmp/video.mp4")
        assert tl["width"] == 1920
        assert tl["height"] == 1080

    def test_single_clip(self):
        tl = youtube_video_template("/tmp/video.mp4")
        video_tracks = [t for t in tl["tracks"] if t["type"] == "video"]
        assert len(video_tracks) == 1
        assert len(video_tracks[0]["clips"]) == 1

    def test_with_outro(self):
        tl = youtube_video_template("/tmp/video.mp4", outro_path="/tmp/outro.mp4")
        video_tracks = [t for t in tl["tracks"] if t["type"] == "video"]
        assert len(video_tracks[0]["clips"]) == 2
        assert video_tracks[0]["clips"][1]["source"] == "/tmp/outro.mp4"

    def test_with_title(self):
        tl = youtube_video_template("/tmp/video.mp4", title="My Video")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 1
        elem = text_tracks[0]["elements"][0]
        assert elem["text"] == "My Video"
        assert elem["position"] == "top-center"
        assert elem["duration"] == 3
        assert elem["style"]["size"] == 48

    def test_with_music(self):
        tl = youtube_video_template("/tmp/video.mp4", music_path="/tmp/music.mp3")
        audio_tracks = [t for t in tl["tracks"] if t["type"] == "audio"]
        assert len(audio_tracks) == 1
        assert audio_tracks[0]["clips"][0]["volume"] == 0.3


class TestInstagramPostTemplate:
    def test_basic_structure(self):
        tl = instagram_post_template("/tmp/video.mp4")
        assert tl["width"] == 1080
        assert tl["height"] == 1080

    def test_with_caption(self):
        tl = instagram_post_template("/tmp/video.mp4", caption="Post caption")
        text_tracks = [t for t in tl["tracks"] if t["type"] == "text"]
        assert len(text_tracks) == 1
        assert text_tracks[0]["elements"][0]["style"]["size"] == 32


class TestTemplatesRegistry:
    def test_has_5_entries(self):
        assert len(TEMPLATES) == 5

    def test_all_callable(self):
        for name, func in TEMPLATES.items():
            assert callable(func), f"{name} is not callable"

    def test_expected_templates(self):
        assert "tiktok" in TEMPLATES
        assert "youtube-shorts" in TEMPLATES
        assert "instagram-reel" in TEMPLATES
        assert "youtube" in TEMPLATES
        assert "instagram-post" in TEMPLATES

    def test_registry_functions_work(self):
        for name, func in TEMPLATES.items():
            tl = func("/tmp/test.mp4")
            assert "tracks" in tl, f"{name} template missing tracks"
            assert "width" in tl, f"{name} template missing width"
            assert "height" in tl, f"{name} template missing height"
