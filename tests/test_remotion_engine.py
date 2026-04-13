"""Tests for the Remotion engine."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_video.remotion_engine import (
    _require_remotion_deps,
    _validate_project,
    compositions,
    create_project,
    render,
    render_and_post,
    scaffold_template,
    still,
    studio,
    validate,
)
from mcp_video.errors import (
    RemotionNotFoundError,
    RemotionProjectError,
    RemotionRenderError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed_process(
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess:
    """Create a fake subprocess.CompletedProcess for mocking."""
    return subprocess.CompletedProcess(
        args=["npx", "remotion"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _mock_deps_ok():
    """Return a patcher that makes shutil.which find node and npx."""
    def _which(name: str):
        if name in ("node", "npx", "npm"):
            return f"/usr/bin/{name}"
        return None
    return patch("mcp_video.remotion_engine.shutil.which", side_effect=_which)


def _mock_project_ok(project_dir: str):
    """Return a patcher that makes _validate_project succeed."""
    return patch.object(Path, "is_dir", return_value=True), \
           patch.object(Path, "is_file", return_value=True)


# ---------------------------------------------------------------------------
# Test: _require_remotion_deps
# ---------------------------------------------------------------------------

class TestRequireRemotionDeps:
    """Tests for _require_remotion_deps()."""

    @patch("mcp_video.remotion_engine.shutil.which", return_value=None)
    def test_raises_when_node_missing(self, mock_which):
        """Should raise RemotionNotFoundError when node is not on PATH."""
        with pytest.raises(RemotionNotFoundError, match="node not found"):
            _require_remotion_deps()
        mock_which.assert_called_with("node")

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_raises_when_npx_missing(self, mock_which):
        """Should raise RemotionNotFoundError when npx is not on PATH."""
        def _which(name: str):
            if name == "node":
                return "/usr/bin/node"
            return None
        mock_which.side_effect = _which

        with pytest.raises(RemotionNotFoundError, match="npx not found"):
            _require_remotion_deps()

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_passes_when_both_found(self, mock_which):
        """Should not raise when both node and npx are available."""
        def _which(name: str):
            return f"/usr/bin/{name}"
        mock_which.side_effect = _which

        _require_remotion_deps()  # should not raise

    def test_raises_with_correct_error_type(self):
        """RemotionNotFoundError should have error_type='dependency_error'."""
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError) as exc_info:
                _require_remotion_deps()
            assert exc_info.value.error_type == "dependency_error"
            assert exc_info.value.code == "remotion_not_found"


# ---------------------------------------------------------------------------
# Test: _validate_project
# ---------------------------------------------------------------------------

class TestValidateProject:
    """Tests for _validate_project()."""

    def test_raises_when_directory_missing(self, tmp_path):
        """Should raise RemotionProjectError if directory does not exist."""
        missing = str(tmp_path / "nonexistent")
        with pytest.raises(RemotionProjectError, match="Directory does not exist"):
            _validate_project(missing)

    def test_raises_when_no_package_json(self, tmp_path):
        """Should raise RemotionProjectError when package.json is missing."""
        with pytest.raises(RemotionProjectError, match=r"Missing package\.json"):
            _validate_project(str(tmp_path))

    def test_raises_when_no_root_tsx(self, tmp_path):
        """Should raise RemotionProjectError when src/Root.tsx is missing."""
        (tmp_path / "package.json").write_text("{}")
        with pytest.raises(RemotionProjectError, match=r"Missing src/Root\.tsx"):
            _validate_project(str(tmp_path))

    def test_returns_resolved_path_on_success(self, tmp_path):
        """Should return the resolved Path when project is valid."""
        (tmp_path / "package.json").write_text("{}")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Root.tsx").write_text(
            'import { registerRoot } from "remotion";\nregisterRoot();'
        )

        project_dir, entry_point = _validate_project(str(tmp_path))
        assert project_dir == tmp_path.resolve()
        assert isinstance(project_dir, Path)


# ---------------------------------------------------------------------------
# Test: render
# ---------------------------------------------------------------------------

class TestRender:
    """Tests for render()."""

    def test_builds_correct_cli_args(self, sample_remotion_project):
        """render() should invoke npx remotion with the right arguments."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="Rendered.")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp) as mock_run, \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024 * 1024):

            render(
                project,
                composition_id="MyComp",
                codec="h264",
                output_path="/tmp/out.mp4",
            )

            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert cmd[0] == "npx"
            assert cmd[1] == "remotion"
            assert "render" in cmd
            assert "MyComp" in cmd
            assert "/tmp/out.mp4" in cmd
            assert "--codec" in cmd
            idx = cmd.index("--codec")
            assert cmd[idx + 1] == "h264"

    def test_passes_all_optional_args(self, sample_remotion_project):
        """render() should forward crf, width, height, fps, concurrency, frames, scale, props."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="done")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=2 * 1024 * 1024):

            result = render(
                project,
                composition_id="Comp",
                output_path="/tmp/out.mp4",
                crf=18,
                width=1280,
                height=720,
                fps=60,
                concurrency=4,
                frames="0-30",
                scale=0.5,
                props={"title": "Hello"},
            )

            # Verify the result has the expected fields
            assert result.output_path == "/tmp/out.mp4"
            assert result.codec == "h264"
            assert result.resolution == "1280x720"

    def test_raises_on_nonzero_exit(self, sample_remotion_project):
        """render() should raise RemotionRenderError on non-zero exit."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(
            returncode=1,
            stderr="Something went wrong",
        )

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):
            with pytest.raises(RemotionRenderError, match="exit code 1"):
                render(project, composition_id="Comp", output_path="/tmp/out.mp4")

    def test_sets_resolution_when_both_width_and_height(self, sample_remotion_project):
        """render() should set resolution when width and height are provided."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024):

            result = render(
                project,
                composition_id="Comp",
                output_path="/tmp/out.mp4",
                width=1920,
                height=1080,
            )
            assert result.resolution == "1920x1080"

    def test_resolution_is_none_when_dimensions_missing(self, sample_remotion_project):
        """render() should return resolution=None when width/height are not set."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024):

            result = render(
                project,
                composition_id="Comp",
                output_path="/tmp/out.mp4",
            )
            assert result.resolution is None


