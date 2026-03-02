from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from git_fleet.models import BranchInfo

# Scan up to 10 repos concurrently
_GIT_SEMAPHORE = asyncio.Semaphore(10)


async def _run(cmd: list[str], cwd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace").strip()


def discover_repos(root: str, max_depth: int = 3) -> list[str]:
    """Walk *root* up to *max_depth* levels looking for .git directories."""
    repos: list[str] = []
    root_path = Path(root).resolve()
    for dirpath, dirnames, _ in os.walk(root_path):
        depth = len(Path(dirpath).relative_to(root_path).parts)
        if depth >= max_depth:
            dirnames.clear()
            continue
        if ".git" in dirnames:
            repos.append(dirpath)
            dirnames.clear()  # don't descend into a repo
    repos.sort()
    return repos


async def _get_current_branch(repo: str) -> tuple[str, bool]:
    """Return (branch_name, is_detached)."""
    rc, out = await _run(["git", "symbolic-ref", "--short", "HEAD"], repo)
    if rc == 0:
        return out, False
    # Detached HEAD — get short sha
    _, out = await _run(["git", "rev-parse", "--short", "HEAD"], repo)
    return out, True


async def _get_dirty_files(repo: str) -> list[str]:
    _, out = await _run(["git", "status", "--porcelain"], repo)
    return [line for line in out.splitlines() if line.strip()] if out else []


async def _get_branches(repo: str) -> list[dict]:
    """Return list of branch dicts from for-each-ref."""
    fmt = "%(refname:short)%09%(upstream:short)%09%(upstream:track)%09%(committerdate:iso-strict)%09%(subject)"
    _, out = await _run(
        ["git", "for-each-ref", "--format", fmt, "refs/heads/"],
        repo,
    )
    branches = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            parts += [""] * (5 - len(parts))
        name, upstream, track, date_str, subject = parts[:5]
        # Skip main/master/develop unless they have dirty changes (handled separately)
        ahead = behind = 0
        if track:
            import re
            m = re.search(r"ahead (\d+)", track)
            if m:
                ahead = int(m.group(1))
            m = re.search(r"behind (\d+)", track)
            if m:
                behind = int(m.group(1))

        commit_date = None
        if date_str:
            try:
                commit_date = datetime.fromisoformat(date_str)
            except ValueError:
                pass

        branches.append({
            "name": name,
            "upstream": upstream,
            "ahead": ahead,
            "behind": behind,
            "commit_date": commit_date,
            "subject": subject,
        })
    return branches


async def _get_remote_url(repo: str) -> str:
    _, out = await _run(["git", "remote", "get-url", "origin"], repo)
    return out


async def scan_repo(repo_path: str) -> list[BranchInfo]:
    """Scan a single repo for branch information."""
    async with _GIT_SEMAPHORE:
        repo_name = os.path.basename(repo_path)

        current_branch, is_detached = await _get_current_branch(repo_path)
        dirty_files = await _get_dirty_files(repo_path)
        branches_raw = await _get_branches(repo_path)
        remote_url = await _get_remote_url(repo_path)

        results: list[BranchInfo] = []
        for br in branches_raw:
            name = br["name"]
            # Skip default branches unless they're the current dirty branch
            if name in ("main", "master", "develop"):
                if not (name == current_branch and dirty_files):
                    continue

            is_current = name == current_branch
            info = BranchInfo(
                repo_name=repo_name,
                repo_path=repo_path,
                branch_name=name,
                is_current=is_current,
                is_dirty=is_current and bool(dirty_files),
                dirty_files=dirty_files if is_current else [],
                has_upstream=bool(br["upstream"]),
                commits_ahead=br["ahead"],
                commits_behind=br["behind"],
                last_commit_date=br["commit_date"],
                last_commit_msg=br["subject"],
                remote_url=remote_url,
            )
            results.append(info)

        # If detached HEAD with dirty changes, add an entry
        if is_detached and dirty_files:
            results.append(BranchInfo(
                repo_name=repo_name,
                repo_path=repo_path,
                branch_name=f"(detached:{current_branch})",
                is_current=True,
                is_dirty=True,
                dirty_files=dirty_files,
                remote_url=remote_url,
            ))

        return results


async def scan_all_repos(
    root: str,
    on_progress: asyncio.Future | None = None,
) -> list[BranchInfo]:
    """Discover repos under *root* and scan them all concurrently.

    *on_progress* — if provided, should be an async callback(done, total).
    """
    repos = discover_repos(root)
    total = len(repos)
    done = 0
    all_branches: list[BranchInfo] = []

    async def _scan_one(repo: str) -> list[BranchInfo]:
        nonlocal done
        result = await scan_repo(repo)
        done += 1
        if on_progress:
            await on_progress(done, total)
        return result

    tasks = [_scan_one(r) for r in repos]
    results = await asyncio.gather(*tasks)
    for branch_list in results:
        all_branches.extend(branch_list)
    return all_branches
