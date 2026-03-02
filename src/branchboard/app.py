from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Input, Select

from branchboard.cache import clear_cache
from branchboard.classify import classify_all
from branchboard.github import fetch_all_prs
from branchboard.models import BranchInfo
from branchboard.scanner import scan_all_repos
from branchboard.screens.detail import DetailScreen
from branchboard.screens.loading import LoadingScreen
from branchboard.widgets.branch_table import BranchTable
from branchboard.widgets.filter_bar import FilterBar
from branchboard.widgets.summary_bar import SummaryBar


class GitFleetApp(App):
    """Git Branch Dashboard TUI."""

    TITLE = "branchboard"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("o", "open_pr", "Open PR", priority=True),
        Binding("s", "toggle_sort", "Sort", priority=True),
        Binding("slash", "focus_search", "/ Search", show=False),
        Binding("escape", "focus_table", "Esc Table", show=False),
    ]

    def __init__(self, scan_path: str, use_cache: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self._scan_path = scan_path
        self._use_cache = use_cache
        self._branches: list[BranchInfo] = []

    def compose(self) -> ComposeResult:
        yield SummaryBar(id="summary")
        yield FilterBar()
        with Vertical(id="main-container"):
            yield BranchTable(id="branch-table")
        yield Footer()

    async def on_mount(self) -> None:
        await self._do_scan()

    async def _do_scan(self) -> None:
        loading = LoadingScreen()
        self.push_screen(loading)

        try:
            # Phase 1: git scanning
            async def on_git_progress(done: int, total: int) -> None:
                loading.update_progress(done, total)

            branches = await scan_all_repos(self._scan_path, on_progress=on_git_progress)

            # Phase 2: GitHub PR fetching
            loading.set_phase("Fetching PR data from GitHub…")
            await fetch_all_prs(branches, use_cache=self._use_cache)

            # Phase 3: classify
            classify_all(branches)
            self._branches = branches
        finally:
            self.pop_screen()

        # Update UI
        self._update_display()
        # Focus the table so keyboard shortcuts work
        self.query_one("#branch-table", BranchTable).focus()

    def _update_display(self) -> None:
        table = self.query_one("#branch-table", BranchTable)
        table.set_branches(self._branches)
        summary = self.query_one("#summary", SummaryBar)
        summary.update_counts(self._branches)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_show_detail()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            table = self.query_one("#branch-table", BranchTable)
            table.set_search(event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "state-select":
            table = self.query_one("#branch-table", BranchTable)
            table.set_state_filter(str(event.value))

    async def action_refresh(self) -> None:
        clear_cache()
        self._use_cache = False
        await self._do_scan()

    def action_open_pr(self) -> None:
        table = self.query_one("#branch-table", BranchTable)
        branch = table.get_selected_branch()
        if branch and branch.pr and branch.pr.url:
            webbrowser.open(branch.pr.url)
        else:
            self.notify("No PR URL for this branch", severity="warning")

    def action_show_detail(self) -> None:
        table = self.query_one("#branch-table", BranchTable)
        branch = table.get_selected_branch()
        if branch:
            self.push_screen(DetailScreen(branch))

    def action_toggle_sort(self) -> None:
        table = self.query_one("#branch-table", BranchTable)
        new_mode = table.toggle_sort()
        label = "Most Recent" if new_mode == "recent" else "Priority"
        self.notify(f"Sort: {label}", timeout=2)

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_focus_table(self) -> None:
        self.query_one("#branch-table", BranchTable).focus()

    def _set_state_filter(self, state: str) -> None:
        select = self.query_one("#state-select", Select)
        select.value = state
        table = self.query_one("#branch-table", BranchTable)
        table.set_state_filter(state)
