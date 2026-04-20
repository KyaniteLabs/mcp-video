"""Remotion engine — subprocess wrappers calling npx remotion CLI.

No pip packages needed — Remotion is external (Node.js). Follows the exact
pattern used by image_engine.py.

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
from typing import Any

from .errors import (
    MCPVideoError,
    RemotionNotFoundError,
    RemotionProjectError,
    RemotionRenderError,
)
from .remotion_models import (
    CompositionInfo,
    CompositionsResult,
    RemotionPipelineResult,
    RemotionProjectResult,
    RemotionRenderResult,
    RemotionStudioResult,
    RemotionStillResult,
    RemotionValidationResult,
    ScaffoldResult,
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _require_remotion_deps() -> None:
    """Raise a helpful error if Node.js/npx are not available."""
    if shutil.which("node") is None:
        raise RemotionNotFoundError("node not found on PATH")
    if shutil.which("npx") is None:
        raise RemotionNotFoundError("npx not found on PATH")


def _find_entry_point(project: Path) -> Path:
    """Locate the Remotion entry point (file that calls registerRoot)."""
    # Common entry point locations
    for candidate in ["src/index.ts", "src/index.tsx", "src/root.ts", "src/root.tsx"]:
        if (project / candidate).is_file():
            return project / candidate
    # Fallback: search for registerRoot in src/
    src_dir = project / "src"
    if src_dir.is_dir():
        for f in src_dir.iterdir():
            if f.suffix in (".ts", ".tsx") and f.is_file():
                try:
                    content = f.read_text()
                    if "registerRoot" in content:
                        return f
                except (PermissionError, UnicodeDecodeError):
                    pass
    raise RemotionProjectError(str(project), "Could not find entry point (file with registerRoot)")


def _validate_project(project_path: str) -> tuple[Path, Path]:
    """Check that the project directory has the expected structure.

    Returns (project_dir, entry_point) tuple.
    """
    p = Path(project_path).resolve()
    if not p.is_dir():
        raise RemotionProjectError(str(p), "Directory does not exist")
    if not (p / "package.json").is_file():
        raise RemotionProjectError(str(p), "Missing package.json")
    src_root = p / "src" / "Root.tsx"
    if not src_root.is_file():
        raise RemotionProjectError(str(p), "Missing src/Root.tsx")
    entry_point = _find_entry_point(p)
    return p, entry_point


def _run_remotion(
    args: list[str],
    cwd: str | Path,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    """Run an npx remotion command and return the CompletedProcess."""
    cmd = ["npx", "remotion", *args]
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RemotionRenderError(" ".join(cmd), -1, "Render timed out") from None
    except FileNotFoundError:
        raise RemotionNotFoundError("npx command not found") from None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render(
    project_path: str,
    composition_id: str,
    output_path: str | None = None,
    codec: str = "h264",
    crf: int | None = None,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
    concurrency: int | None = None,
    frames: str | None = None,
    props: dict[str, Any] | None = None,
    scale: float | None = None,
) -> RemotionRenderResult:
    """Render a Remotion composition to video."""
    _require_remotion_deps()
    project, entry_point = _validate_project(project_path)

    if output_path is None:
        os.makedirs("out", exist_ok=True)
        output_path = os.path.join("out", f"{composition_id}.mp4")

    args = [
        "render",
        str(entry_point),
        composition_id,
        output_path,
        "--codec",
        codec,
    ]
    if crf is not None:
        args += ["--crf", str(crf)]
    if width is not None:
        args += ["--width", str(width)]
    if height is not None:
        args += ["--height", str(height)]
    if fps is not None:
        args += ["--fps", str(fps)]
    if concurrency is not None:
        args += ["--concurrency", str(concurrency)]
    if frames is not None:
        if not re.match(r"^\d+-\d+$", frames):
            raise MCPVideoError(
                f"Invalid frames format: '{frames}'. Expected format: 'START-END' (e.g. '0-90')",
                error_type="validation_error",
                code="invalid_parameter",
            )
        args += ["--frames", frames]
    if scale is not None:
        args += ["--scale", str(scale)]
    if props is not None:
        props_json = json.dumps(props)
        if len(props_json) > 100_000:  # 100 KiB — well under OS arg limits
            raise MCPVideoError(
                f"Props JSON is {len(props_json)} bytes — exceeds 100 KiB limit. "
                "Use a file-based approach for large props.",
                error_type="validation_error",
                code="props_too_large",
            )
        args += ["--props", props_json]

    start_time = time.time()
    result = _run_remotion(args, cwd=project)

    if result.returncode != 0:
        raise RemotionRenderError(" ".join(args), result.returncode, result.stderr)

    render_time = round(time.time() - start_time, 1)
    size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2) if os.path.isfile(output_path) else None

    resolution = None
    if width and height:
        resolution = f"{width}x{height}"

    if not os.path.isfile(output_path):
        return RemotionRenderResult(
            output_path=output_path,
            codec=codec,
            size_mb=None,
            render_time=render_time,
            resolution=resolution,
            success=False,
        )

    return RemotionRenderResult(
        output_path=output_path,
        codec=codec,
        size_mb=size_mb,
        render_time=render_time,
        resolution=resolution,
    )


def _parse_compositions_output(stdout: str) -> list[dict[str, Any]]:
    """Parse compositions from remotion CLI output (JSON or text format)."""
    # Try JSON first (some Remotion versions support --json)
    try:
        data = json.loads(stdout)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("compositions", [data])
    except json.JSONDecodeError:
        pass

    # Fallback: parse text format like:
    # McpVideoExplainer    30      1920x1080      1500 (50.00 sec)
    comps = []
    # Match lines with: Name  fps  WxH  frames (duration)
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
    composition_id: str | None = None,
) -> CompositionsResult:
    """List compositions in a Remotion project."""
    _require_remotion_deps()
    project, entry_point = _validate_project(project_path)

    args = ["compositions", str(entry_point)]
    if composition_id:
        args += ["--composition", composition_id]

    result = _run_remotion(args, cwd=project, timeout=60)

    if result.returncode != 0:
        raise RemotionRenderError(" ".join(args), result.returncode, result.stderr)

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


def studio(
    project_path: str,
    port: int = 3000,
) -> RemotionStudioResult:
    """Launch Remotion Studio for live preview (non-blocking)."""
    _require_remotion_deps()
    project, entry_point = _validate_project(project_path)

    cmd = ["npx", "remotion", "studio", str(entry_point), "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(project),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return RemotionStudioResult(
        url=f"http://localhost:{port}",
        port=port,
        project_path=str(project),
        pid=proc.pid,
    )


def still(
    project_path: str,
    composition_id: str,
    output_path: str | None = None,
    frame: int = 0,
    image_format: str = "png",
) -> RemotionStillResult:
    """Render a single frame from a Remotion composition."""
    _require_remotion_deps()
    project, entry_point = _validate_project(project_path)

    if output_path is None:
        ext = "jpg" if image_format == "jpeg" else image_format
        os.makedirs("out", exist_ok=True)
        output_path = os.path.join("out", f"{composition_id}_frame{frame}.{ext}")

    args = [
        "still",
        str(entry_point),
        composition_id,
        output_path,
        "--frame",
        str(frame),
        "--image-format",
        image_format,
    ]

    result = _run_remotion(args, cwd=project, timeout=120)

    if result.returncode != 0:
        raise RemotionRenderError(" ".join(args), result.returncode, result.stderr)

    return RemotionStillResult(
        output_path=output_path,
        frame=frame,
    )


# ---------------------------------------------------------------------------
# Template scaffolding helpers
# ---------------------------------------------------------------------------

_CONSTANTS_TSX = """// Design tokens — edit these values to customize appearance
export const PRIMARY_COLOR = "{primary_color}";
export const SECONDARY_COLOR = "{secondary_color}";
export const BACKGROUND_COLOR = "{background_color}";
export const HEADING_FONT = "{heading_font}";
export const BODY_FONT = "{body_font}";
export const TARGET_FPS = {target_fps};
export const TARGET_DURATION = {target_duration};
"""

_ROOT_TSX = """import {{ Composition }} from "remotion";
import React from "react";
import {{ {slug}Composition }} from "./compositions/{slug}";

