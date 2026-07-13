"""Generation-lineage graph over durable ``LineageLink`` records (backlog #38).

The graph is an in-memory, read-only projection of the append-only
``lineage_link`` records in the project store. It enforces two structural
invariants when built:

* **No cycles** in the directed derivation edges (a derivative may not be its
  own ancestor through any chain of ``generated_from``/``variant_of``/
  ``repair_of``/``derived_from`` links).
* **No dangling references** — every ``derivative_asset_id`` and every member
  of ``source_asset_ids`` must appear in the caller-supplied set of known asset
  ids (which the caller derives from the project's ``asset_record`` store).

Family-member links (``FAMILY_MEMBER`` relation) are undirected grouping edges:
they participate in family queries but not in ancestor/descendant walks, so they
can never introduce a derivation cycle.
"""

from __future__ import annotations

from collections import defaultdict
from typing import NamedTuple

from kinocut.contracts._errors import INVALID_RECORD, contract_error
from kinocut.contracts._common import AssetId
from kinocut.contracts.registry import LineageLink, LineageRelation

# Relations that create a directed derivation edge (parent → child).
_DERIVATION_RELATIONS = frozenset(
    {
        LineageRelation.GENERATED_FROM,
        LineageRelation.VARIANT_OF,
        LineageRelation.REPAIR_OF,
        LineageRelation.DERIVED_FROM,
    }
)


class LineageGraph(NamedTuple):
    """A validated, read-only view of the generation-lineage graph.

    Construct via :meth:`from_links` (which validates) rather than directly.
    Fields are exposed as named tuples for cheap, immutable access by later
    semantic and beat-planning layers.
    """

    #: child → set of parents (directed derivation edges only).
    parents: dict[str, set[str]]
    #: parent → set of children (directed derivation edges only).
    children: dict[str, set[str]]
    #: asset → set of family-group peers (undirected FAMILY_MEMBER edges).
    family: dict[str, set[str]]
    #: every asset id mentioned in any link (derivatives and sources).
    referenced_assets: frozenset[str]

    @classmethod
    def from_links(
        cls,
        links: list[LineageLink],
        *,
        known_asset_ids: frozenset[str],
    ) -> LineageGraph:
        """Build a validated graph from lineage links and known asset ids.

        Raises ``invalid_record`` if any link references an asset not in
        ``known_asset_ids`` (dangling ref), or if the directed derivation edges
        form a cycle.
        """

        parents: dict[str, set[str]] = defaultdict(set)
        children: dict[str, set[str]] = defaultdict(set)
        family_raw: dict[str, set[str]] = defaultdict(set)
        referenced: set[str] = set()

        for link in links:
            referenced.add(link.derivative_asset_id)
            referenced.update(link.source_asset_ids)
            _check_dangling(link, known_asset_ids)
            if link.relation in _DERIVATION_RELATIONS:
                for src in link.source_asset_ids:
                    parents[link.derivative_asset_id].add(src)
                    children[src].add(link.derivative_asset_id)
            elif link.relation is LineageRelation.FAMILY_MEMBER:
                group = {link.derivative_asset_id, *link.source_asset_ids}
                for member in group:
                    family_raw[member].update(group - {member})

        family = _family_transitive_closure(family_raw)
        graph = cls(
            parents=dict(parents),
            children=dict(children),
            family=dict(family),
            referenced_assets=frozenset(referenced),
        )
        graph._reject_cycles()
        return graph

    def _reject_cycles(self) -> None:
        """Raise ``invalid_record`` if the directed derivation graph has a cycle."""

        color: dict[str, int] = {}  # 0 = visiting, 1 = done

        def _visit(node: str) -> bool:
            marker = color.get(node)
            if marker == 0:
                return True  # back-edge: cycle
            if marker == 1:
                return False
            color[node] = 0
            for parent in self.parents.get(node, ()):
                if parent in self.parents and _visit(parent):
                    return True
            color[node] = 1
            return False

        for node in self.parents:
            if _visit(node):
                raise contract_error(
                    "generation-lineage graph contains a derivation cycle",
                    INVALID_RECORD,
                )

    def ancestors(self, asset_id: AssetId) -> frozenset[str]:
        """Return all transitive parents of ``asset_id`` (its derivation roots)."""

        return self._transitive(asset_id, self.parents)

    def descendants(self, asset_id: AssetId) -> frozenset[str]:
        """Return all transitive children of ``asset_id`` (its derivatives)."""

        return self._transitive(asset_id, self.children)

    def family_peers(self, asset_id: AssetId) -> frozenset[str]:
        """Return every asset sharing a family group with ``asset_id``."""

        return frozenset(self.family.get(asset_id, set()))

    def _transitive(self, asset_id: str, adjacency: dict[str, set[str]]) -> frozenset[str]:
        """Generic breadth-first transitive closure over an adjacency map."""

        result: set[str] = set()
        frontier = list(adjacency.get(asset_id, set()))
        while frontier:
            node = frontier.pop()
            if node in result:
                continue
            result.add(node)
            frontier.extend(adjacency.get(node, set()))
        return frozenset(result)


def _check_dangling(link: LineageLink, known_asset_ids: frozenset[str]) -> None:
    """Raise ``invalid_record`` if a link references an unknown asset."""

    for asset_id in (link.derivative_asset_id, *link.source_asset_ids):
        if asset_id not in known_asset_ids:
            raise contract_error(
                "lineage link references an unknown asset",
                INVALID_RECORD,
            )


def _family_transitive_closure(
    raw: dict[str, set[str]],
) -> dict[str, frozenset[str]]:
    """Compute the transitive closure of the family adjacency map.

    Family membership is an equivalence relation: if A ~ B and B ~ C, then
    A ~ C. A breadth-first flood from each node over the raw adjacency collects
    every peer in its connected component.
    """

    result: dict[str, frozenset[str]] = {}
    for node in raw:
        peers: set[str] = set()
        frontier = list(raw.get(node, set()))
        while frontier:
            peer = frontier.pop()
            if peer == node or peer in peers:
                continue
            peers.add(peer)
            frontier.extend(raw.get(peer, set()))
        result[node] = frozenset(peers)
    return result
