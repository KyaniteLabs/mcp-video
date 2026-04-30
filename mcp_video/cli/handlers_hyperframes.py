"""CLI handlers for Hyperframes commands."""

from __future__ import annotations

from typing import Any

from .common import _parse_json_arg, _with_spinner
from .formatting import (
    _format_hyperframes_add_block,
    _format_hyperframes_compositions,
    _format_hyperframes_init,
    _format_hyperframes_pipeline,
    _format_hyperframes_preview,
    _format_hyperframes_render,
    _format_hyperframes_still,
    _format_hyperframes_validate,
)
from .runner import CommandRunner, _out


def handle_hyperframes_commands(args: Any, *, use_json: bool) -> bool:
    """Handle Hyperframes commands extracted from the main dispatcher."""
    runner = CommandRunner(args, use_json)

    def _render(a, j):
        from ..hyperframes_engine import render

        r = _with_spinner(
            f"Rendering {a.project_path}...",
            render,
            a.project_path,
            output_path=a.output,
            fps=a.fps,
            width=a.width,
            height=a.height,
            quality=a.quality,
            format=a.format,
            workers=a.workers,
            crf=a.crf,
        )
        _out(r, j, lambda res: _format_hyperframes_render(res, a.project_path))

    runner.register("hyperframes-render", _render)

    def _compositions(a, j):
        from ..hyperframes_engine import compositions

        r = _with_spinner("Listing compositions...", compositions, a.project_path)
        _out(
            r,
            j,
            lambda res: _format_hyperframes_compositions(res, a.project_path),
            json_transform=lambda r: r.model_dump() if hasattr(r, "model_dump") else r,
        )

    runner.register("hyperframes-compositions", _compositions)

    def _preview(a, j):
        from ..hyperframes_engine import preview

        r = _with_spinner("Launching Hyperframes preview...", preview, a.project_path, port=a.port)
        _out(
            r,
            j,
            _format_hyperframes_preview,
            json_transform=lambda r: r.model_dump() if hasattr(r, "model_dump") else r,
        )

    runner.register("hyperframes-preview", _preview)

    def _still(a, j):
        from ..hyperframes_engine import still

        r = _with_spinner(
            f"Rendering still frame {a.frame}...", still, a.project_path, output_path=a.output, frame=a.frame
        )
        _out(r, j, lambda res: _format_hyperframes_still(res, a.project_path))

    runner.register("hyperframes-still", _still)

    def _init(a, j):
        from ..hyperframes_engine import create_project

        r = _with_spinner(
            f"Creating project '{a.name}'...", create_project, a.name, output_dir=a.output_dir, template=a.template
        )
        _out(r, j, _format_hyperframes_init)

    runner.register("hyperframes-init", _init)

    def _add_block(a, j):
        from ..hyperframes_engine import add_block

        r = _with_spinner(f"Adding block '{a.block_name}'...", add_block, a.project_path, a.block_name)
        _out(r, j, _format_hyperframes_add_block)

    runner.register("hyperframes-add-block", _add_block)

    def _validate(a, j):
        from ..hyperframes_engine import validate

        r = _with_spinner("Validating project...", validate, a.project_path)
        _out(r, j, _format_hyperframes_validate)

    runner.register("hyperframes-validate", _validate)

    def _pipeline(a, j):
        from ..hyperframes_engine import render_and_post

        post_process = _parse_json_arg(a.post_process, "post-process", json_mode=j)
        r = _with_spinner(
            f"Running pipeline for {a.project_path}...",
            render_and_post,
            a.project_path,
            post_process=post_process,
            output_path=a.output,
        )
        _out(r, j, lambda res: _format_hyperframes_pipeline(res, a.project_path))

    runner.register("hyperframes-pipeline", _pipeline)

    return runner.dispatch()
