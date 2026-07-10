"""Compatibility package alias for Kinocut's original ``mcp_video`` import."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys

import kinocut as _kinocut
from kinocut import *  # noqa: F403


class _KinocutAliasLoader(importlib.abc.Loader):
    def __init__(self, canonical_name: str) -> None:
        self.canonical_name = canonical_name
        self._metadata = {}

    def create_module(self, _spec: importlib.machinery.ModuleSpec):
        module = importlib.import_module(self.canonical_name)
        self._metadata = {
            name: getattr(module, name, None)
            for name in ("__spec__", "__loader__", "__package__", "__file__", "__cached__")
        }
        return module

    def exec_module(self, module) -> None:
        for name, value in self._metadata.items():
            setattr(module, name, value)


class _KinocutAliasFinder(importlib.abc.MetaPathFinder):
    _kinocut_legacy_alias_finder = True

    def find_spec(self, fullname: str, _path=None, _target=None):
        if not fullname.startswith("mcp_video."):
            return None

        canonical_name = f"kinocut.{fullname.removeprefix('mcp_video.')}"
        canonical_spec = importlib.util.find_spec(canonical_name)
        if canonical_spec is None:
            return None
        return importlib.util.spec_from_loader(
            fullname,
            _KinocutAliasLoader(canonical_name),
            is_package=canonical_spec.submodule_search_locations is not None,
        )


if not any(getattr(finder, "_kinocut_legacy_alias_finder", False) for finder in sys.meta_path):
    sys.meta_path.insert(0, _KinocutAliasFinder())

for _name, _module in tuple(sys.modules.items()):
    if _name.startswith("kinocut."):
        sys.modules.setdefault(f"mcp_video.{_name.removeprefix('kinocut.')}", _module)

for _name, _module in tuple(sys.modules.items()):
    if _name.startswith("mcp_video."):
        _parent_name, _child_name = _name.rsplit(".", 1)
        if _parent := sys.modules.get(_parent_name):
            setattr(_parent, _child_name, _module)

__version__ = _kinocut.__version__
__all__ = [*_kinocut.__all__, "__version__"]
__path__ = _kinocut.__path__


if __name__ == "__main__":
    from kinocut.__main__ import main

    main()
