from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import ModalScreen
from textual.widgets import Label, ProgressBar


class LoadingScreen(ModalScreen[None]):
    """Modal progress screen shown during repo scanning."""

    DEFAULT_CSS = """
    LoadingScreen {
        align: center middle;
    }

    #loading-box {
        width: 60;
        height: 10;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }

    #loading-label {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #loading-progress {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Center(id="loading-box"):
                yield Label("Scanning repositories…", id="loading-label")
                yield ProgressBar(total=100, show_eta=False, id="loading-progress")

    def update_progress(self, done: int, total: int) -> None:
        bar = self.query_one("#loading-progress", ProgressBar)
        label = self.query_one("#loading-label", Label)
        if total > 0:
            bar.update(total=total, progress=done)
            label.update(f"Scanning repositories… {done}/{total}")
        else:
            label.update("Scanning repositories…")

    def set_phase(self, text: str) -> None:
        self.query_one("#loading-label", Label).update(text)
