"""Workflow-engine CLI subcommands."""

from __future__ import annotations

import argparse


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add workflow-engine subcommands to the CLI parser."""
    wf_validate = subparsers.add_parser(
        "workflow-validate",
        help="Validate a workflow job-spec without rendering any media",
    )
    wf_validate.add_argument("--spec", required=True, help="Path to the workflow job-spec JSON file")
