# Changelog

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
