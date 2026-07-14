"""Learning subpackage: prompt outcomes, cost ledger, and the learning report.

Privacy-safe, append-only canonical records (design §4.11) plus the derived
learning projection. These are internal record APIs composed over the private
project store; they are not themselves registered MCP tools.
"""

from __future__ import annotations

from kinocut.aivideo.learning.cost import CostTotals, cost_totals, record_cost_event
from kinocut.aivideo.learning.outcomes import prompt_outcomes_for_asset, record_prompt_outcome
from kinocut.aivideo.learning.report import LearningReport, project_learning_report

__all__ = [
    "CostTotals",
    "LearningReport",
    "cost_totals",
    "project_learning_report",
    "prompt_outcomes_for_asset",
    "record_cost_event",
    "record_prompt_outcome",
]
