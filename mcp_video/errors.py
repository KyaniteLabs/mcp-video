"""mcp-video error types with auto-fix suggestions."""

from __future__ import annotations

from typing import Any


class MCPVideoError(Exception):
    """Base error for all mcp-video operations."""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown_error",
        code: str = "unknown",
        suggested_action: dict[str, Any] | None = None,
        docs_url: str | None = None,
    ):
        self.error_type = error_type
        self.code = code
        self.suggested_action = suggested_action
        self.docs_url = docs_url
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.error_type,
            "code": self.code,
            "message": str(self),
        }
        if self.suggested_action:
            result["suggested_action"] = self.suggested_action
        if self.docs_url:
            result["documentation_url"] = self.docs_url
        return result


class FFmpegNotFoundError(MCPVideoError):
    """FFmpeg is not installed or not on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "FFmpeg not found. Install it with: brew install ffmpeg (macOS), "
            "apt install ffmpeg (Ubuntu), or download from https://ffmpeg.org",
            error_type="dependency_error",
            code="ffmpeg_not_found",
            suggested_action={
                "auto_fix": False,
                "description": "Install FFmpeg before using mcp-video",
            },
        )


class FFprobeNotFoundError(MCPVideoError):
    """FFprobe is not installed or not on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "FFprobe not found. It should be installed alongside FFmpeg.",
            error_type="dependency_error",
            code="ffprobe_not_found",
        )


class InputFileError(MCPVideoError):
    """Input file doesn't exist or is not a valid video."""

    def __init__(self, path: str, reason: str = "File not found") -> None:
        super().__init__(
            f"Input file error: {path} — {reason}",
            error_type="input_error",
            code="invalid_input",
            suggested_action={
                "auto_fix": False,
                "description": "Check that the file exists and is a valid video file.",
            },
        )


class CodecError(MCPVideoError):
    """Unsupported or incompatible codec."""

    def __init__(self, codec: str, detail: str = "") -> None:
        super().__init__(
            f"Codec error: {codec}" + (f" — {detail}" if detail else ""),
            error_type="encoding_error",
            code="unsupported_codec",
            suggested_action={
                "auto_fix": True,
                "description": f"Auto-convert input from {codec} to H.264/AAC before editing",
            },
            docs_url="https://github.com/pastorsimon1798/mcp-video#codec-compatibility",
        )


class HyperframesNotFoundError(MCPVideoError):
    """Hyperframes CLI or Node.js not found on PATH."""

    def __init__(self, detail: str = "") -> None:
        msg = "Hyperframes requires Node.js 22+ and npx. Install Node.js from https://nodejs.org"
        if detail:
            msg += f" — {detail}"
        super().__init__(
            msg,
            error_type="dependency_error",
            code="hyperframes_not_found",
            suggested_action={
                "auto_fix": False,
                "description": "Install Node.js (v22+) and ensure npx is on PATH, then run: npx hyperframes --version",
            },
        )


class HyperframesProjectError(MCPVideoError):
    """Invalid Hyperframes project structure."""

    def __init__(self, path: str, reason: str = "Invalid project") -> None:
        super().__init__(
            f"Hyperframes project error: {path} — {reason}",
            error_type="project_error",
            code="invalid_hyperframes_project",
            suggested_action={
                "auto_fix": False,
                "description": "Ensure the project has an index.html with a data-composition-id root element.",
            },
        )


class HyperframesRenderError(MCPVideoError):
    """Hyperframes render failure."""

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        stderr_short = stderr[-500:] if len(stderr) > 500 else stderr
        super().__init__(
            f"Hyperframes render failed (exit code {returncode}): {stderr_short}",
            error_type="render_error",
            code=f"hyperframes_exit_{returncode}",
        )
        self.command = command
        self.returncode = returncode
        self.full_stderr = stderr


# Actionable error keywords that can appear before standard stream markers
_ACTIONABLE_PATTERNS = (
    "permission denied",
    "no such file",
    "not found",
    "invalid data",
    "protocol not found",
    "unable to open",
    "cannot open",
)


def _strip_ffmpeg_banner(stderr: str) -> str:
    """Remove FFmpeg version banner and build configuration from stderr.

    The banner includes version lines, build flags, and library versions
    that clutter error messages. We keep everything from the first 'Input #'
    or from the first line that doesn't look like banner noise.

    Actionable root-cause lines (e.g. 'Permission denied') are preserved
    even if they appear before the usual stream markers.
    """
    lines = stderr.splitlines()
    result_lines: list[str] = []
    in_banner = True
    for line in lines:
        if in_banner:
            # Heuristic: banner lines are indented or start with version info
            stripped = line.strip()
            if stripped.startswith("ffmpeg version") or stripped.startswith("ffprobe version"):
                continue
            if stripped.startswith("built with") or stripped.startswith("configuration:"):
                continue
            if stripped.startswith("lib") and "/" in stripped:
                continue
            # Preserve actionable root-cause lines that appear early
            if (
                any(p in stripped.lower() for p in _ACTIONABLE_PATTERNS)
                or stripped.startswith("Stream mapping:")
                or stripped.startswith("Input #")
                or stripped.startswith("Output #")
                or (stripped.startswith("[") and "Error" in stripped)
                or "error" in stripped.lower()
            ):
                in_banner = False
            else:
                # Still looks like banner noise — skip it
                continue
        result_lines.append(line)
    return "\n".join(result_lines) if result_lines else stderr


class ProcessingError(MCPVideoError):
    """FFmpeg processing failed."""

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        cleaned = _strip_ffmpeg_banner(stderr)
        # Truncate stderr to last 500 chars for readability
        stderr_short = cleaned[-500:] if len(cleaned) > 500 else cleaned
        super().__init__(
            f"FFmpeg processing failed (exit code {returncode}): {stderr_short}",
            error_type="processing_error",
            code=f"ffmpeg_exit_{returncode}",
        )
        self.command = command
        self.returncode = returncode
        self.full_stderr = stderr


class ResourceError(MCPVideoError):
    """Insufficient disk space or memory."""

    def __init__(self, resource: str, detail: str) -> None:
        super().__init__(
            f"Resource error ({resource}): {detail}",
            error_type="resource_error",
            code="insufficient_resource",
        )


def parse_ffmpeg_error(stderr: str) -> MCPVideoError:
    """Parse FFmpeg stderr and return the most specific error type."""
    stderr = _strip_ffmpeg_banner(stderr)
    stderr_lower = stderr.lower()

    if "no such file or directory" in stderr_lower:
        return InputFileError("", "File not found")
    if "invalid data found when processing input" in stderr_lower:
        return InputFileError("", "Not a valid video file")
    if "unsupported codec" in stderr_lower or "decoder" in stderr_lower:
        codec = "unknown"
        for line in stderr.split("\n"):
            if "codec" in line.lower():
                codec = line.strip()
                break
        return CodecError(codec)
    if "error while decoding" in stderr_lower:
        return ProcessingError("", 1, stderr)
    if "permission denied" in stderr_lower:
        return InputFileError("", "Permission denied")
    if "no space left on device" in stderr_lower:
        return ResourceError("disk_space", "No space left on device")

    return ProcessingError("", 1, stderr)


def wrap_error(exc: Exception) -> MCPVideoError:
    """Convert any exception to MCPVideoError. Returns as-is if already MCPVideoError."""
    if isinstance(exc, MCPVideoError):
        return exc
    return ProcessingError(str(exc), 1, getattr(exc, "stderr", ""))
