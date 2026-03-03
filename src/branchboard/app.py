from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Input, Select
from textual.worker import Worker, WorkerState

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
    CSS_PATH = Path(__file__).parent / "app.tcss"

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
        self._loading: LoadingScreen | None = None

    def compose(self) -> ComposeResult:
        yield SummaryBar(id="summary")
        yield FilterBar()
        with Vertical(id="main-container"):
            yield BranchTable(id="branch-table")
        yield Footer()

    def on_mount(self) -> None:
        # Push the loading screen synchronously so Textual renders it on the
        # very first frame, then immediately return so the event loop is free.
        self._loading = LoadingScreen()
        self.push_screen(self._loading)
        # Kick off the scan as a background worker — decoupled from on_mount
        # so the loading screen is already visible before work begins.
        self.run_worker(self._scan(), exclusive=True, name="scan")

    async def _scan(self) -> None:
        """Background worker: scan repos, fetch PRs, classify, update UI."""
        loading = self._loading

        async def on_git_progress(done: int, total: int) -> None:
            if loading:
                loading.update_progress(done, total)

        # Phase 1: git scanning — progress bar
        branches = await scan_all_repos(self._scan_path, on_progress=on_git_progress)

        # Phase 2: GitHub PR fetching — spinner
        if loading:
            loading.set_phase("Fetching PR data from GitHub…")
        await fetch_all_prs(branches, use_cache=self._use_cache)

        # Phase 3: classify + populate table while loading modal still covers it
        classify_all(branches)
        self._branches = branches
        self._update_display()

        # Pop only after table is fully populated — no blank flash
        if self._loading and self._loading in self.screen_stack:
            self.pop_screen()
        self._loading = None

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

    def action_refresh(self) -> None:
        clear_cache()
        self._use_cache = False
        self._loading = LoadingScreen()
        self.push_screen(self._loading)
        self.run_worker(self._scan(), exclusive=True, name="scan")

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
