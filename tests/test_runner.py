"""Tests for the CommandRunner seam."""

from types import SimpleNamespace

import pytest

from mcp_video.cli.runner import CommandRunner, engine_cmd, plain_cmd, _out, _resolve_engine


class TestCommandRunner:
    def test_dispatch_runs_registered_handler(self, capsys):
        args = SimpleNamespace(command="hello")
        runner = CommandRunner(args, use_json=False)
        runner.register("hello", lambda a, j: print("world"))
        assert runner.dispatch() is True
        assert "world" in capsys.readouterr().out

    def test_dispatch_returns_false_for_unknown(self):
        args = SimpleNamespace(command="unknown")
        runner = CommandRunner(args, use_json=False)
        assert runner.dispatch() is False

    def test_dispatch_json_mode(self, capsys):
        args = SimpleNamespace(command="info")
        runner = CommandRunner(args, use_json=True)
        runner.register("info", lambda a, j: print("json" if j else "text"))
        assert runner.dispatch() is True
        assert "json" in capsys.readouterr().out


class TestEngineCmd:
    def test_engine_cmd_runs_with_spinner(self, monkeypatch, capsys):
        def fake_engine(x):
            return {"value": x}

        monkeypatch.setattr("mcp_video.cli.runner._with_spinner", lambda msg, fn, *a, **kw: fn(*a, **kw))
        handler = engine_cmd(fake_engine, "Working...", "x", formatter=lambda r: print(r["value"]))
        args = SimpleNamespace(x=42)
        handler(args, use_json=False)
        assert "42" in capsys.readouterr().out

    def test_engine_cmd_json_transform(self, monkeypatch, capsys):
        def fake_engine(x):
            return x

        monkeypatch.setattr("mcp_video.cli.runner._with_spinner", lambda msg, fn, *a, **kw: fn(*a, **kw))
        handler = engine_cmd(fake_engine, "Working...", "x", json_transform=lambda r: {"success": True, "data": r})
        args = SimpleNamespace(x=99)
        handler(args, use_json=True)
        out = capsys.readouterr().out
        assert "99" in out
        assert '"success": true' in out


class TestPlainCmd:
    def test_plain_cmd_skips_spinner(self, monkeypatch, capsys):
        def fake_engine(x):
            return {"value": x}

        handler = plain_cmd(fake_engine, "x", formatter=lambda r: print(r["value"]))
        args = SimpleNamespace(x=7)
        handler(args, use_json=False)
        assert "7" in capsys.readouterr().out


class TestResolveEngine:
    def test_resolve_callable(self):
        def fn(): ...
        assert _resolve_engine(fn) is fn

    def test_resolve_string(self):
        resolved = _resolve_engine("json:loads")
        import json
        assert resolved is json.loads

    def test_resolve_invalid(self):
        with pytest.raises(TypeError):
            _resolve_engine(123)


class TestOutHelper:
    def test_out_json(self, capsys):
        _out({"a": 1}, True, formatter=None)
        assert '"a": 1' in capsys.readouterr().out

    def test_out_text(self, capsys):
        _out("hello", False, formatter=lambda r: print(r.upper()))
        assert "HELLO" in capsys.readouterr().out
