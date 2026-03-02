"""Generate screenshots of git-fleet with fake data for documentation."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Input, Select

from git_fleet.models import BranchInfo, BranchState, PRInfo
from git_fleet.classify import classify_all
from git_fleet.screens.detail import DetailScreen
from git_fleet.widgets.branch_table import BranchTable
from git_fleet.widgets.filter_bar import FilterBar
from git_fleet.widgets.summary_bar import SummaryBar

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"

now = datetime.now(timezone.utc)


def _ago(**kwargs) -> datetime:
    return now - timedelta(**kwargs)


FAKE_BRANCHES: list[BranchInfo] = [
    # DIRTY branches
    BranchInfo(
        repo_name="atlas-backend",
        repo_path="/home/dev/repos/atlas-backend",
        branch_name="feature/user-auth-refactor",
        is_current=True,
        is_dirty=True,
        dirty_files=["M src/auth/oauth.py", "M src/auth/jwt.py", "?? src/auth/mfa.py", "M tests/test_auth.py", "M config/auth.yaml"],
        has_upstream=True,
        last_commit_date=_ago(hours=2),
        last_commit_msg="WIP: migrate to OAuth2 PKCE flow",
        remote_url="git@github.com:acme-corp/atlas-backend.git",
    ),
    BranchInfo(
        repo_name="nova-ui",
        repo_path="/home/dev/repos/nova-ui",
        branch_name="fix/dashboard-memory-leak",
        is_current=True,
        is_dirty=True,
        dirty_files=["M src/components/Dashboard.tsx", "M src/hooks/useWebSocket.ts", "?? src/utils/cleanup.ts"],
        has_upstream=True,
        last_commit_date=_ago(hours=6),
        last_commit_msg="debug: add memory profiling hooks",
        remote_url="git@github.com:acme-corp/nova-ui.git",
        pr=PRInfo(number=342, title="Fix WebSocket memory leak in Dashboard", state="OPEN", url="https://github.com/acme-corp/nova-ui/pull/342", review_decision="CHANGES_REQUESTED", reviewers=["sarah-dev", "mike-ops"], head_branch="fix/dashboard-memory-leak", base_branch="main", created_at="2026-02-25T10:00:00Z", updated_at="2026-03-01T14:30:00Z"),
    ),
    BranchInfo(
        repo_name="data-pipeline",
        repo_path="/home/dev/repos/data-pipeline",
        branch_name="main",
        is_current=True,
        is_dirty=True,
        dirty_files=["M docker-compose.yml", "?? .env.local"],
        has_upstream=True,
        last_commit_date=_ago(days=1),
        last_commit_msg="update kafka broker config for staging",
        remote_url="git@github.com:acme-corp/data-pipeline.git",
    ),
    BranchInfo(
        repo_name="mercury-api",
        repo_path="/home/dev/repos/mercury-api",
        branch_name="feature/rate-limiting",
        is_current=True,
        is_dirty=True,
        dirty_files=["M src/middleware/ratelimit.go", "M go.mod", "M go.sum"],
        has_upstream=True,
        last_commit_date=_ago(days=3),
        last_commit_msg="implement sliding window rate limiter",
        remote_url="git@github.com:acme-corp/mercury-api.git",
    ),
    # UNPUSHED
    BranchInfo(
        repo_name="orbit-scheduler",
        repo_path="/home/dev/repos/orbit-scheduler",
        branch_name="feature/cron-v2",
        has_upstream=False,
        commits_ahead=3,
        last_commit_date=_ago(days=2),
        last_commit_msg="add cron expression parser with timezone support",
        remote_url="git@github.com:acme-corp/orbit-scheduler.git",
    ),
    BranchInfo(
        repo_name="atlas-backend",
        repo_path="/home/dev/repos/atlas-backend",
        branch_name="experiment/graphql-subscriptions",
        has_upstream=False,
        commits_ahead=7,
        last_commit_date=_ago(days=5),
        last_commit_msg="POC: GraphQL subscriptions with Redis PubSub",
        remote_url="git@github.com:acme-corp/atlas-backend.git",
    ),
    # PR_CHANGES_REQ
    BranchInfo(
        repo_name="nova-ui",
        repo_path="/home/dev/repos/nova-ui",
        branch_name="feature/dark-mode",
        has_upstream=True,
        last_commit_date=_ago(days=4),
        last_commit_msg="add theme toggle and persist preference",
        remote_url="git@github.com:acme-corp/nova-ui.git",
        pr=PRInfo(number=318, title="Add dark mode with system preference detection", state="OPEN", url="https://github.com/acme-corp/nova-ui/pull/318", review_decision="CHANGES_REQUESTED", reviewers=["lisa-design"], head_branch="feature/dark-mode", base_branch="main", created_at="2026-02-20T09:00:00Z", updated_at="2026-02-28T16:00:00Z"),
    ),
    # PR_OPEN
    BranchInfo(
        repo_name="atlas-backend",
        repo_path="/home/dev/repos/atlas-backend",
        branch_name="feature/audit-logging",
        has_upstream=True,
        last_commit_date=_ago(days=1),
        last_commit_msg="add structured audit log middleware",
        remote_url="git@github.com:acme-corp/atlas-backend.git",
        pr=PRInfo(number=891, title="Add audit logging for all admin endpoints", state="OPEN", url="https://github.com/acme-corp/atlas-backend/pull/891", review_decision="REVIEW_REQUIRED", reviewers=["james-sec"], head_branch="feature/audit-logging", base_branch="main", created_at="2026-02-28T11:00:00Z", updated_at="2026-03-01T09:00:00Z"),
    ),
    BranchInfo(
        repo_name="mercury-api",
        repo_path="/home/dev/repos/mercury-api",
        branch_name="fix/connection-pool-exhaustion",
        has_upstream=True,
        last_commit_date=_ago(days=2),
        last_commit_msg="fix: increase pool size and add health checks",
        remote_url="git@github.com:acme-corp/mercury-api.git",
        pr=PRInfo(number=156, title="Fix DB connection pool exhaustion under load", state="OPEN", url="https://github.com/acme-corp/mercury-api/pull/156", review_decision="", head_branch="fix/connection-pool-exhaustion", base_branch="main", created_at="2026-02-27T14:00:00Z", updated_at="2026-02-28T10:00:00Z"),
    ),
    BranchInfo(
        repo_name="data-pipeline",
        repo_path="/home/dev/repos/data-pipeline",
        branch_name="feature/parquet-sink",
        has_upstream=True,
        last_commit_date=_ago(days=6),
        last_commit_msg="add S3 parquet sink connector with schema evolution",
        remote_url="git@github.com:acme-corp/data-pipeline.git",
        pr=PRInfo(number=73, title="Add Parquet sink connector for S3", state="OPEN", url="https://github.com/acme-corp/data-pipeline/pull/73", review_decision="REVIEW_REQUIRED", head_branch="feature/parquet-sink", base_branch="main", created_at="2026-02-22T08:00:00Z", updated_at="2026-02-24T12:00:00Z"),
    ),
    # PR_APPROVED
    BranchInfo(
        repo_name="orbit-scheduler",
        repo_path="/home/dev/repos/orbit-scheduler",
        branch_name="fix/timezone-drift",
        has_upstream=True,
        last_commit_date=_ago(days=1),
        last_commit_msg="fix DST transition edge case in scheduler",
        remote_url="git@github.com:acme-corp/orbit-scheduler.git",
        pr=PRInfo(number=44, title="Fix timezone drift during DST transitions", state="OPEN", url="https://github.com/acme-corp/orbit-scheduler/pull/44", review_decision="APPROVED", reviewers=["carlos-infra"], head_branch="fix/timezone-drift", base_branch="main", created_at="2026-02-28T15:00:00Z", updated_at="2026-03-01T11:00:00Z"),
    ),
    # PR_DRAFT
    BranchInfo(
        repo_name="nova-ui",
        repo_path="/home/dev/repos/nova-ui",
        branch_name="feature/ai-suggestions",
        has_upstream=True,
        last_commit_date=_ago(days=3),
        last_commit_msg="WIP: integrate LLM completion API",
        remote_url="git@github.com:acme-corp/nova-ui.git",
        pr=PRInfo(number=350, title="[WIP] AI-powered code suggestions panel", state="OPEN", url="https://github.com/acme-corp/nova-ui/pull/350", is_draft=True, head_branch="feature/ai-suggestions", base_branch="main", created_at="2026-02-26T10:00:00Z", updated_at="2026-02-27T16:00:00Z"),
    ),
    BranchInfo(
        repo_name="infra-terraform",
        repo_path="/home/dev/repos/infra-terraform",
        branch_name="feature/multi-region",
        has_upstream=True,
        last_commit_date=_ago(days=8),
        last_commit_msg="WIP: add ap-southeast-1 region module",
        remote_url="git@github.com:acme-corp/infra-terraform.git",
        pr=PRInfo(number=29, title="[WIP] Multi-region deployment support", state="OPEN", url="https://github.com/acme-corp/infra-terraform/pull/29", is_draft=True, head_branch="feature/multi-region", base_branch="main", created_at="2026-02-18T09:00:00Z", updated_at="2026-02-22T14:00:00Z"),
    ),
    # NO_PR
    BranchInfo(
        repo_name="mercury-api",
        repo_path="/home/dev/repos/mercury-api",
        branch_name="experiment/grpc-migration",
        has_upstream=True,
        last_commit_date=_ago(days=5),
        last_commit_msg="prototype: gRPC service definitions",
        remote_url="git@github.com:acme-corp/mercury-api.git",
    ),
    BranchInfo(
        repo_name="toolbox",
        repo_path="/home/dev/repos/toolbox",
        branch_name="feature/log-aggregator",
        has_upstream=True,
        last_commit_date=_ago(days=9),
        last_commit_msg="add multi-source log aggregator CLI",
        remote_url="git@github.com:acme-corp/toolbox.git",
    ),
    # STALE
    BranchInfo(
        repo_name="atlas-backend",
        repo_path="/home/dev/repos/atlas-backend",
        branch_name="feature/websocket-notifications",
        has_upstream=True,
        last_commit_date=_ago(days=45),
        last_commit_msg="initial websocket notification handler",
        remote_url="git@github.com:acme-corp/atlas-backend.git",
    ),
    BranchInfo(
        repo_name="data-pipeline",
        repo_path="/home/dev/repos/data-pipeline",
        branch_name="experiment/arrow-flight",
        has_upstream=True,
        last_commit_date=_ago(days=60),
        last_commit_msg="POC: Apache Arrow Flight for data transfer",
        remote_url="git@github.com:acme-corp/data-pipeline.git",
    ),
    BranchInfo(
        repo_name="nova-ui",
        repo_path="/home/dev/repos/nova-ui",
        branch_name="feature/virtual-scroll-v1",
        has_upstream=True,
        last_commit_date=_ago(days=30),
        last_commit_msg="virtual scroll prototype for large tables",
        remote_url="git@github.com:acme-corp/nova-ui.git",
    ),
    BranchInfo(
        repo_name="toolbox",
        repo_path="/home/dev/repos/toolbox",
        branch_name="fix/yaml-parser-edge-case",
        has_upstream=True,
        last_commit_date=_ago(days=22),
        last_commit_msg="handle multiline strings in YAML parser",
        remote_url="git@github.com:acme-corp/toolbox.git",
    ),
    # PR_MERGED
    BranchInfo(
        repo_name="atlas-backend",
        repo_path="/home/dev/repos/atlas-backend",
        branch_name="feature/password-policy",
        has_upstream=True,
        last_commit_date=_ago(days=3),
        last_commit_msg="enforce password complexity rules",
        remote_url="git@github.com:acme-corp/atlas-backend.git",
        pr=PRInfo(number=885, title="Enforce configurable password policy", state="MERGED", url="https://github.com/acme-corp/atlas-backend/pull/885", review_decision="APPROVED", head_branch="feature/password-policy", base_branch="main", created_at="2026-02-24T10:00:00Z", updated_at="2026-02-27T15:00:00Z"),
    ),
    BranchInfo(
        repo_name="nova-ui",
        repo_path="/home/dev/repos/nova-ui",
        branch_name="fix/accessibility-contrast",
        has_upstream=True,
        last_commit_date=_ago(days=5),
        last_commit_msg="fix WCAG 2.1 contrast ratio violations",
        remote_url="git@github.com:acme-corp/nova-ui.git",
        pr=PRInfo(number=310, title="Fix accessibility contrast issues (WCAG 2.1)", state="MERGED", url="https://github.com/acme-corp/nova-ui/pull/310", review_decision="APPROVED", head_branch="fix/accessibility-contrast", base_branch="main", created_at="2026-02-20T13:00:00Z", updated_at="2026-02-25T09:00:00Z"),
    ),
    BranchInfo(
        repo_name="orbit-scheduler",
        repo_path="/home/dev/repos/orbit-scheduler",
        branch_name="feature/job-retry-backoff",
        has_upstream=True,
        last_commit_date=_ago(days=7),
        last_commit_msg="add exponential backoff for failed jobs",
        remote_url="git@github.com:acme-corp/orbit-scheduler.git",
        pr=PRInfo(number=41, title="Add exponential backoff retry strategy", state="MERGED", url="https://github.com/acme-corp/orbit-scheduler/pull/41", review_decision="APPROVED", head_branch="feature/job-retry-backoff", base_branch="main", created_at="2026-02-18T11:00:00Z", updated_at="2026-02-23T10:00:00Z"),
    ),
]


class ScreenshotApp(App):
    """Fake app for taking screenshots."""

    TITLE = "git-fleet"
    CSS_PATH = "../src/git_fleet/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("o", "open_pr", "Open PR"),
        Binding("s", "toggle_sort", "Sort"),
    ]

    def __init__(self, branches: list[BranchInfo], **kwargs):
        super().__init__(**kwargs)
        self._branches = branches

    def compose(self) -> ComposeResult:
        yield SummaryBar(id="summary")
        yield FilterBar()
        with Vertical(id="main-container"):
            yield BranchTable(id="branch-table")
        yield Footer()

    def on_mount(self) -> None:
        classify_all(self._branches)
        table = self.query_one("#branch-table", BranchTable)
        table.set_branches(self._branches)
        summary = self.query_one("#summary", SummaryBar)
        summary.update_counts(self._branches)
        table.focus()


async def take_screenshots():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    branches = list(FAKE_BRANCHES)

    # 1. Main dashboard view
    print("Taking main dashboard screenshot...")
    app = ScreenshotApp(branches)
    async with app.run_test(size=(140, 36)) as pilot:
        await asyncio.sleep(0.5)
        svg = app.export_screenshot()
        (SCREENSHOTS_DIR / "main-dashboard.svg").write_text(svg)
        print("  -> main-dashboard.svg")

        # 2. Move cursor to a PR row and open detail
        print("Taking detail modal screenshot...")
        table = app.query_one("#branch-table", BranchTable)
        # Row index 7 should be the first PR_OPEN (atlas-backend/feature/audit-logging)
        table.move_cursor(row=7)
        await asyncio.sleep(0.2)
        await pilot.press("enter")
        await asyncio.sleep(0.3)
        svg = app.export_screenshot()
        (SCREENSHOTS_DIR / "detail-modal.svg").write_text(svg)
        print("  -> detail-modal.svg")
        await pilot.press("escape")
        await asyncio.sleep(0.2)

        # 3. Filter by state - PR_OPEN
        print("Taking filtered view screenshot...")
        table.set_state_filter("PR_OPEN")
        await asyncio.sleep(0.3)
        svg = app.export_screenshot()
        (SCREENSHOTS_DIR / "filtered-view.svg").write_text(svg)
        print("  -> filtered-view.svg")

        # Reset filter
        table.set_state_filter("ALL")
        await asyncio.sleep(0.2)

        # 4. Sort by recency
        print("Taking recency sort screenshot...")
        table.toggle_sort()
        await asyncio.sleep(0.3)
        svg = app.export_screenshot()
        (SCREENSHOTS_DIR / "recency-sort.svg").write_text(svg)
        print("  -> recency-sort.svg")

        # 5. Dirty detail
        print("Taking dirty detail screenshot...")
        table.toggle_sort()  # back to priority
        await asyncio.sleep(0.2)
        table.move_cursor(row=0)
        await asyncio.sleep(0.2)
        await pilot.press("enter")
        await asyncio.sleep(0.3)
        svg = app.export_screenshot()
        (SCREENSHOTS_DIR / "dirty-detail.svg").write_text(svg)
        print("  -> dirty-detail.svg")

    print(f"\nAll screenshots saved to {SCREENSHOTS_DIR}/")


if __name__ == "__main__":
    asyncio.run(take_screenshots())
