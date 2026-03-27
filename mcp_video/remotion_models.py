"""Pydantic result models for Remotion integration tools."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Enums ---

RemotionCodec = Literal["h264", "h265", "vp8", "vp9", "prores", "gif"]

RemotionImageFormat = Literal["png", "jpeg", "webp"]


# --- Result models ---

class CompositionInfo(BaseModel):
    """A single composition found in a Remotion project."""

    id: str
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    duration_in_frames: int = 150
    default_props: dict[str, Any] = Field(default_factory=dict)


class CompositionsResult(BaseModel):
    """Result of listing compositions in a Remotion project."""

    success: bool = True
    compositions: list[CompositionInfo] = Field(default_factory=list)
    project_path: str


class RemotionRenderResult(BaseModel):
    """Result of rendering a Remotion composition."""

    success: bool = True
    output_path: str
    duration: float | None = None
    resolution: str | None = None
    codec: str = "h264"
    size_mb: float | None = None
    render_time: float | None = None


class RemotionStudioResult(BaseModel):
    """Result of launching Remotion Studio."""

    success: bool = True
    url: str
    port: int
    project_path: str


class RemotionStillResult(BaseModel):
    """Result of rendering a single frame from a Remotion composition."""

    success: bool = True
    output_path: str
    frame: int = 0
    resolution: str | None = None


class RemotionProjectResult(BaseModel):
    """Result of creating a new Remotion project."""

    success: bool = True
    project_path: str
    template: str | None = None
    files: list[str] = Field(default_factory=list)


class ScaffoldResult(BaseModel):
    """Result of scaffolding a composition from a spec."""

    success: bool = True
    project_path: str
    slug: str
    files: list[str] = Field(default_factory=list)


class RemotionValidationResult(BaseModel):
    """Result of validating a Remotion project."""

    success: bool = True
    valid: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    project_path: str


class RemotionPipelineResult(BaseModel):
    """Result of render + post-process pipeline."""

    success: bool = True
    remotion_output: str
    final_output: str
    operations: list[str] = Field(default_factory=list)
