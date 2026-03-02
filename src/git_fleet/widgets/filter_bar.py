from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Select
from textual.widget import Widget

from git_fleet.models import BranchState


_STATE_OPTIONS: list[tuple[str, str]] = [
    ("All States", "ALL"),
] + [(s.label, s.value) for s in BranchState]


class FilterBar(Widget):
    """Search input + state dropdown."""

    DEFAULT_CSS = """
    FilterBar {
        dock: top;
        height: 3;
        layout: horizontal;
        padding: 0 1;
    }

    FilterBar Input {
        width: 1fr;
        margin-right: 1;
    }

    FilterBar Select {
        width: 28;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search repo/branch…", id="search-input")
        yield Select(_STATE_OPTIONS, value="ALL", id="state-select", allow_blank=False)