# ---------------------------------------------------------------------------
# Test: compositions
# ---------------------------------------------------------------------------

class TestCompositions:
    """Tests for compositions()."""

    def test_parses_json_output(self, sample_remotion_project):
        """compositions() should parse JSON output from Remotion CLI."""
        project = str(sample_remotion_project)
        comp_json = json.dumps([
            {
                "id": "Main",
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "durationInFrames": 150,
                "defaultProps": {"title": "Hello"},
            },
            {
                "id": "Second",
                "width": 1280,
                "height": 720,
                "fps": 60,
                "durationInFrames": 300,
            },
        ])
        fake_cp = _make_completed_process(stdout=comp_json)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):

            result = compositions(project)
            assert len(result.compositions) == 2
            assert result.compositions[0].id == "Main"
            assert result.compositions[0].width == 1920
            assert result.compositions[1].id == "Second"
            assert result.compositions[1].fps == 60

    def test_parses_single_composition_dict(self, sample_remotion_project):
        """compositions() should handle a single composition dict (not wrapped in a list)."""
        project = str(sample_remotion_project)
        comp_json = json.dumps({
            "id": "Solo",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "durationInFrames": 90,
        })
        fake_cp = _make_completed_process(stdout=comp_json)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):

            result = compositions(project)
            assert len(result.compositions) == 1
            assert result.compositions[0].id == "Solo"

    def test_parses_compositions_key_wrapper(self, sample_remotion_project):
        """compositions() should handle {"compositions": [...]} wrapper format."""
        project = str(sample_remotion_project)
        comp_json = json.dumps({
            "compositions": [
                {"id": "A", "width": 1920, "height": 1080, "fps": 30, "durationInFrames": 60},
            ]
        })
        fake_cp = _make_completed_process(stdout=comp_json)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):

            result = compositions(project)
            assert len(result.compositions) == 1
            assert result.compositions[0].id == "A"

    def test_handles_invalid_json(self, sample_remotion_project):
        """compositions() should return empty list when JSON is invalid."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="not json at all")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):

            result = compositions(project)
            assert result.compositions == []

    def test_raises_on_nonzero_exit(self, sample_remotion_project):
        """compositions() should raise RemotionRenderError on failure."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(returncode=1, stderr="error")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):
            with pytest.raises(RemotionRenderError):
                compositions(project)

    def test_passes_composition_id_filter(self, sample_remotion_project):
        """compositions() should pass --composition when composition_id is given."""
        project = str(sample_remotion_project)
        comp_json = json.dumps([{"id": "Main"}])
        fake_cp = _make_completed_process(stdout=comp_json)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp) as mock_run:

            compositions(project, composition_id="Main")
            cmd = mock_run.call_args[0][0]
            assert "--composition" in cmd
            idx = cmd.index("--composition")
            assert cmd[idx + 1] == "Main"

    def test_uses_composition_id_alias(self, sample_remotion_project):
        """compositions() should handle 'compositionId' key in JSON output."""
        project = str(sample_remotion_project)
        comp_json = json.dumps([
            {"compositionId": "Alias", "width": 1280, "height": 720},
        ])
        fake_cp = _make_completed_process(stdout=comp_json)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):

            result = compositions(project)
            assert result.compositions[0].id == "Alias"


