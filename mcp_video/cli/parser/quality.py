"""Quality CLI subcommands."""

from __future__ import annotations

import argparse


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add quality subcommands to the CLI parser."""
    # video-auto-chapters
    achap_p = subparsers.add_parser("video-auto-chapters", help="Auto-detect scene changes and create chapters")
    achap_p.add_argument("input", help="Input video file")
    achap_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Scene detection threshold (default: 0.3)")

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
