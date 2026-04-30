"""Tests for CLI parser modules."""

import argparse

import pytest


def _get_subparser_names(parser_module):
    """Return set of subparser names added by a parser module."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser_module.add_parsers(subparsers)
    return set(subparsers.choices.keys())


class TestParserCore:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import core

        names = _get_subparser_names(core)
        expected = {
            "doctor", "info", "extract-frame", "trim", "merge",
            "edit", "blur", "color-grade", "template", "templates",
            "video-extract-frame",
        }
        assert expected <= names


class TestParserMedia:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import media

        names = _get_subparser_names(media)
        expected = {
            "convert", "crop", "extract-audio", "fade", "preview",
            "resize", "rotate", "speed", "storyboard", "subtitles",
            "thumbnail", "export",
        }
        assert expected <= names


class TestParserAdvanced:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import advanced

        names = _get_subparser_names(advanced)
        expected = {
            "apply-mask", "batch", "compare-quality", "create-from-images",
            "detect-scenes", "export-frames", "generate-subtitles",
            "read-metadata", "stabilize", "write-metadata", "audio-waveform",
        }
        assert expected <= names


class TestParserAI:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import ai

        names = _get_subparser_names(ai)
        expected = {
            "video-ai-transcribe", "video-analyze", "video-ai-upscale",
            "video-ai-stem-separation", "video-ai-scene-detect",
            "video-ai-color-grade", "video-ai-remove-silence",
        }
        assert expected <= names


class TestParserAudio:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import audio

        names = _get_subparser_names(audio)
        expected = {
            "audio-synthesize", "audio-compose", "audio-preset",
            "audio-sequence", "audio-effects",
            "video-add-generated-audio", "video-audio-spatial",
            "normalize-audio",
        }
        assert expected <= names


class TestParserEffects:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import effects

        names = _get_subparser_names(effects)
        expected = {
            "effect-vignette", "effect-glow", "effect-noise",
            "effect-scanlines", "effect-chromatic-aberration",
            "add-text", "add-audio", "chroma-key", "filter",
            "overlay-video", "reverse", "split-screen",
            "transition-glitch", "transition-morph", "transition-pixelate",
            "watermark",
        }
        assert expected <= names


class TestParserLayout:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import layout

        names = _get_subparser_names(layout)
        expected = {
            "video-layout-grid", "video-layout-pip",
            "video-mograph-count", "video-mograph-progress", "video-text-animated",
        }
        assert expected <= names


class TestParserImage:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import image

        names = _get_subparser_names(image)
        expected = {
            "image-extract-colors", "image-generate-palette",
            "image-analyze-product",
        }
        assert expected <= names


class TestParserHyperframes:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import hyperframes

        names = _get_subparser_names(hyperframes)
        expected = {
            "hyperframes-render", "hyperframes-compositions",
            "hyperframes-preview", "hyperframes-still", "hyperframes-init",
            "hyperframes-add-block", "hyperframes-validate", "hyperframes-pipeline",
        }
        assert expected <= names


class TestParserQuality:
    def test_adds_expected_parsers(self):
        from mcp_video.cli.parser import quality

        names = _get_subparser_names(quality)
        expected = {
            "video-auto-chapters", "video-info-detailed",
            "video-quality-check", "video-design-quality-check",
            "video-fix-design-issues",
        }
        assert expected <= names


class TestParserInit:
    def test_build_parser_returns_parser(self):
        from mcp_video.cli.parser import build_parser

        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
