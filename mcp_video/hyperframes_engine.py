"""Hyperframes engine — subprocess wrappers calling npx hyperframes CLI.

No pip packages needed — Hyperframes is external (Node.js).

All file paths should be absolute. Output files are generated automatically
if no output_path is provided.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from collections.abc import Callable
from typing import Any

from .errors import (
    HyperframesNotFoundError,
    HyperframesProjectError,
    HyperframesRenderError,
    MCPVideoError,
)
from .ffmpeg_helpers import _validate_output_path
from .hyperframes_models import (
    CompositionInfo,
    CompositionsResult,
    HyperframesBlockResult,
    HyperframesPipelineResult,
    HyperframesPreviewResult,
    HyperframesProjectResult,
    HyperframesRenderResult,
    HyperframesStillResult,
    HyperframesValidationResult,
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_project_name(name: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        raise MCPVideoError(
            "Invalid name: must match ^[a-zA-Z0-9_-]+$",
            error_type="validation_error",
            code="invalid_parameter",
        )
    return name


def _require_hyperframes_deps() -> None:
    """Raise a helpful error if Node.js/npx are not available."""
    if shutil.which("node") is None:
        raise HyperframesNotFoundError("node not found on PATH")
    if shutil.which("npx") is None:
        raise HyperframesNotFoundError("npx not found on PATH")


def _find_entry_point(project: Path) -> Path:
    """Locate the Hyperframes entry point (index.html or any HTML with data-composition-id)."""
    for candidate in ["index.html", "composition.html", "demo.html"]:
        if (project / candidate).is_file():
            return project / candidate
    # Fallback: any HTML file
    for f in project.iterdir():
        if f.suffix == ".html" and f.is_file():
            return f
    raise HyperframesProjectError(str(project), "Could not find entry point (no .html file)")


def _validate_project(project_path: str) -> tuple[Path, Path]:
    """Check that the project directory has the expected structure.

    Returns (project_dir, entry_point) tuple.
    """
    p = Path(project_path).resolve()
    if not p.is_dir():
        raise HyperframesProjectError(str(p), "Directory does not exist")
    entry_point = _find_entry_point(p)
    return p, entry_point


def _run_hyperframes(
    args: list[str],
    cwd: str | Path,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    """Run an npx hyperframes command and return the CompletedProcess."""
    cmd = ["npx", "hyperframes", *args]
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise HyperframesRenderError(" ".join(cmd), -1, "Render timed out") from None
    except FileNotFoundError:
        raise HyperframesNotFoundError("npx command not found") from None


# ---------------------------------------------------------------------------
# Operation schema registry
# ---------------------------------------------------------------------------

_SCHEMA: dict[str, dict[str, Any]] = {
    "render": {
        "subcommand": "render",
        "positional": ["project_path"],
        "flags": {
            "output": "output_path",
            "fps": "fps",
            "quality": "quality",
            "format": "format",
            "workers": "workers",
            "crf": "crf",
        },
        "timeout": 600,
    },
    "compositions": {
        "subcommand": "compositions",
        "positional": ["project_path"],
        "fixed": ["--json"],
        "timeout": 60,
    },
    "snapshot": {
        "subcommand": "snapshot",
        "positional": ["project_path"],
        "fixed": ["--frames", "1"],
        "computed": {
            "at": lambda kw: str(kw.get("frame", 0) / 30.0),
        },
        "timeout": 120,
    },
    "add": {
        "subcommand": "add",
        "positional": ["block_name"],
        "flags": {
            "dir": "project_path",
        },
        "fixed": ["--json"],
        "timeout": 60,
    },
    "init": {
        "subcommand": "init",
        "positional": ["name"],
        "flags": {
            "example": "template",
        },
        "fixed": ["--non-interactive", "--skip-skills"],
        "cwd_key": "output_dir",
        "timeout": 120,
    },
    "lint": {
        "subcommand": "lint",
        "positional": ["project_path"],
        "fixed": ["--json"],
        "timeout": 60,
    },
}


def _hyperframes_op(
    operation: str,
    **kwargs: Any,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Run a hyperframes subcommand from the schema registry.

    Returns (completed_process, cwd_path).
    """
    spec = _SCHEMA.get(operation)
    if spec is None:
        raise MCPVideoError(
            f"Unknown hyperframes operation: {operation}",
            error_type="validation_error",
            code="invalid_parameter",
        )

    _require_hyperframes_deps()

    cwd_key = spec.get("cwd_key", "project_path")
    cwd_val = kwargs.get(cwd_key)
    if cwd_val is None:
        raise MCPVideoError(
            f"Missing required parameter: {cwd_key}",
            error_type="validation_error",
            code="invalid_parameter",
        )

    if cwd_key == "project_path":
        cwd, _entry_point = _validate_project(cwd_val)
    else:
        cwd = Path(cwd_val).resolve()

    args: list[str] = [spec["subcommand"]]

    for pos_key in spec.get("positional", []):
        val = kwargs.get(pos_key)
        if val is None:
            raise MCPVideoError(
                f"Missing required parameter: {pos_key}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        args.append(str(val))

    for flag, kw_key in spec.get("flags", {}).items():
        val = kwargs.get(kw_key)
        if val is not None:
            args.extend([f"--{flag}", str(val)])

    for item in spec.get("fixed", []):
        args.append(item)

    for flag, compute in spec.get("computed", {}).items():
        args.extend([f"--{flag}", str(compute(kwargs))])

    result = _run_hyperframes(args, cwd=cwd, timeout=spec.get("timeout", 600))
    if result.returncode != 0:
        raise HyperframesRenderError(" ".join(args), result.returncode, result.stderr)

    return result, cwd


def _post_process_ops() -> dict[str, Callable]:
    """Return the post-processing operation registry for render_and_post."""
    from . import engine as _video_engine

    return {
        "resize": _video_engine.resize,
        "convert": _video_engine.convert,
        "add_audio": _video_engine.add_audio,
        "normalize_audio": _video_engine.normalize_audio,
        "add_text": _video_engine.add_text,
        "fade": _video_engine.fade,
        "watermark": _video_engine.watermark,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render(
    project_path: str,
    output_path: str | None = None,
    fps: float | None = None,
    width: int | None = None,
    height: int | None = None,
    quality: str | None = None,
    format: str | None = None,
    workers: str | int | None = None,
    crf: int | None = None,
) -> HyperframesRenderResult:
    """Render a Hyperframes composition to video."""
    if output_path is None:
        os.makedirs("out", exist_ok=True)
        output_path = os.path.join("out", f"{Path(project_path).name}.mp4")

    start_time = time.time()
    _result, _project = _hyperframes_op(
        "render",
        project_path=project_path,
        output_path=output_path,
        fps=fps,
        quality=quality,
        format=format,
        workers=workers,
        crf=crf,
    )

    render_time = round(time.time() - start_time, 1)
    size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2) if os.path.isfile(output_path) else None

    resolution = None
    if width and height:
        resolution = f"{width}x{height}"

    if not os.path.isfile(output_path):
        return HyperframesRenderResult(
            output_path=output_path,
            codec=format or "h264",
            size_mb=None,
            render_time=render_time,
            resolution=resolution,
            success=False,
        )

    return HyperframesRenderResult(
        output_path=output_path,
        codec=format or "h264",
        size_mb=size_mb,
        render_time=render_time,
        resolution=resolution,
    )


def _parse_compositions_output(stdout: str) -> list[dict[str, Any]]:
    """Parse compositions from hyperframes CLI output (JSON or text format)."""
    # Try JSON first
    try:
        data = json.loads(stdout)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("compositions", [data])
    except json.JSONDecodeError:
        pass

    # Fallback: simple regex for text output
    comps = []
    pattern = re.compile(
        r"^(\S+)\s+(\d+)\s+(\d+)x(\d+)\s+(\d+)\s+\(.*\)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(stdout):
        comps.append(
            {
                "id": m.group(1),
                "fps": int(m.group(2)),
                "width": int(m.group(3)),
                "height": int(m.group(4)),
                "durationInFrames": int(m.group(5)),
                "defaultProps": {},
            }
        )
    return comps


def compositions(
    project_path: str,
) -> CompositionsResult:
    """List compositions in a Hyperframes project."""
    result, project = _hyperframes_op("compositions", project_path=project_path)

    raw = _parse_compositions_output(result.stdout)

    comp_list = []
    for c in raw:
        comp_list.append(
            CompositionInfo(
                id=c.get("id", c.get("compositionId", "")),
                width=c.get("width", 1920),
                height=c.get("height", 1080),
                fps=c.get("fps", 30),
                duration_in_frames=c.get("durationInFrames", c.get("duration", 0)),
                default_props=c.get("defaultProps", {}),
            )
        )

    return CompositionsResult(
        compositions=comp_list,
        project_path=str(project),
    )


def preview(
    project_path: str,
    port: int = 3002,
    startup_timeout: int = 10,
) -> HyperframesPreviewResult:
    """Launch Hyperframes preview studio (non-blocking)."""
    _require_hyperframes_deps()
    project, _entry_point = _validate_project(project_path)

    cmd = ["npx", "hyperframes", "preview", str(project), "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(project),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    time.sleep(min(startup_timeout, 2))
    if proc.poll() is not None:
        stderr = proc.stderr.read() if proc.stderr else ""
        raise HyperframesProjectError(f"Hyperframes preview exited immediately. stderr: {stderr[:500]}")

    return HyperframesPreviewResult(
        url=f"http://localhost:{port}",
        port=port,
        project_path=str(project),
        pid=proc.pid,
    )


def still(
    project_path: str,
    output_path: str | None = None,
    frame: int = 0,
) -> HyperframesStillResult:
    """Render a single frame from a Hyperframes composition."""
    if output_path is None:
        os.makedirs("out", exist_ok=True)
        output_path = os.path.join("out", f"{Path(project_path).name}_frame{frame}.png")

    _hyperframes_op("snapshot", project_path=project_path, frame=frame)

    return HyperframesStillResult(
        output_path=output_path,
        frame=frame,
    )


def create_project(
    name: str,
    output_dir: str | None = None,
    template: str = "blank",
) -> HyperframesProjectResult:
    """Scaffold a new Hyperframes project."""
    name = _validate_project_name(name)
    if output_dir is None:
        output_dir = os.getcwd()
    output_dir = _validate_output_path(output_dir)
    project_dir = Path(output_dir) / name
    _validate_output_path(str(project_dir))

    _require_hyperframes_deps()

    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"Warning: Project directory already exists and is not empty — files will be overwritten: {project_dir}")

    project_dir.mkdir(parents=True, exist_ok=True)

    _hyperframes_op(
        "init",
        name=name,
        template=template,
        output_dir=output_dir,
    )

    # Discover created files
    files: list[str] = []
    if project_dir.exists():
        for f in project_dir.rglob("*"):
            if f.is_file():
                files.append(str(f.relative_to(project_dir)))

    return HyperframesProjectResult(
        project_path=str(project_dir),
        template=template,
        files=files,
    )


def validate(
    project_path: str,
) -> HyperframesValidationResult:
    """Validate a Hyperframes project for rendering readiness."""
    issues: list[str] = []
    warnings: list[str] = []

    p = Path(project_path).resolve()

    if not p.is_dir():
        issues.append("Project directory does not exist")
        return HyperframesValidationResult(
            valid=False,
            issues=issues,
            warnings=warnings,
            project_path=str(p),
        )

    try:
        _find_entry_point(p)
    except HyperframesProjectError:
        issues.append("No HTML entry point found (expected index.html)")

    # Check Node.js/npx
    if shutil.which("node") is None:
        issues.append("Node.js not found on PATH")
    if shutil.which("npx") is None:
        issues.append("npx not found on PATH")

    # Run hyperframes lint if deps are available
    if shutil.which("npx") is not None:
        try:
            result = _run_hyperframes(["lint", str(p), "--json"], cwd=p, timeout=60)
            if result.returncode != 0:
                try:
                    lint_data = json.loads(result.stdout)
                    for finding in lint_data.get("errors", []):
                        issues.append(f"lint: {finding}")
                    for finding in lint_data.get("warnings", []):
                        warnings.append(f"lint: {finding}")
                except json.JSONDecodeError:
                    issues.append(f"lint failed: {result.stderr[:200]}")
        except Exception as e:
            warnings.append(f"Could not run hyperframes lint: {e}")

    valid = len(issues) == 0

    return HyperframesValidationResult(
        valid=valid,
        issues=issues,
        warnings=warnings,
        project_path=str(p),
    )


def add_block(
    project_path: str,
    block_name: str,
) -> HyperframesBlockResult:
    """Install a block from the Hyperframes catalog."""
    result, project = _hyperframes_op(
        "add",
        project_path=project_path,
        block_name=block_name,
    )

    files_added: list[str] = []
    try:
        add_data = json.loads(result.stdout)
        files_added = add_data.get("files", [])
    except json.JSONDecodeError:
        pass

    return HyperframesBlockResult(
        project_path=str(project),
        block_name=block_name,
        files_added=files_added,
    )


def render_and_post(
    project_path: str,
    post_process: list[dict[str, Any]],
    output_path: str | None = None,
) -> HyperframesPipelineResult:
    """Render a Hyperframes composition, then apply mcp-video post-processing."""
    # Step 1: Render with Hyperframes
    render_result = render(project_path)
    hyperframes_output = render_result.output_path

    # Step 2: Post-process with mcp-video engine
    op_map = _post_process_ops()

    operations: list[str] = []
    current_input = hyperframes_output

    for i, op in enumerate(post_process):
        op_type = op.get("op", op.get("type", ""))
        params = op.get("params", {})
        is_last = i == len(post_process) - 1

        if op_type not in op_map:
            raise MCPVideoError(
                f"Unknown post-processing operation: '{op_type}'. Valid operations: {', '.join(op_map)}",
                error_type="validation_error",
                code="invalid_parameter",
            )

        step_output = output_path if is_last else None
        result = op_map[op_type](current_input, output_path=step_output, **params)
        current_input = result.output_path
        operations.append(op_type)

    return HyperframesPipelineResult(
        hyperframes_output=hyperframes_output,
        final_output=current_input,
        operations=operations,
    )
