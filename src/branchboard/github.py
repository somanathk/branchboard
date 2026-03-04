from __future__ import annotations

import asyncio
import json
import re
from branchboard.models import BranchInfo, PRInfo
from branchboard.cache import load_cache, save_cache

_GH_SEMAPHORE = asyncio.Semaphore(5)

_GH_FIELDS = [
    "number", "title", "state", "url", "isDraft",
    "reviewDecision", "reviewRequests", "createdAt", "updatedAt",
    "headRefName", "baseRefName",
]


def _extract_owner_repo(remote_url: str) -> str | None:
    """Extract 'owner/repo' from a git remote URL."""
    # SSH: git@github.com:owner/repo.git (also matches aliases like github.com-work)
    m = re.match(r"git@github\.com[^:]*:(.+?)(?:\.git)?$", remote_url)
    if m:
        return m.group(1)
    # HTTPS: https://github.com/owner/repo.git
    m = re.match(r"https://github\.com/(.+?)(?:\.git)?$", remote_url)
    if m:
        return m.group(1)
    return None


async def _run_gh(args: list[str]) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "gh", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace").strip()


async def _fetch_prs_for_repo(owner_repo: str, use_cache: bool) -> list[dict]:
    """Fetch PRs for a single GitHub repo."""
    if use_cache:
        cached = load_cache(f"prs_{owner_repo.replace('/', '_')}")
        if cached is not None:
            return cached

    async with _GH_SEMAPHORE:
        fields = ",".join(_GH_FIELDS)
        rc, out = await _run_gh([
            "pr", "list",
            "--repo", owner_repo,
            "--state", "all",
            "--author", "@me",
            "--limit", "100",
            "--json", fields,
        ])
        if rc != 0 or not out:
            return []
        try:
            prs = json.loads(out)
        except json.JSONDecodeError:
            return []

    save_cache(f"prs_{owner_repo.replace('/', '_')}", prs)
    return prs


def _match_pr(branch_name: str, prs: list[dict]) -> dict | None:
    """Find the best matching PR for a branch."""
    # Prefer open PRs, then most recent
    matches = [p for p in prs if p.get("headRefName") == branch_name]
    if not matches:
        return None
    # Sort: open first, then by updatedAt descending
    def sort_key(p: dict) -> tuple:
        is_open = 0 if p.get("state") == "OPEN" else 1
        return (is_open, p.get("updatedAt", ""))
    matches.sort(key=sort_key)
    return matches[0]


def _pr_dict_to_info(pr: dict) -> PRInfo:
    reviewers = []
    for req in pr.get("reviewRequests", []):
        name = req.get("login") or req.get("name", "")
        if name:
            reviewers.append(name)
    return PRInfo(
        number=pr.get("number", 0),
        title=pr.get("title", ""),
        state=pr.get("state", ""),
        url=pr.get("url", ""),
        is_draft=pr.get("isDraft", False),
        review_decision=pr.get("reviewDecision") or "",
        reviewers=reviewers,
        created_at=pr.get("createdAt", ""),
        updated_at=pr.get("updatedAt", ""),
        head_branch=pr.get("headRefName", ""),
        base_branch=pr.get("baseRefName", ""),
    )


async def fetch_all_prs(
    branches: list[BranchInfo],
    use_cache: bool = True,
) -> None:
    """Fetch PR data for all branches, mutating branch.pr in place."""
    # Collect unique owner/repo from remote URLs
    remote_map: dict[str, str] = {}  # owner_repo -> remote_url
    for b in branches:
        if b.remote_url:
            owner_repo = _extract_owner_repo(b.remote_url)
            if owner_repo:
                remote_map[owner_repo] = b.remote_url

    # Fetch PRs for each unique repo
    pr_data: dict[str, list[dict]] = {}
    tasks = []
    for owner_repo in remote_map:
        async def _fetch(or_=owner_repo):
            pr_data[or_] = await _fetch_prs_for_repo(or_, use_cache)
        tasks.append(_fetch())

    await asyncio.gather(*tasks)

    # Match PRs to branches
    for b in branches:
        if not b.remote_url:
            continue
        owner_repo = _extract_owner_repo(b.remote_url)
        if not owner_repo or owner_repo not in pr_data:
            continue
        pr = _match_pr(b.branch_name, pr_data[owner_repo])
        if pr:
            b.pr = _pr_dict_to_info(pr)