# ---------------------------------------------------------------------------
# Test: studio
# ---------------------------------------------------------------------------

class TestStudio:
    """Tests for studio()."""

    def test_returns_url_with_correct_port(self, sample_remotion_project):
        """studio() should return a URL with the specified port."""
        project = str(sample_remotion_project)
        mock_proc = MagicMock()

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.Popen", return_value=mock_proc):

            result = studio(project, port=3000)
            assert result.url == "http://localhost:3000"
            assert result.port == 3000

    def test_custom_port(self, sample_remotion_project):
        """studio() should accept a custom port."""
        project = str(sample_remotion_project)
        mock_proc = MagicMock()

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.Popen", return_value=mock_proc):

            result = studio(project, port=8080)
            assert result.url == "http://localhost:8080"
            assert result.port == 8080

    def test_launches_popen_with_correct_command(self, sample_remotion_project):
        """studio() should launch npx remotion studio with --port."""
        project = str(sample_remotion_project)
        mock_proc = MagicMock()

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.Popen", return_value=mock_proc) as mock_popen:

            studio(project, port=3001)

            call_args = mock_popen.call_args
            cmd = call_args[0][0]
            assert cmd[0] == "npx"
            assert cmd[1] == "remotion"
            assert "studio" in cmd
            assert "--port" in cmd
            idx = cmd.index("--port")
            assert cmd[idx + 1] == "3001"


# ---------------------------------------------------------------------------
# Test: still
# ---------------------------------------------------------------------------

class TestStill:
    """Tests for still()."""

    def test_renders_single_frame(self, sample_remotion_project):
        """still() should render a single frame with correct args."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="Rendered frame.")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp) as mock_run:

            result = still(
                project,
                composition_id="MyComp",
                output_path="/tmp/frame.png",
                frame=42,
                image_format="png",
            )

            assert result.output_path == "/tmp/frame.png"
            assert result.frame == 42

            cmd = mock_run.call_args[0][0]
            assert "still" in cmd
            assert "--frame" in cmd
            idx = cmd.index("--frame")
            assert cmd[idx + 1] == "42"
            assert "--image-format" in cmd
            idx = cmd.index("--image-format")
            assert cmd[idx + 1] == "png"

    def test_default_output_path(self, sample_remotion_project):
        """still() should generate an output path when none is provided."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.makedirs"):

            result = still(project, composition_id="Comp", frame=5)
            assert "Comp_frame5.png" in result.output_path

    def test_jpeg_format_output(self, sample_remotion_project):
        """still() should use .jpg extension for jpeg format."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.makedirs"):

            result = still(
                project,
                composition_id="Comp",
                frame=0,
                image_format="jpeg",
            )
            assert result.output_path.endswith(".jpg")

    def test_raises_on_failure(self, sample_remotion_project):
        """still() should raise RemotionRenderError on non-zero exit."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(returncode=1, stderr="still failed")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):
            with pytest.raises(RemotionRenderError, match="still failed"):
                still(project, composition_id="Comp", output_path="/tmp/out.png")


