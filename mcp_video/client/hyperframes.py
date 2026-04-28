"""mcp-video Python client — Hyperframes operations mixin."""

from __future__ import annotations

from ..errors import MCPVideoError


class ClientHyperframesMixin:
    """Hyperframes operations mixin."""

    def hyperframes_render(
        self,
        project_path: str,
        output: str | None = None,
        fps: float | None = None,
        width: int | None = None,
        height: int | None = None,
        quality: str | None = None,
        format: str | None = None,
        workers: str | int | None = None,
        crf: int | None = None,
    ) -> dict:
        """Render a Hyperframes composition to video."""
        from ..hyperframes_engine import render

        return render(
            project_path,
            output_path=output,
            fps=fps,
            width=width,
            height=height,
            quality=quality,
            format=format,
            workers=workers,
            crf=crf,
        )

    def hyperframes_compositions(self, project_path: str) -> dict:
        """List compositions in a Hyperframes project."""
        from ..hyperframes_engine import compositions

        return compositions(project_path)

    def hyperframes_preview(self, project_path: str, port: int = 3002) -> dict:
        """Launch Hyperframes preview studio for live preview."""
        from ..hyperframes_engine import preview

        return preview(project_path, port=port)

    def hyperframes_still(
        self,
        project_path: str,
        output: str | None = None,
        frame: int = 0,
    ) -> dict:
        """Render a single frame as image."""
        from ..hyperframes_engine import still

        return still(project_path, output_path=output, frame=frame)

    def hyperframes_init(
        self,
        name: str,
        output_dir: str | None = None,
        template: str = "blank",
    ) -> dict:
        """Scaffold a new Hyperframes project.

        Args:
            name: Project name
            output_dir: Directory to create project in (default: current dir)
            template: Project template (blank, warm-grain, swiss-grid)

        Returns:
            dict with key "project_path" (str): absolute path to the new project
        """
        if not name:
            raise MCPVideoError("name cannot be empty", error_type="validation_error", code="empty_name")
        from ..hyperframes_engine import create_project

        return create_project(name, output_dir=output_dir, template=template)

    def hyperframes_add_block(
        self,
        project_path: str,
        block_name: str,
    ) -> dict:
        """Install a block from the Hyperframes catalog."""
        from ..hyperframes_engine import add_block

        return add_block(project_path, block_name)

    def hyperframes_validate(self, project_path: str) -> dict:
        """Validate project for rendering readiness.

        Args:
            project_path: Path to the Hyperframes project directory

        Returns:
            HyperframesValidationResult with pass/fail status and issues list
        """
        from ..hyperframes_engine import validate

        return validate(project_path)

    def hyperframes_to_mcpvideo(
        self,
        project_path: str,
        post_process: list[dict],
        output: str | None = None,
    ) -> dict:
        """Render a Hyperframes composition then post-process with mcp-video tools.

        Args:
            project_path: Path to the Hyperframes project directory
            post_process: List of post-processing operations. Each op has "op" (str) and
                optional "params" (dict). Valid op values: resize, convert, add_audio,
                normalize_audio, add_text, fade, watermark
            output: Output file path (auto-generated if omitted)

        Returns:
            HyperframesPipelineResult with output path and applied operations
        """
        from ..hyperframes_engine import render_and_post

        return render_and_post(project_path, post_process, output_path=output)
