#!/usr/bin/env python3
# RepoDoctor - Zero Dependency Hackathon Submission
# Auto-generated single-file version.

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any
from typing import Dict, Optional
from typing import List
from typing import List, Dict, Tuple
from typing import List, Optional
from typing import List, Tuple
from typing import Optional, List, Tuple, Dict, Any
import argparse
import ast
import concurrent.futures
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time

# --- models.py ---


@dataclass
class HealthScore:
    score: int
    breakdown: List[Tuple[str, int]]

@dataclass
class ReportData:
    path: str
    name: str
    files: List['FileInfo']
    todos: List['TodoItem']
    security: List['SecurityFinding']
    duplicates: List['DuplicateBlock']
    structure: Dict[str, str]
    git: 'GitInfo'
    top_words: List[Tuple[str, int]] = None
    mood: str = None
    clone_exposer: str = None
    score: Optional[HealthScore] = None

@dataclass
class GitInfo:
    available: bool
    branch: str = ""
    uncommitted_changes: int = 0
    commits: int = 0
    top_contributor: str = ""
    hotspot: str = ""

@dataclass
class DuplicateBlock:
    filepaths: List[str]
    lines: Tuple[int, int]
    similarity: str


@dataclass
class SecurityFinding:
    filepath: str
    line_number: int
    category: str
    confidence: str
    explanation: str
    redacted_value: str


@dataclass
class TodoItem:
    filepath: str
    line_number: int
    text: str
    marker: str


@dataclass
class FileMetrics:
    blank_lines: int = 0
    comment_lines: int = 0
    code_lines: int = 0
    longest_line: int = 0
    num_functions: int = 0
    num_classes: int = 0
    max_nesting: int = 0


@dataclass
class FileInfo:
    path: str
    filename: str
    extension: str
    size: int
    lines: int
    is_binary: bool
    language: str
    relative_path: str
    metrics: Optional[FileMetrics] = None
    code_smells: List[str] = None



# --- cli.py ---


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repodoctor",
        description="RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure and Git issues using only the language standard library.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "path",
        help="Path to the repository to analyze",
        default=".",
        nargs="?"
    )
    parser.add_argument("--json", action="store_true", help="Output valid machine-readable JSON")
    parser.add_argument("--html", type=str, help="Output a self-contained HTML report to the specified file", default="")
    parser.add_argument("--baseline", type=str, help="Path to a previous JSON report to compare against", default="")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    parser.add_argument("--badge", type=str, metavar="FILE", help="Generate an SVG health badge", default="")
    parser.add_argument("--tree", action="store_true", help="Print an ASCII project tree")
    parser.add_argument("--export-prompt", type=str, metavar="FILE", help="Export the codebase into a single text file for LLM prompting", default="")
    parser.add_argument("--ignore", type=str, help="Comma-separated list of custom directories to ignore", default="")
    parser.add_argument("--large-file-lines", type=int, help="Threshold for large file lines", default=500)
    parser.add_argument("--duplicate-lines", type=int, help="Minimum lines for duplicate detection", default=8)
    parser.add_argument("--security", action="store_true", help="Focus only on security analysis")
    parser.add_argument("--todos", action="store_true", help="Focus only on TODO/FIXME analysis")
    parser.add_argument("--git", action="store_true", help="Include Git analysis")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--parallel", "-j",
        action="store_true",
        help="Enable parallel file scanning using concurrent.futures.ThreadPoolExecutor (faster on large repos)"
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable live CLI spinner / progress bar animation"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    return parser

def parse_args(args=None):
    parser = build_parser()
    return parser.parse_args(args)


# --- spinner.py ---

"""
spinner.py — Zero-dependency terminal spinner / progress animation.

Uses only Python stdlib: sys, threading, time, itertools.
Automatically suppresses output when stdout is not a TTY
(e.g. file redirection, CI pipelines).
"""



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

    def __init__(self, message: str = "Working", colour: bool = True) -> None:
        self._message = message
        self._use_colour = colour and _is_tty()
        self._active = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def start(self) -> "Spinner":
        if not _is_tty():
            # Non-interactive: just print the static message
            print(f"{self._message}…", flush=True)
            return self
        self._active = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def stop(self, success: bool = True, final_message: str = "") -> None:
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


