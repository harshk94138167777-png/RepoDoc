"""
spinner.py — Zero-dependency terminal spinner / progress animation.

Uses only Python stdlib: sys, threading, time, itertools.
Automatically suppresses output when stdout is not a TTY
(e.g. file redirection, CI pipelines).
"""

import sys
import threading
import time
import itertools


# Braille spinner frames — visually smooth, widely supported
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# ANSI colour codes (disabled when not TTY)
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RESET  = "\033[0m"
_BOLD   = "\033[1m"


def _is_tty() -> bool:
    """Return True only when stdout is an interactive terminal."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class Spinner:
    """
    Context-manager / manual spinner that renders a live animation line.

    Usage (context manager — recommended):
        with Spinner("Scanning repository"):
            do_work()

    Usage (manual):
        sp = Spinner("Cloning repo")
        sp.start()
        do_work()
        sp.stop(success=True)
    """

    def __init__(self, message: str = "Working", colour: bool = True, silent: bool = False) -> None:
        self._message = message
        self._use_colour = colour and _is_tty()
        self._active = False
        self._thread: threading.Thread | None = None
        self.silent = silent

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def start(self) -> "Spinner":
        if self.silent:
            return self
        if not _is_tty():
            # Non-interactive: just print the static message
            print(f"{self._message}…", flush=True)
            return self
        self._active = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def stop(self, success: bool = True, final_message: str = "") -> None:
        if self.silent:
            return
        self._active = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        if _is_tty():
            # Clear the spinner line
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        # Print final status line
        if not final_message:
            final_message = self._message
        if success:
            icon = f"{_GREEN}✔{_RESET}" if self._use_colour else "✔"
        else:
            icon = f"{_YELLOW}✘{_RESET}" if self._use_colour else "✘"
        print(f"{icon}  {final_message}", flush=True)

    def update_message(self, message: str) -> None:
        """Change the message shown next to the spinner in real time."""
        self._message = message

    # ------------------------------------------------------------------ #
    # context-manager support
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "Spinner":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop(success=exc_type is None)
        return False  # do not suppress exceptions

    # ------------------------------------------------------------------ #
    # internal spin loop (runs in background thread)
    # ------------------------------------------------------------------ #

    def _spin(self) -> None:
        spinner = itertools.cycle(_SPINNER_FRAMES)
        while self._active:
            frame = next(spinner)
            if self._use_colour:
                line = f"\r{_CYAN}{_BOLD}{frame}{_RESET}  {self._message} "
            else:
                line = f"\r{frame}  {self._message} "
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(0.08)
        # Final clear is done in stop()


class ProgressBar:
    """
    Simple zero-dependency terminal progress bar.

    Usage:
        bar = ProgressBar(total=len(files), label="Scanning")
        for f in files:
            process(f)
            bar.advance()
        bar.done()
    """

    def __init__(self, total: int, label: str = "Progress",
                 width: int = 30, colour: bool = True) -> None:
        self._total = max(total, 1)
        self._current = 0
        self._label = label
        self._width = width
        self._use_colour = colour and _is_tty()
        self._tty = _is_tty()

    def advance(self, n: int = 1) -> None:
        self._current = min(self._current + n, self._total)
        if self._tty:
            self._render()

    def done(self) -> None:
        self._current = self._total
        if self._tty:
            self._render()
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _render(self) -> None:
        pct = self._current / self._total
        filled = int(self._width * pct)
        bar_body = "█" * filled + "░" * (self._width - filled)

        if self._use_colour:
            bar_str = (
                f"\r{_CYAN}{self._label}{_RESET}  "
                f"[{_GREEN}{bar_body}{_RESET}] "
                f"{_BOLD}{int(pct * 100):3d}%{_RESET} "
                f"({self._current}/{self._total})"
            )
        else:
            bar_str = (
                f"\r{self._label}  [{bar_body}] "
                f"{int(pct * 100):3d}% ({self._current}/{self._total})"
            )

        sys.stdout.write(bar_str)
        sys.stdout.flush()