export const RemotionRoot: React.FC = () => {{
  return (
    <>
      <Composition
        id="{slug}"
        component={{{slug}Composition}}
        durationInFrames={{{target_fps} * {target_duration}}}
        fps={{{target_fps}}}
        compositionWidth={{1920}}
        compositionHeight={{1080}}
      />
    </>
  );
}};
"""

_COMPOSITION_TSX = """import React from "react";
import {{ AbsoluteFill, useCurrentFrame, interpolate }} from "remotion";
import {{ PRIMARY_COLOR, TARGET_FPS }} from "../constants";

interface Props {{
  title?: string;
  subtitle?: string;
}}

const {slug}Composition: React.FC<Props> = ({{ title, subtitle }}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], {{ extrapolateRight: "clamp" }});

  return (
    <AbsoluteFill
      style={{{{ backgroundColor: PRIMARY_COLOR, justifyContent: "center", alignItems: "center" }}}}
    >
      <div style={{{{ opacity, fontSize: 64, fontWeight: "bold", color: "white" }}}}>
        {{title || "{slug}"}}
      </div>
      {{subtitle && (
        <div style={{{{ opacity, fontSize: 32, color: "white", marginTop: 16 }}}}>
          {{subtitle}}
        </div>
      )}}
    </AbsoluteFill>
  );
}};

