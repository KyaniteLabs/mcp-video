"""mcp-video Python client — clean API for programmatic video editing."""

from __future__ import annotations

import warnings

from ..errors import MCPVideoError

_REMOTION_DEPRECATION_MSG = "Remotion is deprecated. Migrate to Hyperframes or Revideo."


def _warn_remotion_deprecated() -> None:
    warnings.warn(_REMOTION_DEPRECATION_MSG, FutureWarning, stacklevel=3)


class ClientRemotionMixin:
    """Remotion operations mixin."""

    def remotion_render(
        self,
        project_path: str,
        composition_id: str,
        output: str | None = None,
        codec: str = "h264",
        crf: int | None = None,
        width: int | None = None,
        height: int | None = None,
        fps: float | None = None,
        concurrency: int | None = None,
        frames: str | None = None,
        props: dict | None = None,
        scale: float | None = None,
    ) -> dict:
        """Render a Remotion composition to video."""
        _warn_remotion_deprecated()
        from ..remotion_engine import render

        return render(
            project_path,
            composition_id,
            output_path=output,
            codec=codec,
            crf=crf,
            width=width,
            height=height,
            fps=fps,
            concurrency=concurrency,
            frames=frames,
            props=props,
            scale=scale,
        )

    def remotion_compositions(self, project_path: str) -> list[dict]:
        """List compositions in a Remotion project."""
        _warn_remotion_deprecated()
        from ..remotion_engine import compositions

        return compositions(project_path)

    def remotion_studio(self, project_path: str, port: int = 3000) -> dict:
        """Launch Remotion Studio for live preview."""
        _warn_remotion_deprecated()
        from ..remotion_engine import studio

        return studio(project_path, port=port)

    def remotion_still(
        self,
        project_path: str,
        composition_id: str,
        output: str | None = None,
        frame: int = 0,
        image_format: str = "png",
    ) -> dict:
        """Render a single frame as image."""
        _warn_remotion_deprecated()
        from ..remotion_engine import still

        return still(project_path, composition_id, output_path=output, frame=frame, image_format=image_format)

    def remotion_create_project(
        self,
        name: str,
        output_dir: str | None = None,
        template: str = "blank",
    ) -> dict:
        """Scaffold a new Remotion project.

        Args:
            name: Project name
            output_dir: Directory to create project in (default: current dir)
            template: Project template (blank, hello-world)

        Returns:
            dict with key "project_path" (str): absolute path to the new project
        """
        _warn_remotion_deprecated()
        if not name:
            raise MCPVideoError("name cannot be empty", error_type="validation_error", code="empty_name")
        from ..remotion_engine import create_project

        return create_project(name, output_dir=output_dir, template=template)

    def remotion_scaffold_template(
        self,
        project_path: str,
        spec: dict,
        slug: str,
    ) -> None:
        """Generate composition from spec."""
        _warn_remotion_deprecated()
        from ..remotion_engine import scaffold_template

        return scaffold_template(project_path, spec, slug)

    def remotion_validate(self, project_path: str, composition_id: str | None = None) -> dict:
        """Validate project for rendering readiness.

        Args:
            project_path: Path to the Remotion project directory
            composition_id: Optional specific composition to validate.
                If omitted, validates the overall project structure.

        Returns:
            RemotionValidationResult with pass/fail status and issues list
        """
        _warn_remotion_deprecated()
        from ..remotion_engine import validate

        return validate(project_path, composition_id=composition_id)

    def remotion_to_mcpvideo(
        self,
        project_path: str,
        composition_id: str,
        post_process: list[dict],
        output: str | None = None,
    ) -> dict:
        """Render a Remotion composition then post-process with mcp-video tools.

        Args:
            project_path: Path to the Remotion project directory
            composition_id: The composition ID to render
            post_process: List of post-processing operations. Each op has "op" (str) and
                optional "params" (dict). Valid op values: resize, convert, add_audio,
                normalize_audio, add_text, fade, watermark
            output: Output file path (auto-generated if omitted)

        Returns:
            RemotionPipelineResult with output path and applied operations
        """
        _warn_remotion_deprecated()
        from ..remotion_engine import render_and_post

        return render_and_post(project_path, composition_id, post_process, output_path=output)

    # ------------------------------------------------------------------
    # Audio Synthesis (P1 Features)
    # ------------------------------------------------------------------
