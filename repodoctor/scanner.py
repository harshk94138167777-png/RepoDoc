"""
scanner.py — Repository file walker with optional parallel scanning.

Parallel mode (--parallel / -j):
  Uses concurrent.futures.ThreadPoolExecutor with worker count =
  min(32, os.cpu_count() + 4) — the same heuristic CPython uses internally
  for I/O-bound thread pools.  No third-party libraries required.

Animation:
  When stdout is a TTY and --no-animation is not set, a live ProgressBar
  is shown during scanning.  Automatically suppressed in CI / file-redirect
  environments.
"""

import os
import concurrent.futures
from pathlib import Path
from typing import List, Optional

from .models import FileInfo
from .spinner import ProgressBar

DEFAULT_IGNORES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", "target", "coverage", ".cache"
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_binary_file(filepath: str, chunk_size: int = 1024) -> bool:
    """Lightweight heuristic to detect if a file is binary."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(chunk_size)
            if b'\0' in chunk:
                return True
            # Also check if it cannot be decoded as utf-8
            try:
                chunk.decode('utf-8')
            except UnicodeDecodeError:
                return True
    except Exception:
        # If we can't read it, assume binary or unreadable to be safe
        return True
    return False


def count_lines(filepath: str) -> int:
    """Count lines in a text file efficiently."""
    lines = 0
    try:
        with open(filepath, 'rb') as f:
            for _ in f:
                lines += 1
    except Exception:
        pass
    return lines


def _process_file(filepath: str, root_path: str) -> Optional[FileInfo]:
    """
    Worker function: stat + classify one file.
    Runs inside a ThreadPoolExecutor worker when parallel=True,
    or called directly in sequential mode.
    Returns None on any unrecoverable error so callers can skip it.
    """
    # Avoid broken symlinks
    if not os.path.exists(filepath):
        return None

    try:
        stat_result = os.stat(filepath)
        size = stat_result.st_size
    except OSError:
        return None

    rel_path = os.path.relpath(filepath, root_path)
    _, ext = os.path.splitext(os.path.basename(filepath))

    is_binary = is_binary_file(filepath)
    lines = 0 if is_binary else count_lines(filepath)

    return FileInfo(
        path=filepath,
        filename=os.path.basename(filepath),
        extension=ext.lower(),
        size=size,
        lines=lines,
        is_binary=is_binary,
        language="Unknown",   # populated later by detect_languages()
        relative_path=rel_path,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def scan_repository(
    root_path: str,
    custom_ignores: Optional[List[str]] = None,
    parallel: bool = False,
    show_animation: bool = True,
) -> List[FileInfo]:
    """
    Walk *root_path* and return a list of FileInfo objects.

    Parameters
    ----------
    root_path       : Absolute or relative path to the repository root.
    custom_ignores  : Extra directory / file names to skip.
    parallel        : If True, use ThreadPoolExecutor for I/O parallelism.
    show_animation  : If True (and stdout is a TTY), render a progress bar.
    """
    ignores = set(DEFAULT_IGNORES)
    if custom_ignores:
        ignores.update(custom_ignores)

    root_path = os.path.abspath(root_path)

    # ------------------------------------------------------------------ #
    # Phase 1: collect all file paths (fast, sequential walk)
    # ------------------------------------------------------------------ #
    all_paths: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in ignores]
        for filename in filenames:
            if filename in ignores:
                continue
            all_paths.append(os.path.join(dirpath, filename))

    total = len(all_paths)
    if total == 0:
        return []

    # ------------------------------------------------------------------ #
    # Phase 2: stat + classify files (sequential or parallel)
    # ------------------------------------------------------------------ #
    bar = ProgressBar(
        total=total,
        label="Scanning files",
        colour=show_animation,
    ) if show_animation else None

    files_info: List[FileInfo] = []

    if parallel:
        # Worker count: same heuristic as CPython's default I/O pool
        max_workers = min(32, (os.cpu_count() or 1) + 4)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(_process_file, p, root_path): p
                for p in all_paths
            }
            for future in concurrent.futures.as_completed(future_to_path):
                result = future.result()
                if result is not None:
                    files_info.append(result)
                if bar:
                    bar.advance()
    else:
        # Sequential path — unchanged behaviour for small repos / CI
        for filepath in all_paths:
            result = _process_file(filepath, root_path)
            if result is not None:
                files_info.append(result)
            if bar:
                bar.advance()

    if bar:
        bar.done()

    return files_info