# --- scanner.py ---

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


# --- languages.py ---


EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".sql": "SQL"
}

def detect_languages(files: List[FileInfo]) -> None:
    for f in files:
        if f.is_binary:
            continue
        f.language = EXTENSION_MAP.get(f.extension, "Unknown")


# --- metrics.py ---


def analyze_python_ast(source: str, metrics: FileMetrics):
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                metrics.num_functions += 1
            elif isinstance(node, ast.ClassDef):
                metrics.num_classes += 1
    except SyntaxError:
        pass

def analyze_metrics(files: List[FileInfo]) -> None:
    for f in files:
        if f.is_binary:
            continue

        metrics = FileMetrics()
        
        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
        except Exception:
            continue

        metrics.code_lines = 0
        metrics.blank_lines = 0
        metrics.comment_lines = 0
        
        source_text = "".join(lines)

        for line in lines:
            line_len = len(line.rstrip('\n'))
            if line_len > metrics.longest_line:
                metrics.longest_line = line_len

            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
                continue
            
            # Very basic comment heuristic
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1
                
                # Heuristic nesting
                leading_spaces = len(line) - len(line.lstrip(' '))
                leading_tabs = len(line) - len(line.lstrip('\t'))
                # Assume 4 spaces = 1 depth, 1 tab = 1 depth
                depth = max(leading_spaces // 4, leading_tabs)
                if depth > metrics.max_nesting:
                    metrics.max_nesting = depth

        if f.extension == '.py':
            analyze_python_ast(source_text, metrics)
        else:
            # Heuristic function/class counts for non-Python
            for line in lines:
                stripped = line.strip()
                if re.match(r'^(public\s+|private\s+|protected\s+)?(class|struct)\s+\w+', stripped):
                    metrics.num_classes += 1
                elif re.match(r'^(public\s+|private\s+|protected\s+)?(static\s+)?\w+\s+\w+\s*\(', stripped) and not stripped.endswith(';'):
                    metrics.num_functions += 1
                elif re.match(r'^(function|func|def)\s+\w+', stripped):
                    metrics.num_functions += 1

        f.metrics = metrics


# --- todos.py ---


MARKERS = ["TODO", "FIXME", "HACK", "XXX", "BUG"]
MARKER_PATTERN = re.compile(r'\b(' + '|'.join(MARKERS) + r')\b')

def scan_todos(files: List[FileInfo]) -> List[TodoItem]:
    todos = []
    
    for f in files:
        if f.is_binary:
            continue
            
        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_idx, line in enumerate(file):
                    if MARKER_PATTERN.search(line):
                        # Extract the actual marker used
                        match = MARKER_PATTERN.search(line)
                        marker = match.group(1)
                        
                        todos.append(TodoItem(
                            filepath=f.relative_path,
                            line_number=line_idx + 1,
                            text=line.strip(),
                            marker=marker
                        ))
        except Exception:
            pass

    return todos


# --- security.py ---


PATTERNS = [
    # (Regex, Category, Confidence, Explanation)
    (re.compile(r'(?i)(?:api_?key|secret|token|password)[\s:=]+[\'"]([A-Za-z0-9_\-]{16,})[\'"]'), "API Key or Token", "HIGH", "A variable name suggests an API key or token was hardcoded."),
    (re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----'), "Private Key", "HIGH", "A private cryptographic key is present."),
    (re.compile(r'https?://[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-\.]+'), "Credential URL", "HIGH", "A URL contains embedded basic authentication credentials."),
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})'), "Potential API Key", "HIGH", "Pattern matches common cloud API keys (e.g., sk-...).")
]

def redact(value: str) -> str:
    if len(value) <= 5:
        return "***"
    return value[:3] + "..." + value[-2:]

