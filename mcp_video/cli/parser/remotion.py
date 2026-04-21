"""Remotion CLI subcommands."""

from __future__ import annotations

import argparse


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add remotion subcommands to the CLI parser."""
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

