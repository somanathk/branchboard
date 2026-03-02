from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from git_fleet.models import BranchInfo, BranchState, STATE_BADGE_STYLES


class SummaryBar(Static):
    """Header bar showing counts by state."""

    DEFAULT_CSS = """
    SummaryBar {
        dock: top;
        height: 1;
        background: #282a36;
        padding: 0 1;
    }
    """

    def update_counts(self, branches: list[BranchInfo]) -> None:
        counts: dict[BranchState, int] = {}
        for b in branches:
            counts[b.state] = counts.get(b.state, 0) + 1

        parts = Text()
        parts.append(f" {len(branches)} branches ", style="bold white")
        parts.append(" ")

        show_order = [
            BranchState.DIRTY,
            BranchState.UNPUSHED,
            BranchState.PR_CHANGES_REQ,
            BranchState.PR_OPEN,
            BranchState.PR_APPROVED,
            BranchState.PR_DRAFT,
            BranchState.NO_PR,
            BranchState.STALE,
            BranchState.PR_MERGED,
        ]
        for state in show_order:
            count = counts.get(state, 0)
            if count > 0:
                parts.append(f" {count} {state.label} ", style=STATE_BADGE_STYLES[state])
                parts.append(" ")

        self.update(parts)