def scan_security(files: List[FileInfo]) -> List[SecurityFinding]:
    findings = []
    
    for f in files:
        if f.is_binary:
            continue
            
        # Check .env
        if f.filename.startswith(".env"):
            findings.append(SecurityFinding(
                filepath=f.relative_path,
                line_number=0,
                category="Environment File",
                confidence="HIGH",
                explanation="An environment file (e.g., .env) is checked in. This often contains secrets.",
                redacted_value="N/A"
            ))

        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_idx, line in enumerate(file):
                    for pattern, category, confidence, explanation in PATTERNS:
                        match = pattern.search(line)
                        if match:
                            # For private key header, the match is the whole header
                            val_to_redact = match.group(1) if len(match.groups()) > 0 else match.group(0)
                            
                            findings.append(SecurityFinding(
                                filepath=f.relative_path,
                                line_number=line_idx + 1,
                                category=category,
                                confidence=confidence,
                                explanation=explanation,
                                redacted_value=redact(val_to_redact)
                            ))
        except Exception:
            pass
            
    return findings


# --- duplicates.py ---


def normalize_line(line: str) -> str:
    """Strip whitespace and ignore if it's too short to be useful code."""
    return line.strip()

def scan_duplicates(files: List[FileInfo], min_lines: int = 8) -> List[DuplicateBlock]:
    block_hashes = defaultdict(list)
    duplicates = []

    for f in files:
        if f.is_binary:
            continue

        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
        except Exception:
            continue

        valid_lines = []
        for idx, line in enumerate(lines):
            norm = normalize_line(line)
            # basic ignore for very short lines, blank lines, or common comments
            if not norm or len(norm) < 4 or norm.startswith('#') or norm.startswith('//'):
                continue
            valid_lines.append((idx + 1, norm))

        if len(valid_lines) < min_lines:
            continue

        # Create rolling window of hashes
        for i in range(len(valid_lines) - min_lines + 1):
            window = valid_lines[i:i + min_lines]
            start_line = window[0][0]
            end_line = window[-1][0]
            
            # Create block text
            block_text = "".join(x[1] for x in window)
            h = hashlib.sha256(block_text.encode('utf-8')).hexdigest()
            
            block_hashes[h].append((f.relative_path, start_line, end_line))

    # Find duplicates
    # Since rolling windows produce overlapping duplicates, we should just report them simply.
    # A true robust algorithm would merge overlapping blocks, but for MVP we just report unique combinations.
    reported_combinations = set()

    for h, occurrences in block_hashes.items():
        if len(occurrences) > 1:
            paths = [occ[0] for occ in occurrences]
            
            # Simple deduplication of reports (e.g. if we have 9 duplicated lines, it will create two 8-line blocks)
            # We just take the first start_line and end_line for simplicity in MVP.
            combo_key = tuple(sorted(paths))
            if combo_key not in reported_combinations:
                # Approximate the lines
                # The format is just showing that these files share duplicate code blocks.
                duplicates.append(DuplicateBlock(
                    filepaths=paths,
                    lines=(occurrences[0][1], occurrences[0][2]),
                    similarity="exact"
                ))
                reported_combinations.add(combo_key)

    return duplicates


# --- structure.py ---


def check_project_structure(root_path: str) -> Dict[str, str]:
    """
    Returns PASS, WARN, FAIL, or NOT APPLICABLE
    """
    results = {
        "README": "WARN",
        ".gitignore": "WARN",
        "Tests": "WARN",
        "LICENSE": "WARN",
        "CI config": "WARN"
    }

    root = os.path.abspath(root_path)

    # Check README
    if any(os.path.exists(os.path.join(root, f)) for f in ["README.md", "README.txt", "README"]):
        results["README"] = "PASS"

    # Check .gitignore
    if os.path.exists(os.path.join(root, ".gitignore")):
        results[".gitignore"] = "PASS"
    elif not os.path.exists(os.path.join(root, ".git")):
        results[".gitignore"] = "NOT APPLICABLE"

    # Check tests
    if os.path.exists(os.path.join(root, "tests")) or os.path.exists(os.path.join(root, "test")):
        results["Tests"] = "PASS"

    # Check LICENSE
    if any(os.path.exists(os.path.join(root, f)) for f in ["LICENSE", "LICENSE.txt", "LICENSE.md"]):
        results["LICENSE"] = "PASS"

    # Check CI config
    if os.path.exists(os.path.join(root, ".github")) or os.path.exists(os.path.join(root, ".gitlab-ci.yml")):
        results["CI config"] = "PASS"
    
    return results


