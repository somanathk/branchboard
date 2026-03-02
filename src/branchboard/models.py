from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class BranchState(enum.Enum):
    DIRTY = "DIRTY"
    UNPUSHED = "UNPUSHED"
    PR_CHANGES_REQ = "PR_CHANGES_REQ"
    PR_OPEN = "PR_OPEN"
    PR_APPROVED = "PR_APPROVED"
    PR_DRAFT = "PR_DRAFT"
    NO_PR = "NO_PR"
    STALE = "STALE"
    PR_MERGED = "PR_MERGED"

    @property
    def color(self) -> str:
        return _STATE_COLORS[self]

    @property
    def label(self) -> str:
        return _STATE_LABELS[self]


# Use explicit hex colors for better terminal contrast
_STATE_COLORS: dict[BranchState, str] = {
    BranchState.DIRTY: "#ff5555",          # bright red
    BranchState.UNPUSHED: "#ff7979",       # lighter red/salmon
    BranchState.PR_CHANGES_REQ: "#ffb86c", # orange
    BranchState.PR_OPEN: "#f1fa8c",        # yellow
    BranchState.PR_APPROVED: "#50fa7b",    # green
    BranchState.PR_DRAFT: "#8be9fd",       # cyan
    BranchState.NO_PR: "#bd93f9",          # purple
    BranchState.STALE: "#6272a4",          # muted grey-blue
    BranchState.PR_MERGED: "#69ff94",      # bright green
}

_STATE_LABELS: dict[BranchState, str] = {
    BranchState.DIRTY: "Dirty",
    BranchState.UNPUSHED: "Unpushed",
    BranchState.PR_CHANGES_REQ: "Changes Req",
    BranchState.PR_OPEN: "PR Open",
    BranchState.PR_APPROVED: "PR Approved",
    BranchState.PR_DRAFT: "PR Draft",
    BranchState.NO_PR: "No PR",
    BranchState.STALE: "Stale",
    BranchState.PR_MERGED: "PR Merged",
}

# Priority for sorting — lower = more important (shows first)
STATE_PRIORITY: dict[BranchState, int] = {
    BranchState.DIRTY: 0,
    BranchState.UNPUSHED: 1,
    BranchState.PR_CHANGES_REQ: 2,
    BranchState.PR_OPEN: 3,
    BranchState.PR_APPROVED: 4,
    BranchState.PR_DRAFT: 5,
    BranchState.NO_PR: 6,
    BranchState.STALE: 7,
    BranchState.PR_MERGED: 8,
}

# State label colors for the summary bar (bolder/more visible)
STATE_BADGE_STYLES: dict[BranchState, str] = {
    BranchState.DIRTY: "bold #ff5555",
    BranchState.UNPUSHED: "bold #ff7979",
    BranchState.PR_CHANGES_REQ: "bold #ffb86c",
    BranchState.PR_OPEN: "bold #f1fa8c",
    BranchState.PR_APPROVED: "bold #50fa7b",
    BranchState.PR_DRAFT: "bold #8be9fd",
    BranchState.NO_PR: "bold #bd93f9",
    BranchState.STALE: "#6272a4",
    BranchState.PR_MERGED: "bold #69ff94",
}


@dataclass
class PRInfo:
    number: int
    title: str
    state: str  # OPEN, CLOSED, MERGED
    url: str
    is_draft: bool = False
    review_decision: str = ""  # APPROVED, CHANGES_REQUESTED, REVIEW_REQUIRED, ""
    reviewers: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    head_branch: str = ""
    base_branch: str = ""


@dataclass
class BranchInfo:
    repo_name: str
    repo_path: str
    branch_name: str
    is_current: bool = False
    is_dirty: bool = False
    dirty_files: list[str] = field(default_factory=list)
    has_upstream: bool = False
    commits_ahead: int = 0
    commits_behind: int = 0
    last_commit_date: datetime | None = None
    last_commit_msg: str = ""
    remote_url: str = ""
    pr: PRInfo | None = None
    state: BranchState = BranchState.NO_PR
