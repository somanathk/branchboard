from __future__ import annotations

from datetime import datetime, timezone, timedelta
from branchboard.models import BranchInfo, BranchState, STATE_PRIORITY

_STALE_DAYS = 14


def classify_branch(branch: BranchInfo) -> BranchState:
    """Determine the state of a single branch."""
    # Dirty takes highest priority
    if branch.is_dirty:
        return BranchState.DIRTY

    # Unpushed commits (no upstream or ahead of upstream)
    if not branch.has_upstream or (branch.commits_ahead > 0 and branch.pr is None):
        # Check if stale first
        if _is_stale(branch) and branch.pr is None:
            return BranchState.STALE
        if not branch.has_upstream or branch.commits_ahead > 0:
            if branch.pr is None:
                if not branch.has_upstream:
                    return BranchState.UNPUSHED
                return BranchState.UNPUSHED

    # PR-based states
    if branch.pr is not None:
        pr = branch.pr
        if pr.state == "MERGED":
            return BranchState.PR_MERGED
        if pr.state == "CLOSED":
            # Closed but not merged — treat as stale
            return BranchState.STALE
        # OPEN PR
        if pr.is_draft:
            return BranchState.PR_DRAFT
        if pr.review_decision == "APPROVED":
            return BranchState.PR_APPROVED
        if pr.review_decision == "CHANGES_REQUESTED":
            return BranchState.PR_CHANGES_REQ
        return BranchState.PR_OPEN

    # Has upstream but no PR
    if branch.has_upstream:
        if _is_stale(branch):
            return BranchState.STALE
        return BranchState.NO_PR

    # Fallback
    if _is_stale(branch):
        return BranchState.STALE
    return BranchState.NO_PR


def _is_stale(branch: BranchInfo) -> bool:
    if branch.last_commit_date is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=_STALE_DAYS)
    commit_date = branch.last_commit_date
    if commit_date.tzinfo is None:
        commit_date = commit_date.replace(tzinfo=timezone.utc)
    return commit_date < cutoff


def classify_all(branches: list[BranchInfo]) -> None:
    """Classify all branches in place and sort by priority."""
    for b in branches:
        b.state = classify_branch(b)
    branches.sort(key=lambda b: (STATE_PRIORITY.get(b.state, 99), b.repo_name, b.branch_name))
