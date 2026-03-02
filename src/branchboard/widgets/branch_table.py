from __future__ import annotations

from datetime import datetime, timezone
from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable

from branchboard.models import BranchInfo, BranchState, STATE_PRIORITY


def _relative_time(dt: datetime | None) -> str:
    if dt is None:
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    days = delta.days
    if days == 0:
        hours = delta.seconds // 3600
        if hours == 0:
            return f"{delta.seconds // 60}m ago"
        return f"{hours}h ago"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    return f"{months}mo ago"


def _sort_key_for_date(dt: datetime | None) -> float:
    """Return a timestamp for sorting. None -> very old."""
    if dt is None:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


class SortMode:
    PRIORITY = "priority"
    RECENT = "recent"


class BranchTable(DataTable):
    """Color-coded branch table with filtering, sorting, and Vim navigation."""

    DEFAULT_CSS = """
    BranchTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        # Vim single-row movement
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        # Vim jump to top/bottom
        Binding("g", "scroll_top", "Top", show=False),
        Binding("G", "scroll_bottom", "Bottom", show=False),
        # Vim half-page
        Binding("ctrl+d", "half_page_down", "Half Pg Down", show=False),
        Binding("ctrl+u", "half_page_up", "Half Pg Up", show=False),
        # Vim full-page (also standard PageUp/PageDown already handled by DataTable)
        Binding("ctrl+f", "page_down", "Pg Down", show=False),
        Binding("ctrl+b", "page_up", "Pg Up", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_branches: list[BranchInfo] = []
        self._filtered: list[BranchInfo] = []
        self._search_text = ""
        self._state_filter = "ALL"
        self._sort_mode = SortMode.PRIORITY

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("Repo", "Branch", "State", "Last Activity", "PR#", "Details")

    def _visible_row_count(self) -> int:
        """Approximate number of visible rows in the table viewport."""
        # content_size.height gives the viewport height; each row is 1 cell high
        # Subtract 1 for the header row
        return max(1, self.size.height - 1)

    # -- Vim navigation actions --

    def action_scroll_top(self) -> None:
        """Move cursor to the first row (Vim: gg)."""
        if self.row_count > 0:
            self.move_cursor(row=0)

    def action_scroll_bottom(self) -> None:
        """Move cursor to the last row (Vim: G)."""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)

    def action_half_page_down(self) -> None:
        """Move cursor down by half a page (Vim: Ctrl-d)."""
        if self.row_count == 0:
            return
        half = self._visible_row_count() // 2
        new_row = min(self.cursor_row + half, self.row_count - 1)
        self.move_cursor(row=new_row)

    def action_half_page_up(self) -> None:
        """Move cursor up by half a page (Vim: Ctrl-u)."""
        if self.row_count == 0:
            return
        half = self._visible_row_count() // 2
        new_row = max(self.cursor_row - half, 0)
        self.move_cursor(row=new_row)

    def action_page_down(self) -> None:
        """Move cursor down by a full page (Vim: Ctrl-f)."""
        if self.row_count == 0:
            return
        page = self._visible_row_count()
        new_row = min(self.cursor_row + page, self.row_count - 1)
        self.move_cursor(row=new_row)

    def action_page_up(self) -> None:
        """Move cursor up by a full page (Vim: Ctrl-b)."""
        if self.row_count == 0:
            return
        page = self._visible_row_count()
        new_row = max(self.cursor_row - page, 0)
        self.move_cursor(row=new_row)

    # -- Sort / filter / data --

    @property
    def sort_mode(self) -> str:
        return self._sort_mode

    def toggle_sort(self) -> str:
        """Toggle between priority and recency sort. Returns new mode."""
        if self._sort_mode == SortMode.PRIORITY:
            self._sort_mode = SortMode.RECENT
        else:
            self._sort_mode = SortMode.PRIORITY
        self._apply_filter()
        return self._sort_mode

    def set_branches(self, branches: list[BranchInfo]) -> None:
        self._all_branches = branches
        self._apply_filter()

    def set_search(self, text: str) -> None:
        self._search_text = text.lower()
        self._apply_filter()

    def set_state_filter(self, state: str) -> None:
        self._state_filter = state
        self._apply_filter()

    def _apply_filter(self) -> None:
        filtered = self._all_branches
        if self._search_text:
            filtered = [
                b for b in filtered
                if self._search_text in b.repo_name.lower()
                or self._search_text in b.branch_name.lower()
            ]
        if self._state_filter != "ALL":
            filtered = [b for b in filtered if b.state.value == self._state_filter]

        # Apply sorting
        if self._sort_mode == SortMode.RECENT:
            filtered = sorted(
                filtered,
                key=lambda b: _sort_key_for_date(b.last_commit_date),
                reverse=True,
            )
        else:
            filtered = sorted(
                filtered,
                key=lambda b: (STATE_PRIORITY.get(b.state, 99), b.repo_name, b.branch_name),
            )

        self._filtered = filtered
        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        self.clear()
        for i, b in enumerate(self._filtered):
            color = b.state.color
            state_text = Text(f" {b.state.label} ", style=f"bold {color}")
            pr_num = Text(f"#{b.pr.number}", style=color) if b.pr else Text("")

            detail = ""
            if b.is_dirty:
                detail = f"{len(b.dirty_files)} dirty files"
            elif b.pr:
                detail = b.pr.title[:50]
            elif b.commits_ahead:
                detail = f"{b.commits_ahead} unpushed commit(s)"

            self.add_row(
                Text(b.repo_name),
                Text(b.branch_name, style=color),
                state_text,
                Text(_relative_time(b.last_commit_date)),
                pr_num,
                Text(detail, style="dim" if b.state == BranchState.STALE else ""),
                key=f"{b.repo_path}:{b.branch_name}:{i}",
            )

    def get_selected_branch(self) -> BranchInfo | None:
        if self.cursor_row is None or self.cursor_row >= len(self._filtered):
            return None
        return self._filtered[self.cursor_row]
