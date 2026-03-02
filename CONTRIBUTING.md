# Contributing to branchboard

Thanks for your interest in improving branchboard! This guide covers how to get set up and submit changes.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/somanathk/branchboard.git
cd branchboard

# Create a virtual environment (Python 3.12+)
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Verify it runs
branchboard --help
```

## Project Layout

```
src/branchboard/
├── models.py       # Data structures (BranchState, BranchInfo, PRInfo)
├── scanner.py      # Async git subprocess calls
├── github.py       # gh CLI wrapper for PR data
├── classify.py     # Pure-logic state classification
├── cache.py        # JSON file cache
├── app.py          # Textual App wiring
├── app.tcss        # Textual CSS
├── cli.py          # argparse entry point
├── screens/        # Modal screens (loading, detail)
└── widgets/        # UI components (table, filter bar, summary bar)
```

## Making Changes

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-change
   ```

2. **Make your changes.** Keep commits focused on a single concern.

3. **Test manually** by running `branchboard` against a directory with Git repos:
   ```bash
   branchboard --path ~/your/repos --no-cache
   ```

4. **Regenerate screenshots** if you changed the UI:
   ```bash
   python docs/generate_screenshots.py
   ```

5. **Open a pull request** against `main`.

## Code Style

- Python 3.12+ with `from __future__ import annotations`
- Type hints on function signatures
- Async for all I/O (Git subprocesses, GitHub CLI calls)
- No external dependencies beyond `textual` and `rich` (both are required by Textual)

## Adding a New Branch State

1. Add the variant to `BranchState` in `models.py`
2. Add entries to `_STATE_COLORS`, `_STATE_LABELS`, `STATE_PRIORITY`, and `STATE_BADGE_STYLES`
3. Update the classification logic in `classify.py`
4. Update the fake data in `docs/generate_screenshots.py` and regenerate screenshots

## Adding a Keyboard Shortcut

- **App-level bindings** go in `app.py` `BINDINGS` (these work globally)
- **Table-only bindings** go in `widgets/branch_table.py` `BINDINGS` (these only fire when the table has focus, so they don't conflict with the search input)

## Reporting Issues

Open an issue with:
- Your OS and Python version
- Output of `gh --version` and `git --version`
- The error traceback or a screenshot of the unexpected behavior