export default {slug}Composition;
"""

_PACKAGE_JSON = """{{
  "name": "{name}",
  "version": "1.0.0",
  "private": true,
  "scripts": {{
    "studio": "remotion studio",
    "render": "remotion render",
    "build": "remotion render src/index.ts {{name}} out/video.mp4"
  }},
  "dependencies": {{
    "react": "^18",
    "react-dom": "^18",
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0",
    "@remotion/player": "^4.0.0"
  }},
  "devDependencies": {{
    "@remotion/eslint-config": "^4.0.0",
    "@types/react": "^18",
    "typescript": "^5"
  }}
}}
"""

_TS_CONFIG = """{{
  "compilerOptions": {{
    "target": "ES2018",
    "module": "commonjs",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src"
  }},
  "include": ["src/**/*"]
}}
"""

_HELLO_WORLD_TSX = """import React from "react";
import {{ AbsoluteFill, useCurrentFrame, interpolate, spring }} from "remotion";

export const HelloWorld: React.FC = () => {{
  const frame = useCurrentFrame();
  const scale = spring({{ frame, fps: 30, config: {{ damping: 200 }} }});
  const opacity = interpolate(frame, [0, 30], [0, 1], {{ extrapolateRight: "clamp" }});

  return (
    <AbsoluteFill
      style={{{{ backgroundColor: "#0b1215", justifyContent: "center", alignItems: "center" }}}}
    >
      <div
        style={{{{
          opacity,
          transform: `scale(${{scale}})`,
          fontSize: 80,
          fontWeight: "bold",
          color: "white",
        }}}}
      >
        Hello, Remotion!
      </div>
    </AbsoluteFill>
  );
}};
"""


def create_project(
    name: str,
    output_dir: str | None = None,
    template: str = "blank",
) -> RemotionProjectResult:
    """Scaffold a new Remotion project."""
    _require_remotion_deps()

    if output_dir is None:
        output_dir = os.getcwd()
    project_dir = Path(output_dir) / name

    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"Warning: Project directory already exists and is not empty — files will be overwritten: {project_dir}")

    project_dir.mkdir(parents=True, exist_ok=True)

    files: list[str] = []

    # package.json
    pkg_content = _PACKAGE_JSON.format(name=name)
    (project_dir / "package.json").write_text(pkg_content)
    files.append("package.json")

    # tsconfig.json
    (project_dir / "tsconfig.json").write_text(_TS_CONFIG)
    files.append("tsconfig.json")

    # src directory
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # src/index.ts (entry point)
    index_ts = 'import { registerRoot } from "remotion";\nimport { RemotionRoot } from "./Root";\nregisterRoot(RemotionRoot);\n'
    (src_dir / "index.ts").write_text(index_ts)
    files.append("src/index.ts")

    if template == "hello-world":
        # Create a hello-world composition
        (src_dir / "HelloWorld.tsx").write_text(_HELLO_WORLD_TSX)
        files.append("src/HelloWorld.tsx")

        root_content = """import { Composition } from "remotion";
import React from "react";
import { HelloWorld } from "./HelloWorld";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        compositionWidth={1920}
        compositionHeight={1080}
      />
    </>
  );
};
"""
        (src_dir / "Root.tsx").write_text(root_content)
        files.append("src/Root.tsx")
    else:
        # Blank template — minimal Root.tsx
        root_content = """import { Composition } from "remotion";