# ---------------------------------------------------------------------------
# Test: create_project
# ---------------------------------------------------------------------------

class TestCreateProject:
    """Tests for create_project()."""

    def test_creates_directory_structure(self, tmp_path):
        """create_project() should create the expected directory structure."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run") as mock_run:
            # Let npm install succeed (or be skipped)
            mock_run.return_value = _make_completed_process(stdout="installed")

            create_project("test-project", output_dir=str(tmp_path))

            project_dir = tmp_path / "test-project"
            assert project_dir.is_dir()
            assert (project_dir / "package.json").is_file()
            assert (project_dir / "tsconfig.json").is_file()
            assert (project_dir / "src" / "index.ts").is_file()
            assert (project_dir / "src" / "Root.tsx").is_file()

    def test_package_json_contains_project_name(self, tmp_path):
        """package.json should contain the provided project name."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=_make_completed_process()):

            create_project("my-remotion-app", output_dir=str(tmp_path))

            pkg = json.loads((tmp_path / "my-remotion-app" / "package.json").read_text())
            assert pkg["name"] == "my-remotion-app"

    def test_blank_template(self, tmp_path):
        """Blank template should create a minimal Root.tsx."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=_make_completed_process()):

            result = create_project("proj", output_dir=str(tmp_path), template="blank")
            assert result.template == "blank"

            root = (tmp_path / "proj" / "src" / "Root.tsx").read_text()
            assert "RemotionRoot" in root
            assert "Composition" in root

    def test_hello_world_template(self, tmp_path):
        """hello-world template should include HelloWorld composition."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=_make_completed_process()):

            result = create_project("proj", output_dir=str(tmp_path), template="hello-world")
            assert result.template == "hello-world"

            hello = (tmp_path / "proj" / "src" / "HelloWorld.tsx").read_text()
            assert "HelloWorld" in hello
            assert "Hello, Remotion!" in hello

            root = (tmp_path / "proj" / "src" / "Root.tsx").read_text()
            assert "HelloWorld" in root

    def test_returns_correct_files_list(self, tmp_path):
        """create_project() should return the list of created files."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=_make_completed_process()):

            result = create_project("proj", output_dir=str(tmp_path), template="hello-world")
            assert "package.json" in result.files
            assert "tsconfig.json" in result.files
            assert "src/index.ts" in result.files
            assert "src/Root.tsx" in result.files
            assert "src/HelloWorld.tsx" in result.files

    def test_runs_npm_install(self, tmp_path):
        """create_project() should run npm install in the project directory."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=_make_completed_process()) as mock_run:

            create_project("proj", output_dir=str(tmp_path))

            # Find the npm install call
            npm_calls = [
                c for c in mock_run.call_args_list
                if c[0][0][0] == "npm"
            ]
            assert len(npm_calls) == 1
            assert npm_calls[0][0][0] == ["npm", "install"]

    def test_npm_install_failure_is_non_fatal(self, tmp_path):
        """create_project() should not raise if npm install fails."""
        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run") as mock_run:
            # Make npm install raise
            def _run_side_effect(*args, **kwargs):
                if args[0][0] == "npm":
                    raise FileNotFoundError("npm not found")
                return _make_completed_process()
            mock_run.side_effect = _run_side_effect

            # Should not raise
            result = create_project("proj", output_dir=str(tmp_path))
            assert result.success is True


# ---------------------------------------------------------------------------
# Test: scaffold_template
# ---------------------------------------------------------------------------

