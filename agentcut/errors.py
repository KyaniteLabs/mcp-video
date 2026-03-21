"""AgentCut error types with auto-fix suggestions."""

from __future__ import annotations

from typing import Any


class AgentCutError(Exception):
    """Base error for all AgentCut operations."""

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


class FFmpegNotFoundError(AgentCutError):
    """FFmpeg is not installed or not on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "FFmpeg not found. Install it with: brew install ffmpeg (macOS), "
            "apt install ffmpeg (Ubuntu), or download from https://ffmpeg.org",
            error_type="dependency_error",
            code="ffmpeg_not_found",
            suggested_action={
                "auto_fix": False,
                "description": "Install FFmpeg before using AgentCut",
            },
        )


class FFprobeNotFoundError(AgentCutError):
    """FFprobe is not installed or not on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "FFprobe not found. It should be installed alongside FFmpeg.",
            error_type="dependency_error",
            code="ffprobe_not_found",
        )


class InputFileError(AgentCutError):
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


class CodecError(AgentCutError):
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
            docs_url="https://github.com/pastorsimon1798/agentcut#codec-compatibility",
        )


class ResolutionMismatchError(AgentCutError):
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


class ProcessingError(AgentCutError):
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


class ExportError(AgentCutError):
    """Export/rendering failed."""

    def __init__(self, format: str, detail: str) -> None:
        super().__init__(
            f"Export to {format} failed: {detail}",
            error_type="export_error",
            code=f"export_{format}_failed",
        )


class ResourceError(AgentCutError):
    """Insufficient disk space or memory."""

    def __init__(self, resource: str, detail: str) -> None:
        super().__init__(
            f"Resource error ({resource}): {detail}",
            error_type="resource_error",
            code="insufficient_resource",
        )


def parse_ffmpeg_error(stderr: str) -> AgentCutError:
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
