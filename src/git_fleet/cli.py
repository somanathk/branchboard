from __future__ import annotations

import argparse
import os
import shutil
import sys


def _check_dependencies() -> None:
    """Verify external CLI tools are available before starting."""
    if not shutil.which("git"):
        print("error: git is not installed or not on PATH", file=sys.stderr)
        print("  Install: https://git-scm.com/downloads", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("gh"):
        print("error: GitHub CLI (gh) is not installed or not on PATH", file=sys.stderr)
        print()
        print("  git-fleet uses `gh` to fetch PR data from GitHub.", file=sys.stderr)
        print()
        print("  Install:", file=sys.stderr)
        print("    macOS:  brew install gh", file=sys.stderr)
        print("    Linux:  https://github.com/cli/cli/blob/trunk/docs/install_linux.md", file=sys.stderr)
        print("    Other:  https://cli.github.com/", file=sys.stderr)
        print()
        print("  Then authenticate:  gh auth login", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="git-fleet",
        description="Git Branch Dashboard TUI — scan repos and show branch/PR status",
    )
    parser.add_argument(
        "--path",
        default=os.path.expanduser("~/Work/repos"),
        help="Root directory to scan for git repos (default: ~/Work/repos)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the JSON file cache and fetch fresh data",
    )
    args = parser.parse_args()

    _check_dependencies()

    from git_fleet.app import GitFleetApp

    app = GitFleetApp(scan_path=args.path, use_cache=not args.no_cache)
    app.run()


if __name__ == "__main__":
    main()