class TestScaffoldTemplate:
    """Tests for scaffold_template()."""

    def test_generates_tsx_files(self, tmp_path):
        """scaffold_template() should create constants.ts and composition TSX."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text("{}")
        (project_dir / "src").mkdir()

        with _mock_deps_ok():
            result = scaffold_template(
                str(project_dir),
                spec={"primary_color": "#ff0000"},
                slug="my-comp",
            )

        assert "src/constants.ts" in result.files
        assert "src/compositions/my-comp.tsx" in result.files
        assert "src/Root.tsx" in result.files

    def test_constants_use_spec_values(self, tmp_path):
        """scaffold_template() should inject spec values into constants.ts."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()

        spec = {
            "primary_color": "#aabbcc",
            "secondary_color": "#ddeeff",
            "background_color": "#112233",
            "heading_font": "Inter",
            "body_font": "Roboto",
            "target_fps": 60,
            "target_duration": 10,
        }

        with _mock_deps_ok():
            scaffold_template(str(project_dir), spec=spec, slug="test")

        constants = (project_dir / "src" / "constants.ts").read_text()
        assert "#aabbcc" in constants
        assert "Inter" in constants
        assert "Roboto" in constants
        assert "60" in constants
        assert "10" in constants

    def test_default_spec_values(self, tmp_path):
        """scaffold_template() should use defaults when spec is empty."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()

        with _mock_deps_ok():
            scaffold_template(str(project_dir), spec={}, slug="test")

        constants = (project_dir / "src" / "constants.ts").read_text()
        assert "#1a1a2e" in constants  # default primary_color
        assert "Arial" in constants  # default heading_font

    def test_composition_file_contains_slug(self, tmp_path):
        """The generated composition TSX should use the slug."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()

        with _mock_deps_ok():
            scaffold_template(str(project_dir), spec={}, slug="promo")

        comp = (project_dir / "src" / "compositions" / "promo.tsx").read_text()
        assert "promoComposition" in comp
        assert "export default" in comp

    def test_raises_when_directory_missing(self, tmp_path):
        """scaffold_template() should raise RemotionProjectError for missing dir."""
        with _mock_deps_ok():
            with pytest.raises(RemotionProjectError, match="Directory does not exist"):
                scaffold_template(
                    str(tmp_path / "nonexistent"),
                    spec={},
                    slug="test",
                )


# ---------------------------------------------------------------------------
# Test: validate
# ---------------------------------------------------------------------------

