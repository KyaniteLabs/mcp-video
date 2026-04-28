"""Hyperframes CLI subcommands."""

from __future__ import annotations

import argparse


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add Hyperframes subcommands to the CLI parser."""
    # hyperframes-render
    hyperframes_render_p = subparsers.add_parser("hyperframes-render", help="Render a Hyperframes composition to video")
    hyperframes_render_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_render_p.add_argument("-o", "--output", help="Output video file path")
    hyperframes_render_p.add_argument("--fps", type=float, help="Frame rate (24, 30, 60)")
    hyperframes_render_p.add_argument("--width", type=int, help="Output width in pixels")
    hyperframes_render_p.add_argument("--height", type=int, help="Output height in pixels")
    hyperframes_render_p.add_argument(
        "--quality",
        default="standard",
        choices=["draft", "standard", "high"],
        help="Render quality (default: standard)",
    )
    hyperframes_render_p.add_argument(
        "--format", default="mp4", choices=["mp4", "webm", "mov"], help="Output format (default: mp4)"
    )
    hyperframes_render_p.add_argument("--workers", help="Parallel render workers (number or 'auto')")
    hyperframes_render_p.add_argument("--crf", type=int, help="Override encoder CRF")

    # hyperframes-compositions
    hyperframes_comps_p = subparsers.add_parser(
        "hyperframes-compositions", help="List compositions in a Hyperframes project"
    )
    hyperframes_comps_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_comps_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # hyperframes-preview
    hyperframes_preview_p = subparsers.add_parser("hyperframes-preview", help="Launch Hyperframes preview studio")
    hyperframes_preview_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_preview_p.add_argument("-p", "--port", type=int, default=3002, help="Preview port (default: 3002)")
    hyperframes_preview_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # hyperframes-still
    hyperframes_still_p = subparsers.add_parser("hyperframes-still", help="Render a single frame as image")
    hyperframes_still_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_still_p.add_argument("-o", "--output", help="Output image file path")
    hyperframes_still_p.add_argument("--frame", type=int, default=0, help="Frame number to render (default: 0)")

    # hyperframes-init
    hyperframes_init_p = subparsers.add_parser("hyperframes-init", help="Scaffold a new Hyperframes project")
    hyperframes_init_p.add_argument("name", help="Project name")
    hyperframes_init_p.add_argument("-d", "--output-dir", help="Output directory (default: current directory)")
    hyperframes_init_p.add_argument(
        "-t",
        "--template",
        default="blank",
        choices=["blank", "warm-grain", "swiss-grid"],
        help="Project template (default: blank)",
    )

    # hyperframes-add-block
    hyperframes_add_p = subparsers.add_parser(
        "hyperframes-add-block", help="Install a block from the Hyperframes catalog"
    )
    hyperframes_add_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_add_p.add_argument("block_name", help="Registry item name (e.g. claude-code-window, shader-wipe)")

    # hyperframes-validate
    hyperframes_validate_p = subparsers.add_parser("hyperframes-validate", help="Validate a Hyperframes project")
    hyperframes_validate_p.add_argument("project_path", help="Path to Hyperframes project")

    # hyperframes-pipeline
    hyperframes_pipeline_p = subparsers.add_parser("hyperframes-pipeline", help="Render + post-process in one step")
    hyperframes_pipeline_p.add_argument("project_path", help="Path to Hyperframes project")
    hyperframes_pipeline_p.add_argument("--post-process", required=True, help="Post-processing operations as JSON list")
    hyperframes_pipeline_p.add_argument("-o", "--output", help="Final output file path")
