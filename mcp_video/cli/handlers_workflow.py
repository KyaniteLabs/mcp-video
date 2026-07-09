"""CLI handlers for workflow-engine commands."""

from __future__ import annotations

from typing import Any

from .formatting import _format_workflow_validation
from .runner import CommandRunner, _out


def handle_workflow_commands(args: Any, *, use_json: bool) -> bool:
    """Handle workflow-engine CLI commands."""
    runner = CommandRunner(args, use_json)

    def _workflow_validate(a, j):
        from ..workflow import validate_workflow_spec

        result = validate_workflow_spec(a.spec)
        _out(result, j, _format_workflow_validation)

    runner.register("workflow-validate", _workflow_validate)

    return runner.dispatch()