class TestValidate:
    """Tests for validate()."""

    def test_detects_missing_directory(self, tmp_path):
        """validate() should report when project directory doesn't exist."""
        missing = str(tmp_path / "ghost")
        result = validate(missing)
        assert result.valid is False
        assert "Project directory does not exist" in result.issues

    def test_detects_missing_package_json(self, tmp_path):
        """validate() should report missing package.json."""
        result = validate(str(tmp_path))
        assert result.valid is False
        assert any("package.json" in i for i in result.issues)

    def test_detects_missing_root_tsx(self, tmp_path):
        """validate() should report missing src/Root.tsx."""
        (tmp_path / "package.json").write_text("{}")
        result = validate(str(tmp_path))
        assert result.valid is False
        assert any("Root.tsx" in i for i in result.issues)

    def test_detects_missing_node(self, tmp_path):
        """validate() should report when Node.js is not on PATH."""
        (tmp_path / "package.json").write_text("{}")
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")

        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            result = validate(str(tmp_path))

        assert result.valid is False
        assert any("Node.js not found" in i for i in result.issues)
        assert any("npx not found" in i for i in result.issues)

    def test_valid_project(self, tmp_path):
        """validate() should return valid=True for a well-formed project."""
        (tmp_path / "package.json").write_text("{}")
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")
        (tmp_path / "tsconfig.json").write_text("{}")
        (tmp_path / "node_modules").mkdir()

        with _mock_deps_ok():
            result = validate(str(tmp_path))

        assert result.valid is True
        assert result.issues == []

    def test_warns_about_missing_node_modules(self, tmp_path):
        """validate() should warn when node_modules is missing."""
        (tmp_path / "package.json").write_text("{}")
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")

        with _mock_deps_ok():
            result = validate(str(tmp_path))

        assert any("node_modules" in w for w in result.warnings)

    def test_warns_about_missing_tsconfig(self, tmp_path):
        """validate() should warn when tsconfig.json is missing."""
        (tmp_path / "package.json").write_text("{}")
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")
        (tmp_path / "node_modules").mkdir()

        with _mock_deps_ok():
            result = validate(str(tmp_path))

        assert any("tsconfig.json" in w for w in result.warnings)

    def test_valid_project_with_deps_available(self, tmp_path):
        """validate() should pass when all deps and files are present."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "tsconfig.json").write_text("{}")
        (tmp_path / "node_modules").mkdir()
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")

        with _mock_deps_ok():
            result = validate(str(tmp_path))

        assert result.valid is True
        assert result.issues == []
        assert result.warnings == []


# ---------------------------------------------------------------------------
# Test: render_and_post
# ---------------------------------------------------------------------------

class TestRenderAndPost:
    """Tests for render_and_post()."""

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_chains_render_and_resize(self, mock_which, sample_remotion_project):
        """render_and_post() should render then apply resize."""
        def _which(name: str):
            if name in ("node", "npx"):
                return f"/usr/bin/{name}"
            if name in ("ffmpeg", "ffprobe"):
                return f"/usr/bin/{name}"
            return None
        mock_which.side_effect = _which

        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="rendered")

        mock_resize_result = MagicMock()
        mock_resize_result.output_path = "/tmp/resized.mp4"

        with patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024), \
             patch("mcp_video.engine.resize", return_value=mock_resize_result):

            result = render_and_post(
                project,
                composition_id="Comp",
                post_process=[
                    {"op": "resize", "params": {"width": 640, "height": 480}},
                ],
                output_path="/tmp/resized.mp4",
            )

            assert result.operations == ["resize"]
            assert result.final_output == "/tmp/resized.mp4"
            assert result.remotion_output  # should be set from the render step

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_chains_multiple_operations(self, mock_which, sample_remotion_project):
        """render_and_post() should chain multiple post-processing ops."""
        def _which(name: str):
            if name in ("node", "npx", "ffmpeg", "ffprobe"):
                return f"/usr/bin/{name}"
            return None
        mock_which.side_effect = _which

        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        mock_result = MagicMock()
        mock_result.output_path = "/tmp/final.mp4"

        with patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024), \
             patch("mcp_video.engine.convert", return_value=mock_result), \
             patch("mcp_video.engine.add_audio", return_value=mock_result):

            result = render_and_post(
                project,
                composition_id="Comp",
                post_process=[
                    {"op": "convert", "params": {"format": "webm"}},
                    {"op": "add_audio", "params": {"audio_path": "/tmp/audio.mp3"}},
                ],
            )

            assert result.operations == ["convert", "add_audio"]

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_unknown_operation(self, mock_which, sample_remotion_project):
        """render_and_post() should raise ValueError for unknown operations."""
        def _which(name: str):
            if name in ("node", "npx"):
                return f"/usr/bin/{name}"
            return None
        mock_which.side_effect = _which

        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        with patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024):

            with pytest.raises(ValueError, match=r"Unknown post-processing operation.*nonexistent_op"):
                render_and_post(
                    project,
                    composition_id="Comp",
                    post_process=[
                        {"op": "nonexistent_op", "params": {}},
                    ],
                )

    @patch("mcp_video.remotion_engine.shutil.which")
    def test_type_alias_for_op(self, mock_which, sample_remotion_project):
        """render_and_post() should accept 'type' key as alias for 'op'."""
        def _which(name: str):
            if name in ("node", "npx", "ffmpeg", "ffprobe"):
                return f"/usr/bin/{name}"
            return None
        mock_which.side_effect = _which

        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(stdout="ok")

        mock_result = MagicMock()
        mock_result.output_path = "/tmp/out.mp4"

        with patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp), \
             patch("os.path.isfile", return_value=True), \
             patch("os.path.getsize", return_value=1024), \
             patch("mcp_video.engine.normalize_audio", return_value=mock_result):

            result = render_and_post(
                project,
                composition_id="Comp",
                post_process=[
                    {"type": "normalize_audio", "params": {"target_lufs": -14}},
                ],
            )

            assert result.operations == ["normalize_audio"]


# ---------------------------------------------------------------------------
# Test: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling edge cases."""

    def test_render_timeout(self, sample_remotion_project):
        """render() should raise RemotionRenderError on timeout."""
        project = str(sample_remotion_project)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="npx", timeout=600)

            with pytest.raises(RemotionRenderError, match="timed out"):
                render(project, composition_id="Comp", output_path="/tmp/out.mp4")

    def test_render_npx_not_found(self, sample_remotion_project):
        """render() should raise RemotionNotFoundError when npx binary is missing."""
        project = str(sample_remotion_project)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("npx not found")

            with pytest.raises(RemotionNotFoundError, match="npx command not found"):
                render(project, composition_id="Comp", output_path="/tmp/out.mp4")

    def test_render_error_has_command_and_returncode(self, sample_remotion_project):
        """RemotionRenderError should carry command and returncode info."""
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(returncode=42, stderr="Bad error")

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):
            with pytest.raises(RemotionRenderError) as exc_info:
                render(project, composition_id="Comp", output_path="/tmp/out.mp4")

            err = exc_info.value
            assert err.returncode == 42
            assert "42" in err.code  # code should be remotion_exit_42

    def test_render_error_truncates_long_stderr(self, sample_remotion_project):
        """RemotionRenderError should truncate very long stderr."""
        long_stderr = "x" * 1000
        project = str(sample_remotion_project)
        fake_cp = _make_completed_process(returncode=1, stderr=long_stderr)

        with _mock_deps_ok(), \
             patch("mcp_video.remotion_engine.subprocess.run", return_value=fake_cp):
            with pytest.raises(RemotionRenderError) as exc_info:
                render(project, composition_id="Comp", output_path="/tmp/out.mp4")

            # full_stderr should be the original, but message should be truncated
            assert exc_info.value.full_stderr == long_stderr

    def test_missing_deps_before_project_validation(self):
        """All public functions should check deps before project validation."""
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError):
                render("/some/project", composition_id="C")

    def test_studio_missing_deps(self):
        """studio() should raise RemotionNotFoundError when deps are missing."""
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError):
                studio("/some/project")

    def test_still_missing_deps(self):
        """still() should raise RemotionNotFoundError when deps are missing."""
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError):
                still("/some/project", composition_id="C")

    def test_create_project_missing_deps(self):
        """create_project() should raise RemotionNotFoundError when deps are missing."""
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError):
                create_project("test")

    def test_scaffold_template_missing_deps(self, tmp_path):
        """scaffold_template() should raise RemotionNotFoundError when deps are missing."""
        (tmp_path / "src").mkdir()
        with patch("mcp_video.remotion_engine.shutil.which", return_value=None):
            with pytest.raises(RemotionNotFoundError):
                scaffold_template(str(tmp_path), spec={}, slug="test")


# ---------------------------------------------------------------------------
# Integration tests (require real Node.js)
# ---------------------------------------------------------------------------

@pytest.mark.remotion
class TestRemotionIntegration:
    """Integration tests that require a real Node.js/Remotion installation."""

    def test_require_remotion_deps_with_real_node(self):
        """Verify deps check passes with a real Node.js install."""
        _require_remotion_deps()  # should not raise

    def test_validate_real_project(self, tmp_path):
        """Validate a well-formed project structure."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        src = tmp_path / "src"
        src.mkdir()
        (src / "Root.tsx").write_text("// root")
        result = validate(str(tmp_path))
        assert result.valid is True
