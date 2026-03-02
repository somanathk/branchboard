from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Middle, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Label, Static

from branchboard.models import BranchInfo


class DetailScreen(ModalScreen[None]):
    """Modal showing full branch/PR details."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    DetailScreen {
        align: center middle;
    }

    #detail-box {
        width: 80;
        max-height: 80%;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }

    #detail-title {
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    #detail-content {
        width: 100%;
    }
    """

    def __init__(self, branch: BranchInfo, **kwargs) -> None:
        super().__init__(**kwargs)
        self._branch = branch

    def compose(self) -> ComposeResult:
        b = self._branch
        with Middle():
            with VerticalScroll(id="detail-box"):
                yield Label(
                    f"{b.repo_name} / {b.branch_name}",
                    id="detail-title",
                )
                yield Static(self._build_content(), id="detail-content")

    def _build_content(self) -> Text:
        b = self._branch
        lines = Text()

        lines.append("State: ", style="bold")
        lines.append(f"{b.state.label}\n", style=b.state.color)

        lines.append("Repo: ", style="bold")
        lines.append(f"{b.repo_path}\n")

        if b.last_commit_date:
            lines.append("Last commit: ", style="bold")
            lines.append(f"{b.last_commit_date.strftime('%Y-%m-%d %H:%M')} — {b.last_commit_msg}\n")

        if b.has_upstream:
            lines.append("Upstream: ", style="bold")
            ahead_behind = []
            if b.commits_ahead:
                ahead_behind.append(f"{b.commits_ahead} ahead")
            if b.commits_behind:
                ahead_behind.append(f"{b.commits_behind} behind")
            lines.append(", ".join(ahead_behind) if ahead_behind else "up to date")
            lines.append("\n")

        if b.is_dirty and b.dirty_files:
            lines.append(f"\nDirty files ({len(b.dirty_files)}):\n", style="bold red")
            for f in b.dirty_files[:30]:
                lines.append(f"  {f}\n", style="red")
            if len(b.dirty_files) > 30:
                lines.append(f"  … and {len(b.dirty_files) - 30} more\n", style="dim")

        if b.pr:
            pr = b.pr
            lines.append(f"\nPR #{pr.number}: ", style="bold")
            lines.append(f"{pr.title}\n")
            lines.append("URL: ", style="bold")
            lines.append(f"{pr.url}\n")
            lines.append("State: ", style="bold")
            lines.append(f"{pr.state}")
            if pr.is_draft:
                lines.append(" (draft)")
            lines.append("\n")
            if pr.review_decision:
                lines.append("Review: ", style="bold")
                lines.append(f"{pr.review_decision}\n")
            if pr.reviewers:
                lines.append("Reviewers: ", style="bold")
                lines.append(", ".join(pr.reviewers))
                lines.append("\n")
            lines.append("Base: ", style="bold")
            lines.append(f"{pr.base_branch}\n")

        lines.append("\n[Esc] close  [o] open PR in browser", style="dim")
        return lines

    def action_dismiss(self) -> None:
        self.dismiss(None)
