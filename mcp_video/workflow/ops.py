"""Op allowlist + engine binding for the agent workflow engine.

Two distinct things are kept explicit and separate here:

1. A tiny input/output BINDING map (which ``inputs``/``output`` key wires to
   which engine positional arg). This is a small wiring table, not a
   re-implementation of param semantics.
2. Tunable params DERIVED from each engine's real signature via introspection
   (``inspect.signature``). There is no hand-maintained parallel param schema,
   so an adapter can never advertise a param the engine does not accept — a
   drift-guard test asserts ``accepted_params ⊆ engine signature`` per op.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..engine import add_text, convert, merge, probe, resize, trim


@dataclass(frozen=True)
class OpAdapter:
    """Binds an allowlisted workflow op to an existing vetted engine function."""

    name: str
    engine_fn: Callable[..., Any]
    input_key: str  # inputs key the spec must use: "src" (single) or "srcs" (list)
    engine_input_param: str  # engine positional param that receives the resolved input
    multi_input: bool = False  # True => srcs is a list of refs (e.g. merge -> clips)
    has_output: bool = True  # False => inspection op with no output file (e.g. probe)

    def accepted_params(self) -> frozenset[str]:
        """Tunable params for this op, derived from the engine signature.

        Everything the engine accepts EXCEPT the input-bound param, the output
        path, variadics, and non-JSON callable params (e.g. ``on_progress``).
        """
        excluded = {self.engine_input_param, "output_path"}
        accepted: set[str] = set()
        for pname, param in inspect.signature(self.engine_fn).parameters.items():
            if pname in excluded:
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if "Callable" in _annotation_text(param.annotation):
                continue
            accepted.add(pname)
        return frozenset(accepted)


def _annotation_text(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return ""
    if isinstance(annotation, str):
        return annotation
    return getattr(annotation, "__name__", str(annotation))


# The EXACT MVP allowlist. Anything else fails closed (unsupported_workflow_op).
OP_ADAPTERS: dict[str, OpAdapter] = {
    "probe": OpAdapter("probe", probe, input_key="src", engine_input_param="path", has_output=False),
    "trim": OpAdapter("trim", trim, input_key="src", engine_input_param="input_path"),
    "resize": OpAdapter("resize", resize, input_key="src", engine_input_param="input_path"),
    "convert": OpAdapter("convert", convert, input_key="src", engine_input_param="input_path"),
    "add_text": OpAdapter("add_text", add_text, input_key="src", engine_input_param="input_path"),
    "merge": OpAdapter("merge", merge, input_key="srcs", engine_input_param="clips", multi_input=True),
}

OP_ALLOWLIST: frozenset[str] = frozenset(OP_ADAPTERS)