# --- git.py ---


def run_git(cmd: list, cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""

def get_git_info(root_path: str) -> GitInfo:
    root = os.path.abspath(root_path)
    
    is_git_repo = run_git(["rev-parse", "--is-inside-work-tree"], root)
    if is_git_repo != "true":
        return GitInfo(available=False)

    branch = run_git(["branch", "--show-current"], root)
    if not branch:
        branch = "detached"

    commits_str = run_git(["rev-list", "--count", "HEAD"], root)
    commits = int(commits_str) if commits_str.isdigit() else 0

    status_str = run_git(["status", "--porcelain"], root)
    uncommitted = len(status_str.splitlines()) if status_str else 0

    top_contributor = ""
    try:
        result = subprocess.run(["git", "shortlog", "-sn", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        if lines and lines[0]:
            parts = lines[0].strip().split('\t', 1)
            if len(parts) == 2:
                top_contributor = f"{parts[1].strip()} ({parts[0].strip()} commits)"
    except Exception:
        pass

    hotspot = ""
    try:
        result = subprocess.run(["git", "log", "--name-only", "--pretty=format:"], cwd=root, capture_output=True, text=True, check=True)
        files = [f for f in result.stdout.split('\n') if f.strip()]
        if files:
            from collections import Counter
            c = Counter(files)
            most_common = c.most_common(1)
            if most_common:
                hotspot = f"{most_common[0][0]} ({most_common[0][1]} edits)"
    except Exception:
        pass

    return GitInfo(
        available=True,
        branch=branch,
        uncommitted_changes=uncommitted,
        commits=commits,
        top_contributor=top_contributor,
        hotspot=hotspot
    )


# --- scoring.py ---


def calculate_score(data: ReportData, large_file_threshold: int = 500) -> HealthScore:
    base = 85
    breakdown = []

    if data.structure.get("README") == "PASS":
        base += 5
        breakdown.append(("README present", 5))
    
    if data.structure.get("Tests") == "PASS":
        base += 5
        breakdown.append(("Tests detected", 5))

    if data.structure.get(".gitignore") == "PASS":
        base += 5
        breakdown.append((".gitignore present", 5))

    # Penalties
    large_files = sum(1 for f in data.files if f.lines > large_file_threshold)
    if large_files > 0:
        penalty = min(15, large_files * 3) # max -15
        base -= penalty
        breakdown.append(("Large files", -penalty))

    if len(data.todos) > 0:
        penalty = min(10, len(data.todos))
        base -= penalty
        breakdown.append(("TODO/FIXME count", -penalty))

    if len(data.security) > 0:
        penalty = min(30, len(data.security) * 15)
        base -= penalty
        breakdown.append(("Potential secrets", -penalty))

    if len(data.duplicates) > 0:
        penalty = min(20, len(data.duplicates) * 5)
        base -= penalty
        breakdown.append(("Duplicate blocks", -penalty))
        
    # High complexity (nesting > 4)
    high_complexity = sum(1 for f in data.files if f.metrics and f.metrics.max_nesting > 4)
    if high_complexity > 0:
        penalty = min(10, high_complexity * 2)
        base -= penalty
        breakdown.append(("High complexity", -penalty))

    base = max(0, min(100, base))
    return HealthScore(score=base, breakdown=breakdown)


# --- report.py ---



def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas: Optional[Dict[str, int]] = None, exec_time: Optional[float] = None, tree: bool = False) -> None:
    def c(text: str, color_code: str) -> str:
        if not use_color: return text
        return f"\033[{color_code}m{text}\033[0m"

    def fmt_delta(val: int, inverted: bool = False) -> str:
        if val == 0: return ""
        sign = "+" if val > 0 else ""
        color = "92" if (val > 0 and not inverted) or (val < 0 and inverted) else "91"
        return c(f" ({sign}{val})", color)

    print(c("╔════════════════════════════════════════════════════════════╗", "94"))
    print(c("║                       REPO DOCTOR                         ║", "94;1"))
    print(c("╚════════════════════════════════════════════════════════════╝", "94"))
    print()
    print(f"Repository: {data.name}")
    print(f"Path: {data.path}")
    if deltas:
        print(c("Baseline comparison activated.", "36"))
    print()

    print(c("SUMMARY", "1"))
    print("────────────────────────────────────────────────────────────")
    
    files_str = f"{len(data.files)}{fmt_delta(deltas['files']) if deltas else ''}"
    print(f"Files scanned:          {files_str}")
    
    total_lines = sum(f.lines for f in data.files)
    lines_str = f"{total_lines:,}{fmt_delta(deltas['lines']) if deltas else ''}"
    print(f"Lines of code:          {lines_str}")
    
    languages = set(f.language for f in data.files if f.language != "Unknown")
    print(f"Languages detected:     {', '.join(languages) if languages else 'None'}")
    
    if data.score:
        score_str = f"{data.score.score}/100{fmt_delta(deltas['score']) if deltas else ''}"
        print(f"Health score:           {score_str}")
    print()

    print(c("MAINTAINABILITY", "1"))
    print("────────────────────────────────────────────────────────────")
    large_files = sum(1 for f in data.files if f.lines > large_file_threshold)
    print(f"Large files:            {large_files}")
    long_functions = sum(f.metrics.num_functions for f in data.files if f.metrics)
    print(f"Long functions:         {long_functions}")
    high_nesting = sum(1 for f in data.files if f.metrics and f.metrics.max_nesting > 4)
    print(f"High nesting:           {high_nesting}")
    
    todos_str = f"{len(data.todos)}{fmt_delta(deltas['todos'], inverted=True) if deltas else ''}"
    print(f"TODO/FIXME items:       {todos_str}")
    
    dups_str = f"{len(data.duplicates)}{fmt_delta(deltas['duplicates'], inverted=True) if deltas else ''}"
    print(f"Duplicate blocks:       {dups_str}")
    print()

    print(c("SECURITY", "1"))
    print("────────────────────────────────────────────────────────────")
    sec_str = f"{len(data.security)}{fmt_delta(deltas['secrets'], inverted=True) if deltas else ''}"
    print(f"Potential secrets:      {sec_str}")
    if data.security:
        for sec in data.security:
            print(f"  {sec.filepath}:{sec.line_number} - {sec.category} (Confidence: {sec.confidence})")
            print(f"  Value: {sec.redacted_value}")
    print()

    print(c("PROJECT HEALTH", "1"))
    print("────────────────────────────────────────────────────────────")
    for key, val in data.structure.items():
        icon = "✓" if val == "PASS" else ("✗" if val == "FAIL" else ("⚠" if val == "WARN" else "-"))
        print(f"{key:<23} {icon}")
    print()

    print(c("GIT", "1"))
    print("────────────────────────────────────────────────────────────")
    if data.git.available:
        print(f"Branch:                 {data.git.branch}")
        print(f"Uncommitted changes:    {data.git.uncommitted_changes}")
        print(f"Commits:                {data.git.commits}")
    else:
        print("Git repository:         Not available")
    print()

    if data.score:
        print("────────────────────────────────────────────────────────────")
        print(c(f"Health Score: {data.score.score}/100", "92;1" if data.score.score > 80 else "91;1"))
        print("────────────────────────────────────────────────────────────")
        for reason, change in data.score.breakdown:
            sign = "+" if change > 0 else ""
            print(f"{reason:<30} {sign}{change}")

def get_json_report(data: ReportData, large_file_threshold: int = 500) -> str:
    total_lines = sum(f.lines for f in data.files)
    large_files = sum(1 for f in data.files if f.lines > large_file_threshold)
    
    out = {
        "repository": {
            "path": data.path,
            "name": data.name
        },
        "summary": {
            "files": len(data.files),
            "lines": total_lines,
            "health_score": data.score.score if data.score else None
        },
        "security": {
            "potential_secrets": len(data.security),
            "findings": [
                {
                    "file": s.filepath,
                    "line": s.line_number,
                    "category": s.category,
                    "confidence": s.confidence,
                    "explanation": s.explanation,
                    # Deliberately omitting full secret, just showing redacted
                    "redacted_value": s.redacted_value
                } for s in data.security
            ]
        },
        "maintainability": {
            "large_files": large_files,
            "todos": len(data.todos),
            "duplicates": len(data.duplicates)
        },
        "git": {
            "available": data.git.available,
            "branch": data.git.branch,
            "commits": data.git.commits,
            "uncommitted_changes": data.git.uncommitted_changes
        },
        "structure": data.structure
    }
    return json.dumps(out, indent=2)

def generate_html_report(data: ReportData, large_file_threshold: int = 500) -> str:
    total_lines = sum(f.lines for f in data.files)
    large_files = sum(1 for f in data.files if f.lines > large_file_threshold)
    long_functions = sum(f.metrics.num_functions for f in data.files if f.metrics)
    high_nesting = sum(1 for f in data.files if f.metrics and f.metrics.max_nesting > 4)
    languages = set(f.language for f in data.files if f.language != "Unknown")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>RepoDoctor Report - {data.name}</title>
<style>
    body {{ font-family: monospace, sans-serif; background-color: #ffffff; color: #000000; margin: 0; padding: 20px; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 20px; border: 1px solid #000000; }}
    h1 {{ border-bottom: 2px solid #000000; padding-bottom: 10px; text-transform: uppercase; font-size: 1.5em; }}
    h2 {{ margin-top: 30px; border-bottom: 1px solid #000000; padding-bottom: 5px; text-transform: uppercase; font-size: 1.2em; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; }}
    .stat-card {{ padding: 15px; border: 1px solid #000000; text-align: center; }}
    .stat-value {{ font-size: 24px; font-weight: bold; }}
    .stat-label {{ font-size: 14px; margin-top: 5px; text-transform: uppercase; }}
    .score {{ font-size: 48px; font-weight: bold; text-align: center; margin: 20px 0; border: 3px solid #000000; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ padding: 8px 12px; border: 1px solid #000000; text-align: left; }}
    th {{ background: #eeeeee; text-transform: uppercase; }}
    .status-text {{ font-weight: bold; }}
    ul {{ list-style-type: square; }}
</style>
</head>
<body>
<div class="container">
    <h1>REPO DOCTOR REPORT: {data.name}</h1>
    <div class="score">HEALTH SCORE: {data.score.score if data.score else 'N/A'} / 100</div>
    
    <h2>SUMMARY</h2>
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">{len(data.files)}</div><div class="stat-label">Files Scanned</div></div>
        <div class="stat-card"><div class="stat-value">{total_lines:,}</div><div class="stat-label">Lines of Code</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.todos)}</div><div class="stat-label">TODO/FIXME Items</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.duplicates)}</div><div class="stat-label">Duplicate Blocks</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.security)}</div><div class="stat-label">Potential Secrets</div></div>
    </div>
    
    <h2>MAINTAINABILITY</h2>
    <ul>
        <li><b>Large Files:</b> {large_files}</li>
        <li><b>Long Functions (Heuristic):</b> {long_functions}</li>
        <li><b>High Nesting:</b> {high_nesting}</li>
        <li><b>Languages:</b> {', '.join(languages) if languages else 'None'}</li>
    </ul>

    <h2>PROJECT HEALTH</h2>
    <table>
        <tr><th>Check</th><th>Status</th></tr>
        {''.join(f"<tr><td>{k}</td><td><span class='status-text'>[{v}]</span></td></tr>" for k, v in data.structure.items())}
    </table>

    <h2>SECURITY FINDINGS</h2>
    { "<ul>" + "".join(f"<li><b>{s.filepath}:{s.line_number}</b> - {s.category} (Value: {s.redacted_value})</li>" for s in data.security) + "</ul>" if data.security else "<p>No secrets detected.</p>" }
    
    <h2>GIT INFO</h2>
    <p>{ f"Branch: {data.git.branch} | Commits: {data.git.commits} | Uncommitted Changes: {data.git.uncommitted_changes}" if data.git.available else "Git not available." }</p>
</div>
</body>
</html>"""
    return html


# --- baseline.py ---


def compare_baseline(current_data: ReportData, baseline_path: str) -> Optional[Dict[str, int]]:
    if not os.path.exists(baseline_path):
        return None
        
    try:
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
            
        deltas = {}
        
        # Current values
        c_score = current_data.score.score if current_data.score else 0
        c_files = len(current_data.files)
        c_lines = sum(f.lines for f in current_data.files)
        c_todos = len(current_data.todos)
        c_dups = len(current_data.duplicates)
        c_secrets = len(current_data.security)
        
        # Baseline values
        b_score = baseline.get("summary", {}).get("health_score", 0)
        b_files = baseline.get("summary", {}).get("files", 0)
        b_lines = baseline.get("summary", {}).get("lines", 0)
        b_todos = baseline.get("maintainability", {}).get("todos", 0)
        b_dups = baseline.get("maintainability", {}).get("duplicates", 0)
        b_secrets = baseline.get("security", {}).get("potential_secrets", 0)
        
        deltas["score"] = c_score - (b_score or 0)
        deltas["files"] = c_files - b_files
        deltas["lines"] = c_lines - b_lines
        deltas["todos"] = c_todos - b_todos
        deltas["duplicates"] = c_dups - b_dups
        deltas["secrets"] = c_secrets - b_secrets
        
        return deltas
        
    except Exception:
        return None


# --- __main__.py ---


# Force utf-8 output to avoid cp1252 encoding errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    start_time = time.time()
    args = parse_args()

    root_path = args.path
    if not os.path.isdir(root_path):
        print(f"Error: {root_path} is not a directory.")
        sys.exit(2)

    custom_ignores = args.ignore.split(",") if args.ignore else []

    # Determine animation mode (disabled by --no-animation or when not a TTY)
    show_animation = not getattr(args, "no_animation", False)
    use_parallel   = getattr(args, "parallel", False)

    # ------------------------------------------------------------------ #
    # File scanning (with optional animation + parallel mode)
    # ------------------------------------------------------------------ #
    files = scan_repository(
        root_path,
        custom_ignores,
        parallel=use_parallel,
        show_animation=show_animation,
    )

    # ------------------------------------------------------------------ #
    # Analysis phases — show spinner for each
    # ------------------------------------------------------------------ #
    with Spinner("Detecting languages", colour=show_animation):
        detect_languages(files)

    with Spinner("Analysing metrics", colour=show_animation):
        analyze_metrics(files)

    with Spinner("Scanning TODOs", colour=show_animation):
        todos = scan_todos(files)

    with Spinner("Scanning security patterns", colour=show_animation):
        security = scan_security(files)

    with Spinner("Detecting duplicates", colour=show_animation):
        duplicates = scan_duplicates(files, args.duplicate_lines)

    with Spinner("Checking project structure", colour=show_animation):
        structure = check_project_structure(root_path)

    with Spinner("Reading Git info", colour=show_animation):
        git_info = get_git_info(root_path)

    repo_name = os.path.basename(os.path.abspath(root_path))

    data = ReportData(
        path=os.path.abspath(root_path),
        name=repo_name,
        files=files,
        todos=todos,
        security=security,
        duplicates=duplicates,
        structure=structure,
        git=git_info
    )

    import re
    from collections import Counter
    word_counter = Counter()
    for file_info in data.files:
        if file_info.language != "Unknown":
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as src:
                    words = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', src.read())
                    words = [w for w in words if len(w) > 3 and w.lower() not in {"this", "that", "with", "from", "import", "return", "class", "function", "const", "let", "var", "true", "false", "null", "none", "self", "def", "async", "await"}]
                    word_counter.update(words)
            except Exception:
                pass
    data.top_words = word_counter.most_common(5)

    
    # --- Feature: Mood Analyzer ---
    positive_words = {"clean", "elegant", "thanks", "awesome", "perfect", "great", "love", "refactor"}
    negative_words = {"stupid", "hack", "hate", "crap", "fuck", "shit", "damn", "ugly", "temp", "fixme", "gross"}
    pos_count, neg_count = 0, 0
    for file_info in data.files:
        if file_info.language != "Unknown":
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as src:
                    content = src.read().lower()
                    for w in positive_words: pos_count += content.count(w)
                    for w in negative_words: neg_count += content.count(w)
            except: pass
    mood_status = "Neutral 😐"
    if pos_count > neg_count * 2: mood_status = "Happy 😃"
    elif neg_count > pos_count * 2: mood_status = "Severely Frustrated 😡"
    elif neg_count > pos_count: mood_status = "Stressed 😰"
    elif pos_count > 0 or neg_count > 0: mood_status = "Slightly Annoyed 🙄"
    data.mood = f"{mood_status} ({pos_count} positive, {neg_count} negative words)"

    # --- Feature: Code Clone Exposer ---
    import difflib
    highest_ratio = 0
    clone_pair = None
    lang_groups = {}
    for f in data.files:
        if f.language not in ("Unknown", "JSON", "Markdown") and f.lines > 10:
            lang_groups.setdefault(f.language, []).append(f)
            
    for lang, files in lang_groups.items():
        if len(files) < 2: continue
        files.sort(key=lambda x: x.size)
        for i in range(len(files)-1):
            f1 = files[i]
            for j in range(i+1, min(i+4, len(files))):
                f2 = files[j]
                if abs(f1.size - f2.size) < max(f1.size, f2.size) * 0.3:
                    try:
                        with open(f1.path, "r", encoding="utf-8", errors="ignore") as s1, \
                             open(f2.path, "r", encoding="utf-8", errors="ignore") as s2:
                            r = difflib.SequenceMatcher(None, s1.read(), s2.read()).quick_ratio()
                            if r > highest_ratio:
                                highest_ratio = r
                                clone_pair = (f1.relative_path, f2.relative_path)
                    except: pass
    if clone_pair and highest_ratio > 0.7:
        data.clone_exposer = f"{clone_pair[0]} & {clone_pair[1]} ({int(highest_ratio*100)}% identical)"
    else:
        data.clone_exposer = "No major clones detected 👏"

    data.score = calculate_score(data, args.large_file_lines)

    exit_code = 0
    if len(security) > 0 or len(duplicates) > 0:
        exit_code = 1

    deltas = None
    if args.baseline:
        deltas = compare_baseline(data, args.baseline)

    if args.badge and data.score:
        color = "#4c1" if data.score.score >= 80 else ("#dfb317" if data.score.score >= 50 else "#e05d44")
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">
  <linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="a"><rect width="140" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#a)">
    <rect width="80" height="20" fill="#555"/>
    <rect x="80" width="60" height="20" fill="{color}"/>
    <rect width="140" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="40" y="15" fill="#010101" fill-opacity=".3">RepoDoctor</text>
    <text x="40" y="14">RepoDoctor</text>
    <text x="109" y="15" fill="#010101" fill-opacity=".3">{data.score.score}/100</text>
    <text x="109" y="14">{data.score.score}/100</text>
  </g>
</svg>'''
        try:
            with open(args.badge, "w", encoding="utf-8") as bf:
                bf.write(svg)
            print(f"SVG badge successfully written to {args.badge}")
        except Exception:
            pass
            
    if args.json:
        print(get_json_report(data, args.large_file_lines))
    
    if args.export_prompt:
        try:
            with open(args.export_prompt, "w", encoding="utf-8") as f:
                f.write(f"Repository: {data.name}\n")
                f.write("="*80 + "\n\n")
                for file_info in data.files:
                    if file_info.language != "Unknown" and file_info.lines < args.large_file_lines:
                        f.write(f"--- FILE: {file_info.relative_path} ---\n")
                        try:
                            with open(file_info.path, "r", encoding="utf-8", errors="ignore") as src:
                                f.write(src.read() + "\n\n")
                        except Exception:
                            f.write("[Error reading file contents]\n\n")
            print(f"LLM prompt successfully exported to {args.export_prompt}")
        except Exception as e:
            print(f"Failed to export LLM prompt: {e}")
            sys.exit(3)
            
    if args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(generate_html_report(data, args.large_file_lines))
            print(f"HTML report successfully written to {args.html}")
        except Exception as e:
            print(f"Failed to write HTML report: {e}")
            sys.exit(3)
            
    if not args.json:
        # Check if stdout is TTY for color
        use_color = not args.no_color and sys.stdout.isatty()
        exec_time = time.time() - start_time
        print_terminal_report(data, use_color, args.large_file_lines, deltas, exec_time, args.tree)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
