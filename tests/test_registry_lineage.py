"""Lineage-graph tests: cycles, dangling refs, ancestor/descendant/family walks.

The graph is a read-only projection of ``LineageLink`` records, validated for
structural integrity at construction time.
"""

from __future__ import annotations

import pytest

from kinocut.errors import MCPVideoError
from kinocut.registry._lineage import LineageGraph
from kinocut.contracts.registry import LineageLink
from tests.registry_fixtures import lineage_link_kwargs

_A = "sha256:" + "1" * 64
_B = "sha256:" + "2" * 64
_C = "sha256:" + "3" * 64
_D = "sha256:" + "4" * 64
_UNKNOWN = "sha256:" + "9" * 64


def _link(
    derivative: str,
    sources: tuple[str, ...],
    relation: str = "generated_from",
    project_id: str = "proj-alpha",
) -> LineageLink:
    return LineageLink(
        **lineage_link_kwargs(
            project_id=project_id,
            derivative_asset_id=derivative,
            source_asset_ids=sources,
            relation=relation,
        )
    )


def _known(*ids: str) -> frozenset[str]:
    return frozenset(ids)


def test_empty_graph_is_valid():
    graph = LineageGraph.from_links([], known_asset_ids=_known(_A))
    assert graph.ancestors(_A) == frozenset()
    assert graph.descendants(_A) == frozenset()


def test_linear_ancestry():
    """A → B → C (C is generated from B, B from A)."""

    links = [
        _link(_B, (_A,)),  # B derived from A
        _link(_C, (_B,)),  # C derived from B
    ]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C))
    assert graph.ancestors(_C) == frozenset({_A, _B})
    assert graph.descendants(_A) == frozenset({_B, _C})
    assert graph.ancestors(_A) == frozenset()
    assert graph.descendants(_C) == frozenset()


def test_multi_source_derivation():
    """C is generated from both A and B."""

    links = [_link(_C, (_A, _B))]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C))
    assert graph.ancestors(_C) == frozenset({_A, _B})


def test_cycle_is_rejected():
    """A → B → A forms a derivation cycle and must fail."""

    links = [
        _link(_B, (_A,)),
        _link(_A, (_B,)),
    ]
    with pytest.raises(MCPVideoError):
        LineageGraph.from_links(links, known_asset_ids=_known(_A, _B))


def test_self_cycle_through_three_nodes_rejected():
    """A → B → C → A is a longer cycle."""

    links = [
        _link(_B, (_A,)),
        _link(_C, (_B,)),
        _link(_A, (_C,)),
    ]
    with pytest.raises(MCPVideoError):
        LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C))


def test_dangling_derivative_rejected():
    """A link referencing an unknown derivative asset fails."""

    links = [_link(_UNKNOWN, (_A,))]
    with pytest.raises(MCPVideoError):
        LineageGraph.from_links(links, known_asset_ids=_known(_A))


def test_dangling_source_rejected():
    """A link referencing an unknown source asset fails."""

    links = [_link(_B, (_UNKNOWN,))]
    with pytest.raises(MCPVideoError):
        LineageGraph.from_links(links, known_asset_ids=_known(_A, _B))


def test_family_member_is_undirected():
    """FAMILY_MEMBER links create symmetric grouping, not derivation edges."""

    links = [
        _link(_A, (_B,), relation="family_member"),
    ]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B))
    # No derivation edges — family links don't participate in ancestry.
    assert graph.ancestors(_A) == frozenset()
    assert graph.descendants(_B) == frozenset()
    # But they do create family peers.
    assert graph.family_peers(_A) == frozenset({_B})
    assert graph.family_peers(_B) == frozenset({_A})


def test_family_group_transitive():
    """A family of three all know each other."""

    links = [
        _link(_A, (_B,), relation="family_member"),
        _link(_B, (_C,), relation="family_member"),
    ]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C))
    assert graph.family_peers(_A) == frozenset({_B, _C})


def test_referenced_assets_collected():
    """Every asset mentioned in any link is in referenced_assets."""

    links = [
        _link(_B, (_A,)),
        _link(_C, (_B,)),
    ]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C))
    assert graph.referenced_assets == frozenset({_A, _B, _C})


def test_family_member_does_not_create_cycle():
    """Even if A is family of B and B derives from A, no cycle."""

    links = [
        _link(_A, (_B,), relation="family_member"),
        _link(_B, (_A,), relation="derived_from"),
    ]
    # B is derived from A, and A is family of B — no cycle in derivation edges.
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B))
    assert graph.ancestors(_B) == frozenset({_A})


def test_diamond_dependency_no_cycle():
    """A → B, A → C, B → D, C → D (D has two derivation paths)."""

    links = [
        _link(_B, (_A,)),
        _link(_C, (_A,)),
        _link(_D, (_B, _C)),
    ]
    graph = LineageGraph.from_links(links, known_asset_ids=_known(_A, _B, _C, _D))
    assert graph.ancestors(_D) == frozenset({_A, _B, _C})
    assert graph.descendants(_A) == frozenset({_B, _C, _D})
