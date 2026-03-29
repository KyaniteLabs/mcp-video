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


class ResolutionMismatchError(MCPVideoError):
    """Clips have different resolutions for concat operation."""

    def __init__(self, resolutions: list[str]) -> None:
        super().__init__(
            f"Resolution mismatch: clips have different resolutions: {resolutions}",
            error_type="encoding_error",
            code="resolution_mismatch",
            suggested_action={
                "auto_fix": True,
                "description": "Auto-resize all clips to match the largest resolution before merging",
            },
        )


class RemotionNotFoundError(MCPVideoError):
    """Node.js or npx not found on PATH."""

    def __init__(self, detail: str = "") -> None:
        msg = "Remotion requires Node.js and npx. Install Node.js from https://nodejs.org"
        if detail:
            msg += f" — {detail}"
        super().__init__(
            msg,
            error_type="dependency_error",
            code="remotion_not_found",
            suggested_action={
                "auto_fix": False,
                "description": "Install Node.js (v18+) and ensure npx is on PATH",
            },
        )


class RemotionProjectError(MCPVideoError):
    """Invalid Remotion project structure."""

    def __init__(self, path: str, reason: str = "Invalid project") -> None:
        super().__init__(
            f"Remotion project error: {path} — {reason}",
            error_type="project_error",
            code="invalid_remotion_project",
            suggested_action={
                "auto_fix": False,
                "description": "Ensure the project has package.json and src/Root.tsx",
            },
        )


class RemotionRenderError(MCPVideoError):
    """Remotion render failure."""

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        stderr_short = stderr[-500:] if len(stderr) > 500 else stderr
        super().__init__(
            f"Remotion render failed (exit code {returncode}): {stderr_short}",
            error_type="render_error",
            code=f"remotion_exit_{returncode}",
        )
        self.command = command
        self.returncode = returncode
        self.full_stderr = stderr


class RemotionValidationError(MCPVideoError):
    """Remotion project validation failure."""

    def __init__(self, issues: list[str]) -> None:
        msg = "Remotion validation failed: " + "; ".join(issues)
        super().__init__(
            msg,
            error_type="validation_error",
            code="remotion_validation_failed",
        )


class ProcessingError(MCPVideoError):
    """FFmpeg processing failed."""

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        # Truncate stderr to last 500 chars for readability
        stderr_short = stderr[-500:] if len(stderr) > 500 else stderr
        super().__init__(
            f"FFmpeg processing failed (exit code {returncode}): {stderr_short}",
            error_type="processing_error",
            code=f"ffmpeg_exit_{returncode}",
        )
        self.command = command
        self.returncode = returncode
        self.full_stderr = stderr


class ExportError(MCPVideoError):
    """Export/rendering failed."""

    def __init__(self, format: str, detail: str) -> None:
        super().__init__(
            f"Export to {format} failed: {detail}",
            error_type="export_error",
            code=f"export_{format}_failed",
        )


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


# Backwards compatibility alias
AgentCutError = MCPVideoError


def wrap_error(exc: Exception) -> MCPVideoError:
    """Convert any exception to MCPVideoError. Returns as-is if already MCPVideoError."""
    if isinstance(exc, MCPVideoError):
        return exc
    return ProcessingError(str(exc), 1, getattr(exc, "stderr", ""))
