"""Rich output formatting helpers for the mcp-video CLI."""

from __future__ import annotations

import logging
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

console = Console()
err_console = Console(stderr=True)


def _format_info_text(info: Any) -> None:
    """Display video info as a rich table."""
    table = Table(title="Video Info", show_header=False, border_style="blue")
    table.add_column("Property", style="bold cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Path", str(getattr(info, "path", "N/A")))
    table.add_row("Duration", f"{getattr(info, 'duration', 0):.2f}s")
    table.add_row("Resolution", getattr(info, "resolution", "N/A"))
    table.add_row("Aspect Ratio", getattr(info, "aspect_ratio", "N/A"))
    table.add_row("FPS", str(getattr(info, "fps", "N/A")))
    table.add_row("Video Codec", getattr(info, "codec", "N/A"))
    table.add_row("Audio Codec", getattr(info, "audio_codec", "N/A"))
    table.add_row("Size", f"{getattr(info, 'size_mb', 0):.2f} MB")
    table.add_row("Format", getattr(info, "format", "N/A"))
    console.print(table)


def _format_edit_text(result: Any) -> None:
    """Display edit result as a success panel."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    lines = [
        f"[bold green]Operation:[/bold green] {data.get('operation', 'N/A')}",
        f"[bold green]Output:[/bold green] {data.get('output_path', 'N/A')}",
    ]
    if data.get("duration") is not None:
        lines.append(f"[bold green]Duration:[/bold green] {data['duration']:.2f}s")
    if data.get("resolution"):
        lines.append(f"[bold green]Resolution:[/bold green] {data['resolution']}")
    if data.get("size_mb") is not None:
        lines.append(f"[bold green]Size:[/bold green] {data['size_mb']:.2f} MB")
    if data.get("format"):
        lines.append(f"[bold green]Format:[/bold green] {data['format']}")
    console.print(Panel("\n".join(lines), border_style="green", title="Done"))


def _format_thumbnail_text(result: Any) -> None:
    """Display thumbnail/extract-frame result."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    frame_path = data.get("frame_path", "N/A")
    timestamp = data.get("timestamp", 0.0)
    console.print(
        Panel(
            f"[bold green]Frame extracted:[/bold green] {frame_path}\n[bold green]Timestamp:[/bold green] {timestamp:.2f}s",
            border_style="green",
            title="Done",
        )
    )


def _format_storyboard_text(result: Any) -> None:
    """Display storyboard result."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    frames = data.get("frames", [])
    grid = data.get("grid")
    lines = [
        f"[bold green]Frames:[/bold green] {data.get('count', len(frames))}",
    ]
    if frames:
        lines.append(f"[bold green]Output dir:[/bold green] {frames[0].rsplit('/', 1)[0] if '/' in frames[0] else '.'}")
    if grid:
        lines.append(f"[bold green]Grid:[/bold green] {grid}")
    console.print(Panel("\n".join(lines), border_style="green", title="Storyboard"))


def _format_batch_text(result: dict) -> None:
    """Display batch result as a table."""
    if result.get("success") is False:
        error_msg = result.get("error", {})
        msg = error_msg.get("message", str(error_msg)) if isinstance(error_msg, dict) else str(error_msg)
        console.print(f"[bold red]Batch failed: {msg}[/bold red]")
        return
    table = Table(title="Batch Results")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    table.add_column("Output")
    for r in result.get("results", []):
        status = "[green]OK[/green]" if r.get("success") else f"[red]{r.get('error', 'Failed')}[/red]"
        table.add_row(r.get("input", "N/A"), status, r.get("output_path", "-"))
    console.print(table)
    summary = f"[bold]{result['succeeded']}/{result['total']} succeeded[/bold]"
    if result.get("failed"):
        summary += f", [red]{result['failed']} failed[/red]"
    console.print(summary)


def _format_extract_audio_text(result: Any) -> None:
    """Display extract-audio result."""
    console.print(Panel(f"[bold green]Audio extracted:[/bold green] {result}", border_style="green", title="Done"))


def _format_doctor_text(report: dict[str, Any]) -> None:
    """Display diagnostics as a compact table."""
    summary = report["summary"]
    status = "OK" if summary["required_ok"] else "Missing required dependencies"
    console.print(f"[bold]mcp-video doctor[/bold] — {status}")
    table = Table(title="Environment Checks")
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Required")
    table.add_column("Status")
    table.add_column("Version / Hint")
    for check in report["checks"]:
        state = "[green]OK[/green]" if check["ok"] else "[yellow]Missing[/yellow]"
        detail = check.get("version") or check.get("install_hint") or "-"
        table.add_row(check["name"], check["category"], "yes" if check["required"] else "no", state, escape(detail))
    console.print(table)


def _format_error(e: Exception) -> None:
    """Display error in a styled panel."""
    from ..errors import MCPVideoError

    if isinstance(e, MCPVideoError):
        try:
            data = e.to_dict()
        except Exception as exc:
            logger.debug("MCPVideoError.to_dict() failed in CLI formatting: %s", exc)
            data = {}
        msg = data.get("message", str(e))
        code = data.get("code", "")
        action = data.get("suggested_action", {})
        lines = [f"[bold red]{msg}[/bold red]"]
        if code:
            lines.append(f"[dim]Code: {code}[/dim]")
        if isinstance(action, dict) and action.get("description"):
            lines.append(f"\n[yellow]Suggested fix:[/yellow] {action['description']}")
        err_console.print(Panel("\n".join(lines), border_style="red", title="Error"))
    else:
        err_console.print(Panel(f"[bold red]{e}[/bold red]", border_style="red", title="Error"))
