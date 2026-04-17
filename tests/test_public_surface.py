"""Characterization tests for public import and command surfaces."""

import re
import subprocess
import sys
import asyncio


EXPECTED_CLI_COMMANDS = {
    "doctor",
    "info",
    "extract-frame",
    "trim",
    "merge",
    "add-text",
    "add-audio",
    "resize",
    "speed",
    "convert",
    "thumbnail",
    "preview",
    "storyboard",
    "subtitles",
    "watermark",
    "crop",
    "rotate",
    "fade",
    "export",
    "extract-audio",
    "edit",
    "filter",
    "blur",
    "reverse",
    "chroma-key",
    "color-grade",
    "normalize-audio",
    "overlay-video",
    "split-screen",
    "batch",
    "detect-scenes",
    "create-from-images",
    "export-frames",
    "compare-quality",
    "read-metadata",
    "write-metadata",
    "stabilize",
    "apply-mask",
    "audio-waveform",
    "generate-subtitles",
    "templates",
    "template",
    "remotion-render",
    "remotion-compositions",
    "remotion-studio",
    "remotion-still",
    "remotion-create",
    "remotion-scaffold",
    "remotion-validate",
    "remotion-pipeline",
    "effect-vignette",
    "effect-glow",
    "effect-noise",
    "effect-scanlines",
    "effect-chromatic-aberration",
    "transition-glitch",
    "transition-morph",
    "transition-pixelate",
    "video-ai-transcribe",
    "video-analyze",
    "video-ai-upscale",
    "video-ai-stem-separation",
    "video-ai-scene-detect",
    "video-ai-color-grade",
    "video-ai-remove-silence",
    "audio-synthesize",
    "audio-compose",
    "audio-preset",
    "audio-sequence",
    "audio-effects",
    "video-text-animated",
    "video-mograph-count",
    "video-mograph-progress",
    "video-layout-grid",
    "video-layout-pip",
    "video-add-generated-audio",
    "video-audio-spatial",
    "video-auto-chapters",
    "video-extract-frame",
    "video-info-detailed",
    "video-quality-check",
    "video-design-quality-check",
    "video-fix-design-issues",
    "image-extract-colors",
    "image-generate-palette",
    "image-analyze-product",
}

EXPECTED_SERVER_TOOLS = {
    "video_info",
    "video_trim",
    "video_merge",
    "video_add_text",
    "video_add_audio",
    "video_resize",
    "video_convert",
    "video_speed",
    "video_thumbnail",
    "video_preview",
    "video_storyboard",
    "video_subtitles",
    "video_watermark",
    "video_export",
    "video_crop",
    "video_rotate",
    "video_fade",
    "video_edit",
    "video_extract_audio",
    "video_filter",
    "video_reverse",
    "video_chroma_key",
    "video_blur",
    "video_color_grade",
    "video_normalize_audio",
    "video_overlay",
    "video_split_screen",
    "video_batch",
    "video_detect_scenes",
    "video_create_from_images",
    "video_export_frames",
    "video_generate_subtitles",
    "video_compare_quality",
    "video_read_metadata",
    "video_write_metadata",
    "video_stabilize",
    "video_apply_mask",
    "video_audio_waveform",
    "video_extract_frame",
    "remotion_render",
    "remotion_compositions",
    "remotion_studio",
    "remotion_still",
    "remotion_create_project",
    "remotion_scaffold_template",
    "remotion_validate",
    "remotion_to_mcpvideo",
    "audio_synthesize",
    "audio_preset",
    "audio_sequence",
    "audio_compose",
    "audio_effects",
    "video_add_generated_audio",
    "effect_vignette",
    "effect_chromatic_aberration",
    "effect_scanlines",
    "effect_noise",
    "effect_glow",
    "video_text_animated",
    "video_text_subtitles",
    "video_mograph_count",
    "video_mograph_progress",
    "video_layout_grid",
    "video_layout_pip",
    "video_auto_chapters",
    "video_info_detailed",
    "transition_glitch",
    "transition_pixelate",
    "transition_morph",
    "video_ai_remove_silence",
    "video_ai_transcribe",
    "video_analyze",
    "video_ai_scene_detect",
    "video_ai_stem_separation",
    "video_ai_upscale",
    "video_ai_color_grade",
    "video_audio_spatial",
    "video_quality_check",
    "video_design_quality_check",
    "video_fix_design_issues",
    "image_extract_colors",
    "image_generate_palette",
    "image_analyze_product",
}


def test_cli_help_lists_all_commands():
    result = subprocess.run(
        [sys.executable, "-m", "mcp_video", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    command_lists = re.findall(r"\{([^}]+)\}", result.stdout)
    command_list = max(command_lists, key=lambda value: len(value.split(",")))
    help_commands = set(command_list.split(","))

    assert help_commands == EXPECTED_CLI_COMMANDS
    assert len(EXPECTED_CLI_COMMANDS) == 86


def test_server_tool_registry_keeps_public_tool_names():
    from mcp_video.server import mcp

    tool_names = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert tool_names >= EXPECTED_SERVER_TOOLS
    assert len(tool_names) == 83


def test_server_module_reexports_resource_and_tool_functions():
    import mcp_video.server as server

    for name in [
        "_error_result",
        "_result",
        "templates_resource",
        "video_info_resource",
        "video_preview_resource",
        "video_audio_resource",
        "video_trim",
        "video_analyze",
        "remotion_render",
        "image_analyze_product",
    ]:
        assert hasattr(server, name)


def test_engine_module_preserves_legacy_import_targets():
    import mcp_video.engine as engine

    for name in [
        "_check_filter_available",
        "_escape_ffmpeg_filter_value",
        "_generate_thumbnail_base64",
        "_get_color_preset_filter",
        "_parse_ffmpeg_time",
        "_run_ffmpeg_with_progress",
        "_validate_color",
        "_validate_input",
        "_validate_position",
        "add_text",
        "convert",
        "resize",
        "trim",
        "video_batch",
    ]:
        assert hasattr(engine, name)
