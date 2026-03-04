# Changelog

## 0.1.7 (2026-03-04)

- Fix PR detection for repos using custom SSH host aliases (e.g. `github.com-work`)

## 0.1.6 (2026-03-04)

- Fix crash on startup: guard LoadingScreen widget queries with `is_mounted` check
  to prevent `NoMatches` error when the worker starts before the screen is composed
- Rename internal `GitFleetApp` class to `BranchBoardApp` (leftover from rename)

## 0.1.5 (2026-03-03)

- Fix loading spinner not appearing on launch: switch from `await _do_scan()` in
  `on_mount` to `run_worker()` so Textual renders the loading screen on the first
  frame before any scanning begins

## 0.1.4 (2026-03-03)

- Fix crash on pip-installed package: resolve `app.tcss` relative to `__file__` instead of CWD
- Bundle `app.tcss` in the wheel via `package-data` so it's present after `pip install`

## 0.1.3 (2026-03-03)

- Add animated spinner during GitHub PR fetch phase
- Fix blank flash on refresh: populate table before dismissing loading modal

## 0.1.2 (2026-03-03)

- Lower Python requirement from 3.12 to 3.9 (constrained by Textual ≥3.9)

## 0.1.1 (2026-03-02)

- Fix screenshots not rendering on PyPI: convert SVGs to PNGs and use absolute `raw.githubusercontent.com` URLs

## 0.1.0 (2026-03-02)

Initial release.

- Scan all Git repos under a directory tree (3 levels deep, 10 concurrent)
- Fetch PR data from GitHub via `gh` CLI (5 concurrent, cached for 5 minutes)
- Classify branches into 9 color-coded states: Dirty, Unpushed, Changes Requested, PR Open, PR Approved, PR Draft, No PR, Stale, PR Merged
- Interactive DataTable with row selection and detail modal
- Vim-style navigation: `j`/`k`, `g`/`G`, `Ctrl-d`/`Ctrl-u`, `Ctrl-f`/`Ctrl-b`
- Free-text search and state dropdown filtering
- Toggle between priority sort and recency sort
- Open PR in browser with `o`
- Loading screen with progress bar
- `--path` and `--no-cache` CLI flags