import React from "react";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Add your compositions here */}
    </>
  );
};
"""
        (src_dir / "Root.tsx").write_text(root_content)
        files.append("src/Root.tsx")

    # Run npm install
    try:
        npm_result = subprocess.run(
            ["npm", "install"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if npm_result.returncode != 0:
            print(f"Warning: npm install failed: {npm_result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("Warning: npm install timed out after 120 seconds")
    except FileNotFoundError:
        print("Warning: npm not found — skipping install. Run 'npm install' manually.")

    return RemotionProjectResult(
        project_path=str(project_dir),
        template=template,
        files=files,
    )


def scaffold_template(
    project_path: str,
    spec: dict[str, Any],
    slug: str,
) -> ScaffoldResult:
    """Generate a generic composition from a spec."""
    # Sanitize slug — only alphanumeric, dashes, underscores
    import re

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
        raise RemotionProjectError(
            project_path,
            f"Invalid slug '{slug}': must contain only alphanumeric characters, dashes, and underscores",
        )

    # Validate color values (hex format only)
    for color_key in ("primary_color", "secondary_color", "background_color"):
        color_val = spec.get(color_key, "")
        if color_val and not re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(color_val)):
            raise RemotionProjectError(
                project_path,
                f"Invalid {color_key} '{color_val}': must be a hex color (e.g. #1a1a2e)",
            )

    # Sanitize font names — alphanumeric + spaces only
    for font_key in ("heading_font", "body_font"):
        font_val = spec.get(font_key, "")
        if font_val and not re.fullmatch(r"[a-zA-Z0-9\s+-]+", str(font_val)):
            raise RemotionProjectError(
                project_path,
                f"Invalid {font_key} '{font_val}': must contain only alphanumeric characters and spaces",
            )

    _require_remotion_deps()
    project = Path(project_path).resolve()

    if not project.is_dir():
        raise RemotionProjectError(str(project), "Directory does not exist")

    # Extract spec values with defaults
    primary_color = spec.get("primary_color", "#1a1a2e")
    secondary_color = spec.get("secondary_color", "#16213e")
    background_color = spec.get("background_color", "#0f3460")
    heading_font = spec.get("heading_font", "Arial")
    body_font = spec.get("body_font", "Arial")
    target_fps = spec.get("target_fps", 30)
    target_duration = spec.get("target_duration", 5)

    files: list[str] = []

    # src/constants.ts
    src_dir = project / "src"
    src_dir.mkdir(exist_ok=True)

    constants_content = _CONSTANTS_TSX.format(
        primary_color=primary_color,
        secondary_color=secondary_color,
        background_color=background_color,
        heading_font=heading_font,
        body_font=body_font,
        target_fps=target_fps,
        target_duration=target_duration,
    )
    (src_dir / "constants.ts").write_text(constants_content)
    files.append("src/constants.ts")

    # src/compositions/ directory
    comp_dir = src_dir / "compositions"
    comp_dir.mkdir(exist_ok=True)

    # Composition TSX
    comp_content = _COMPOSITION_TSX.format(slug=slug)
    comp_file = comp_dir / f"{slug}.tsx"
    comp_file.write_text(comp_content)
    files.append(f"src/compositions/{slug}.tsx")

    # Update or create Root.tsx
    root_content = _ROOT_TSX.format(slug=slug, target_fps=target_fps, target_duration=target_duration)
    (src_dir / "Root.tsx").write_text(root_content)
    files.append("src/Root.tsx")

    return ScaffoldResult(
        project_path=str(project),
        slug=slug,
        files=files,
    )


def validate(
    project_path: str,
    composition_id: str | None = None,
) -> RemotionValidationResult:
    """Validate a Remotion project for rendering readiness."""
    issues: list[str] = []
    warnings: list[str] = []

    p = Path(project_path).resolve()

    if not p.is_dir():
        issues.append("Project directory does not exist")
        return RemotionValidationResult(
            valid=False,
            issues=issues,
            warnings=warnings,
            project_path=str(p),
        )

    if not (p / "package.json").is_file():
        issues.append("Missing package.json")

    if not (p / "src" / "Root.tsx").is_file():
        issues.append("Missing src/Root.tsx")

    # Check for node_modules
    if not (p / "node_modules").is_dir():
        warnings.append("node_modules not found — run npm install")

    # Check for tsconfig
    if not (p / "tsconfig.json").is_file():
        warnings.append("Missing tsconfig.json")

    # Check Node.js/npx
    if shutil.which("node") is None:
        issues.append("Node.js not found on PATH")
    if shutil.which("npx") is None:
        issues.append("npx not found on PATH")

    valid = len(issues) == 0

    return RemotionValidationResult(
        valid=valid,
        issues=issues,
        warnings=warnings,
        project_path=str(p),
    )


def render_and_post(
    project_path: str,
    composition_id: str,
    post_process: list[dict[str, Any]],
    output_path: str | None = None,
) -> RemotionPipelineResult:
    """Render a Remotion composition, then apply mcp-video post-processing."""
    # Step 1: Render with Remotion
    render_result = render(project_path, composition_id)
    remotion_output = render_result.output_path

    # Step 2: Post-process with mcp-video engine
    from . import engine as video_engine

    operations: list[str] = []
    current_input = remotion_output

    op_map = {
        "resize": video_engine.resize,
        "convert": video_engine.convert,
        "add_audio": video_engine.add_audio,
        "normalize_audio": video_engine.normalize_audio,
        "add_text": video_engine.add_text,
        "fade": video_engine.fade,
        "watermark": video_engine.watermark,
    }

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

    return RemotionPipelineResult(
        remotion_output=remotion_output,
        final_output=current_input,
        operations=operations,
    )
