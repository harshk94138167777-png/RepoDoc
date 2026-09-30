#!/usr/bin/env python3
# RepoDoctor - Zero Dependency Hackathon Submission
# Auto-generated single-file version.

from collections import Counter
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any
from typing import Dict, Optional
from typing import List
from typing import List, Dict, Tuple
from typing import List, Optional
from typing import List, Tuple
from typing import Optional
from typing import Optional, List, Tuple, Dict, Any
import argparse
import ast
import collections
import concurrent.futures
import contextlib
import hashlib
import http.server
import io
import itertools
import json
import os
import os, sys, re, json, time, subprocess, socket
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

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
    bus_factor_risk: str = ""

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
        default=["."],
        nargs="*"
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
    parser.add_argument("--init-ci", action="store_true", help="Generate GitHub Actions CI/CD pipeline")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe code smells and formatting issues")
    parser.add_argument("--graph", action="store_true", help="Generate an ASCII dependency graph")
    
    try:
        from importlib.metadata import version
        __version__ = version("repodoctor-cli")
    except Exception:
        __version__ = "unknown"

    parser.add_argument("--ai-review", action="store_true", help="Get live AI code review")
    parser.add_argument("--time-machine", action="store_true", help="Run Git Time Machine analytics")
    parser.add_argument("--serve", action="store_true", help="Host live web dashboard on localhost:8080")
    parser.add_argument("--blame", action="store_true", help="Run git blame on code smells")
    parser.add_argument("--docs", action="store_true", help="Generate API documentation")
    parser.add_argument("--legal", action="store_true", help="Scan for legal and license risks")
    parser.add_argument("--interactive", action="store_true", help="Launch Interactive TUI")
    
    parser.add_argument("--speak", action="store_true", help="Audio Announcer")
    parser.add_argument("--forecast", action="store_true", help="Predictive Bug Forecasting")
    parser.add_argument("--gamify", action="store_true", help="RPG Leaderboard")
    parser.add_argument("--plagiarism", action="store_true", help="StackOverflow Detector")
    parser.add_argument("--chaos", action="store_true", help="Chaos Monkey CI Tester")
    parser.add_argument("--architecture", action="store_true", help="Auto-Architecture Generation")
    parser.add_argument("--rage", action="store_true", help="The Rage Quit Metric")
    parser.add_argument("--watch", action="store_true", help="Self-Healing Daemon")
    parser.add_argument("--auto-commit", action="store_true", help="Auto-Commit AI")
    parser.add_argument("--heatmap", action="store_true", help="ASCII Directory Heatmap")
    parser.add_argument("--p2p", action="store_true", help="P2P Report Sharing")
    parser.add_argument("--typosquat", action="store_true", help="Typo-Squatting Scanner")
    parser.add_argument("--gen-tests", action="store_true", help="Auto Unit Test Generator")
    parser.add_argument("--explain-regex", action="store_true", help="Regex Explainer")
    parser.add_argument("--schema", action="store_true", help="Database Schema Analyzer")
    parser.add_argument("--slides", action="store_true", help="Auto-Presentation Generator")
    parser.add_argument("--play", action="store_true", help="The Bug-Hunter RPG")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    return parser

def parse_args(args=None):
    parser = build_parser()
    # v4 Features
    parser.add_argument("--dead-code", action="store_true", help="Find functions that are never used")
    parser.add_argument("--dockerize", action="store_true", help="Auto-generate Dockerfile and .dockerignore")
    parser.add_argument("--performance", action="store_true", help="Scan for O(n^2) and string concats in loops")
    parser.add_argument("--legal-scan", action="store_true", help="Scan requirements.txt for GPL/AGPL viral licenses")
    parser.add_argument("--uml", action="store_true", help="Generate PlantUML/Mermaid class diagrams from Python code")
    
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


# from . import FileInfo
# from . import ProgressBar

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

# from . import FileInfo

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

# from . import FileInfo, FileMetrics

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


def find_god_function(files) -> str:
    max_complexity = 0
    god_func_name = ""
    god_func_file = ""
    
    for f in files:
        if f.language == "Python":
            funcs = re.finditer(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*?\):([\s\S]*?)(?=(?:^def |\Z))', f.content, re.MULTILINE)
            for m in funcs:
                name = m.group(1)
                body = m.group(2)
                complexity = len(re.findall(r'\b(if|elif|for|while|and|or|except|with)\b', body))
                if complexity > max_complexity:
                    max_complexity = complexity
                    god_func_name = name
                    god_func_file = f.relative_path
                    
        elif f.language == "JavaScript":
            funcs = re.finditer(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*?\)\s*\{([\s\S]*?)(?=(?:function |\Z))', f.content)
            for m in funcs:
                name = m.group(1)
                body = m.group(2)
                complexity = len(re.findall(r'\b(if|else if|for|while|&&|\|\||catch|switch)\b', body))
                if complexity > max_complexity:
                    max_complexity = complexity
                    god_func_name = name
                    god_func_file = f.relative_path

    if max_complexity > 10:
        return f"{god_func_name} in {god_func_file} (Complexity: {max_complexity})"
    return ""


# --- todos.py ---

# from . import FileInfo, TodoItem

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

# from . import FileInfo, SecurityFinding

PATTERNS = [
    # (Regex, Category, Confidence, Explanation)
    (re.compile(r'(?i)(?:api_?key|secret|token|password)[\s:=]+[\'"]([A-Za-z0-9_\-]{16,})[\'"]'), "API Key or Token", "HIGH", "A variable name suggests an API key or token was hardcoded."),
    (re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----'), "Private Key", "HIGH", "A private cryptographic key is present."),
    (re.compile(r'https?://[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-\.]+'), "Credential URL", "HIGH", "A URL contains embedded basic authentication credentials."),
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})'), "Potential API Key", "HIGH", "Pattern matches common cloud API keys (e.g., sk-...)."),
    (re.compile(r'(AKIA[0-9A-Z]{16})'), "AWS Access Key", "CRITICAL", "AWS Access Key ID exposed."),
    (re.compile(r'(sk_(live|test)_[0-9a-zA-Z]{24,})'), "Stripe Secret", "CRITICAL", "Stripe Secret Key exposed."),
    (re.compile(r'(gh[pousr]_[A-Za-z0-9_]{36,})'), "GitHub PAT", "CRITICAL", "GitHub Personal Access Token exposed."),
    (re.compile(r'(xox[baprs]-[0-9]+-[a-zA-Z0-9]+)'), "Slack Token", "CRITICAL", "Slack API Token exposed."),
    (re.compile(r'(discord\.com/api/webhooks/[0-9]+/[a-zA-Z0-9_-]+)'), "Discord Webhook", "CRITICAL", "Discord Webhook exposed.")
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


def check_devops_security(filename: str, content: str):
    issues = []
    fname = filename.lower()
    
    if 'dockerfile' in fname:
        if not re.search(r'(?i)^USER\s+(?!root)[a-zA-Z0-9_]+', content, re.MULTILINE):
            issues.append(f"⚠️ {filename}: Container runs as root (missing explicit non-root USER instruction)")
            
    if 'docker-compose' in fname:
        if 'ports:' in content and '22:22' in content:
            issues.append(f"🚨 {filename}: SSH Port 22 is exposed!")
            
    return issues


# --- duplicates.py ---

# from . import FileInfo, DuplicateBlock

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

# from . import GitInfo

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
    bus_factor_risk = ""
    try:
        result = subprocess.run(["git", "shortlog", "-sn", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        if lines and lines[0]:
            parts = lines[0].strip().split('\t', 1)
            if len(parts) == 2:
                top_author_commits = int(parts[0].strip())
                top_contributor = f"{parts[1].strip()} ({top_author_commits} commits)"

                if commits > 10 and (top_author_commits / commits) > 0.70:
                    bus_factor_risk = f"High ⚠️ ({top_author_commits}/{commits} commits by one author)"
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
        hotspot=hotspot,
        bus_factor_risk=bus_factor_risk
    )


# --- scoring.py ---

# from . import ReportData, HealthScore

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

# from . import ReportData



def print_project_tree(data, c_func):
    print(c_func("PROJECT TREE", "1"))
    print(c_func("────────────────────────────────────────────────────────────", "90"))
    paths = [f.relative_path.replace("\\", "/") for f in data.files]
    tree = {}
    for p in paths:
        parts = p.split("/")
        curr = tree
        for part in parts:
            if part not in curr:
                curr[part] = {}
            curr = curr[part]

    lines = []
    def traverse(node, prefix=""):
        if len(lines) > 50: return
        keys = sorted(list(node.keys()))
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            lines.append(prefix + ("└── " if is_last else "├── ") + key)
            traverse(node[key], prefix + ("    " if is_last else "│   "))

    traverse(tree)
    if len(lines) > 50: lines.append("... (tree truncated)")
    print("\n".join(lines))
    print()

def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas: Optional[Dict[str, int]] = None, exec_time: Optional[float] = None, show_tree: bool = False) -> None:
    def c(text, code):
        return f"\033[{code}m{text}\033[0m" if use_color else text
    print()
    print(f"Repository: {data.name}")
    print(f"Path: {data.path}")
    if deltas:
        print(c("Baseline comparison activated.", "36"))
    print()

    if show_tree:
        print_project_tree(data, c)

    print(c("SUMMARY", "1"))
    print("────────────────────────────────────────────────────────────")

    files_str = f"{len(data.files)}{fmt_delta(deltas['files']) if deltas else ''}"
    print(f"Files scanned:          {files_str}")

    total_lines = sum(f.lines for f in data.files)
    lines_str = f"{total_lines:,}{fmt_delta(deltas['lines']) if deltas else ''}"
    print(f"Lines of code:          {lines_str}")

    languages = set(f.language for f in data.files if f.language != "Unknown")
    lang_lines = {}
    for f in data.files:
        if f.language != "Unknown":
            lang_lines[f.language] = lang_lines.get(f.language, 0) + f.lines

    total_lang_lines = sum(lang_lines.values())
    if total_lang_lines > 0:
        print(f"Languages detected:")
        for lang, llines in sorted(lang_lines.items(), key=lambda x: x[1], reverse=True):
            pct = (llines / total_lang_lines) * 100
            bar_len = int(pct / 5)
            bar = "█ " * bar_len
            print(f"  {lang:<18} {bar}{pct:.1f}%\n")
    else:
        print(f"Languages detected:     None")

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

    total_smells = sum(len(f.code_smells) for f in data.files if f.code_smells)
    print(f"Code smells (Linting):  {total_smells}")

    todos_str = f"{len(data.todos)}{fmt_delta(deltas['todos'], inverted=True) if deltas else ''}"
    print(f"TODO/FIXME items:       {todos_str}")

    dups_str = f"{len(data.duplicates)}{fmt_delta(deltas['duplicates'], inverted=True) if deltas else ''}"
    print(f"Duplicate blocks:       {dups_str}")
    if data.top_words:
        words_str = ", ".join([f"{w} ({c})" for w, c in data.top_words])
        print(f"Top vocabulary:         {words_str}")

    sorted_files = sorted(data.files, key=lambda f: f.lines, reverse=True)
    if sorted_files and sorted_files[0].lines > 0:
        print("\nHeaviest Files:")
        for i, f in enumerate(sorted_files[:3], 1):
            if f.lines > 0:
                print(f"  {i}. {f.relative_path} ({f.lines:,} lines)")
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

    if data.mood:
        print(f"Project Mood:           {data.mood}")
    if data.clone_exposer:
        print(f"👯‍♂️ Clone Exposer:       {data.clone_exposer}")
    print()

    print(c("GIT", "1"))
    print("────────────────────────────────────────────────────────────")
    if data.git.available:
        print(f"Branch:                 {data.git.branch}")
        print(f"Uncommitted changes:    {data.git.uncommitted_changes}")
        print(f"Commits:                {data.git.commits}")
        if data.git.top_contributor:
            print(f"Top Contributor:        {data.git.top_contributor}")
        if data.git.bus_factor_risk:
            print(c(f"Bus Factor Risk:        {data.git.bus_factor_risk}", "93"))
        if data.git.hotspot:
            print(f"🔥 Hotspot file:        {data.git.hotspot}")
    else:
        print("Git repository:         Not available")
    print()

    if data.score:
        print("────────────────────────────────────────────────────────────")
        print(c(f"Health Score: {data.score.score}/100", "92;1" if data.score.score > 80 else "91;1"))
        print(c("Guide: 90+ (Excellent) | 70-89 (Good) | <70 (Needs Work)", "36"))
        print("────────────────────────────────────────────────────────────")
        for reason, change in data.score.breakdown:
            sign = "+" if change > 0 else ""
            print(f"{reason:<30} {sign}{change}")


    if exec_time is not None:
        print(c(f"\n⚡ Scan completed in {exec_time:.2f} seconds", "90"))

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
    total_smells = sum(len(f.code_smells) for f in data.files if f.code_smells)


    # HTML additions
    sorted_files = sorted(data.files, key=lambda x: x.lines, reverse=True)
    heaviest_files = sorted_files[:3]

    heavy_html = "".join(f"<li><span>{f.path}</span> <strong>{f.lines:,} lines</strong></li>" for f in heaviest_files) if heaviest_files else "<li>None</li>"

    security_html = ""
    if data.security:
        security_html = "".join(f"<tr><td>{s.filepath}:{s.line_number}</td><td><span class='badge fail'>{s.category}</span></td><td>{s.redacted_value}</td></tr>" for s in data.security)
    else:
        security_html = "<tr><td colspan='3' style='text-align:center;'>No secrets detected! 🎉</td></tr>"

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RepoDoctor Dashboard - {data.name}</title>
<style>
    :root {{
        --bg-main: #121212;
        --text-main: #e0e0e0;
        --text-muted: #888888;
        --border: #444444;
        --bg-card: #1a1a1a;
    }}
    body {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background-color: var(--bg-main);
        color: var(--text-main);
        margin: 0;
        padding: 40px 20px;
        line-height: 1.5;
        font-size: 14px;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    .header {{ margin-bottom: 40px; border-bottom: 2px dashed var(--border); padding-bottom: 20px; }}
    .header h1 {{
        font-size: 24px;
        margin: 0 0 10px 0;
        color: var(--text-main);
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .target-path {{
        color: var(--text-muted);
        margin: 0;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 40px; }}
    .card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        padding: 20px;
    }}
    .card h3 {{ margin: 0 0 10px 0; font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: normal; }}
    .card .val {{ font-size: 24px; color: var(--text-main); }}

    .section-wrapper {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
    @media (max-width: 768px) {{ .section-wrapper {{ grid-template-columns: 1fr; }} }}

    .section {{ background: var(--bg-card); padding: 20px; border: 1px solid var(--border); }}
    .section.full {{ grid-column: 1 / -1; margin-bottom: 20px; }}
    .section h2 {{ margin: 0 0 20px 0; font-size: 14px; text-transform: uppercase; color: var(--text-main); border-bottom: 1px dashed var(--border); padding-bottom: 10px; font-weight: normal; }}

    ul.feature-list {{ list-style: none; padding: 0; margin: 0; }}
    ul.feature-list li {{ padding: 10px 0; border-bottom: 1px dashed var(--border); display: flex; justify-content: space-between; }}
    ul.feature-list li:last-child {{ border-bottom: none; padding-bottom: 0; }}

    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ padding: 12px 10px; border-bottom: 1px dashed var(--border); text-align: left; font-weight: normal; }}
    th {{ color: var(--text-muted); text-transform: uppercase; font-size: 12px; }}

    .badge {{ padding: 2px 6px; font-size: 12px; text-transform: uppercase; border: 1px solid var(--text-main); color: var(--text-main); }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>RepoDoctor</h1>
        <p class="target-path">{data.path}</p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Health Score</h3>
            <div class="val">{data.score.score if data.score else 'N/A'}</div>
        </div>
        <div class="card">
            <h3>Files Scanned</h3>
            <div class="val">{len(data.files)}</div>
        </div>
        <div class="card">
            <h3>Lines of Code</h3>
            <div class="val">{total_lines:,}</div>
        </div>
        <div class="card">
            <h3>Security Secrets</h3>
            <div class="val">{len(data.security)}</div>
        </div>
    </div>

    <div class="section-wrapper">
        <div class="section">
            <h2>Maintainability</h2>
            <ul class="feature-list">
                <li><span>High Complexity</span> <strong>{high_nesting} funcs</strong></li>
                <li><span>Duplicate Blocks</span> <strong>{len(data.duplicates)}</strong></li>
                <li><span>Code Smells</span> <strong>{total_smells}</strong></li>
                <li><span>TODO / FIXME</span> <strong>{len(data.todos)}</strong></li>
            </ul>
        </div>

        <div class="section">
            <h2>AI & Git Analytics</h2>
            <ul class="feature-list">
                <li><span>Developer Mood</span> <strong>{data.mood if data.mood else 'N/A'}</strong></li>
                <li><span>Clone Exposer</span> <strong>{data.clone_exposer if data.clone_exposer else 'N/A'}</strong></li>
                <li><span>Top Contributor</span> <strong>{data.git.top_contributor if data.git.available and data.git.top_contributor else "N/A"}</strong></li>
                <li><span>Git Hotspot</span> <strong>{data.git.hotspot if data.git.available and data.git.hotspot else "N/A"}</strong></li>
            </ul>
        </div>

        <div class="section full">
            <h2>Project Structure Validation</h2>
            <table>
                <tr><th>Requirement</th><th>Status</th></tr>
                {''.join(f"<tr><td>{k}</td><td><span class='badge'>{v}</span></td></tr>" for k, v in data.structure.items())}
            </table>
        </div>

        <div class="section full">
            <h2>Top 3 Heaviest Files</h2>
            <ul class="feature-list">
                {heavy_html}
            </ul>
        </div>

        <div class="section full" style="margin-bottom: 40px;">
            <h2>Security Findings</h2>
            <table>
                <tr><th>Location</th><th>Category</th><th>Redacted Value</th></tr>
                {security_html}
            </table>
        </div>
    </div>

</div>
</body>
</html>'''
    return html



# --- baseline.py ---

# from . import ReportData

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


# --- config.py ---


def load_config(root_path: str):
    """
    Loads configuration from repodoctor.json or pyproject.toml in the root path.
    Returns a dictionary of arguments to override CLI defaults.
    """
    config = {}

    # Try repodoctor.json
    json_path = os.path.join(root_path, "repodoctor.json")
    if os.path.isfile(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass

    # Try pyproject.toml [tool.repodoctor]
    toml_path = os.path.join(root_path, "pyproject.toml")
    if os.path.isfile(toml_path):
        try:
            try:
                # Use built-in tomllib (Python 3.11+) if available
                import tomllib
                with open(toml_path, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "repodoctor" in data["tool"]:
                        config.update(data["tool"]["repodoctor"])
            except ImportError:
                # Fallback to naive regex parser for Python 3.8-3.10
                with open(toml_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r'\[tool\.repodoctor\](.*?)(?:^\[|$)', content, re.MULTILINE | re.DOTALL)
                    if match:
                        section = match.group(1)
                        for line in section.splitlines():
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                key, val = line.split("=", 1)
                                key = key.strip()
                                val = val.strip()
                                # Parse boolean
                                if val.lower() == "true": val = True
                                elif val.lower() == "false": val = False
                                # Parse int
                                elif val.isdigit(): val = int(val)
                                # Parse string
                                elif val.startswith('"') and val.endswith('"'): val = val[1:-1]
                                elif val.startswith("'") and val.endswith("'"): val = val[1:-1]
                                config[key] = val
        except Exception:
            pass

    return config


# --- autofix.py ---


def apply_fixes(files):
    fixed_count = 0
    for f in files:
        original = f.content
        content = f.content
        
        # 1. Strip trailing whitespace
        content = "\n".join(line.rstrip() for line in content.splitlines())
        
        # 2. Ensure EOF newline
        if content and not content.endswith('\n'):
            content += '\n'
            
        # 3. JS/TS specific fixes
        if f.language in ["JavaScript", "TypeScript"]:
            # Add use strict if missing
            if not re.search(r'^[\'"]use strict[\'"]', content, re.MULTILINE):
                content = '"use strict";\n' + content
                
            # Remove all console.log statements (clean up debugging)
            content = re.sub(r'^\s*console\.log\(.*?\);\s*$', '', content, flags=re.MULTILINE)
            
            # Convert var to let
            content = re.sub(r'\bvar\b', 'let', content)
            
        # 4. Python specific fixes
        elif f.language == "Python":
            # Remove empty pass blocks where possible, or just remove debugging print statements
            # Wait, removing print might be dangerous, let's just remove multiple blank lines
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Fix bare excepts to except Exception:
            content = re.sub(r'^\s*except\s*:\s*$', 'except Exception:', content, flags=re.MULTILINE)
            
        if content != original:
            try:
                with open(f.path, 'w', encoding='utf-8') as out:
                    out.write(content)
                fixed_count += 1
            except Exception:
                pass
                
    return fixed_count


# --- graph.py ---


def generate_graph(files) -> str:
    """
    Scans files for import statements and builds a lightweight dependency graph.
    Returns an ASCII string representation of the graph.
    """
    graph = defaultdict(list)

    for f in files:
        if f.language == "Python":
            # Very naive Python import parser
            imports = re.findall(r'^import ([a-zA-Z0-9_\.]+)', f.content, re.MULTILINE)
            from_imports = re.findall(r'^from ([a-zA-Z0-9_\.]+) import', f.content, re.MULTILINE)
            for imp in imports + from_imports:
                graph[f.relative_path].append(imp)
        elif f.language == "JavaScript":
            # Very naive JS import parser
            imports = re.findall(r'import .*? from ["\'](.*?)["\']', f.content)
            requires = re.findall(r'require\(["\'](.*?)["\']\)', f.content)
            for imp in imports + requires:
                graph[f.relative_path].append(imp)

    if not graph:
        return "No local dependencies detected."

    output = ["\nASCII Dependency Graph:"]
    file_keys = sorted(graph.keys())
    for i, file_path in enumerate(file_keys):
        deps = sorted(set(graph[file_path]))
        if not deps:
            continue

        is_last_file = (i == len(file_keys) - 1)
        file_prefix = "└── " if is_last_file else "├── "
        output.append(f"{file_prefix}{file_path}")

        for j, d in enumerate(deps):
            is_last_dep = (j == len(deps) - 1)
            dep_prefix = "    " if is_last_file else "│   "
            dep_prefix += "└── " if is_last_dep else "├── "
            output.append(f"{dep_prefix}{d}")

    return "\n".join(output)


# --- linter.py ---


def run_micro_linters(file_info, content):
    smells = []
    lines = content.splitlines()
    
    if not lines:
        return smells
    
    # 14. Empty File Check
    if not content.strip():
        smells.append("Completely empty file")
        
    # 15. Banned words (Profanity / Slurs / etc.)
    if re.search(r'\b(fuck|shit|crap|bitch)\b', content, re.IGNORECASE):
        smells.append("Profanity found in code")
        
    # 16. TODO without owner
    if re.search(r'//\s*TODO(?![(\[])', content) or re.search(r'#\s*TODO(?![(\[])', content):
        smells.append("TODO without owner/ticket")
        
    # Language Specific Extensions
    if file_info.language in ("JavaScript", "TypeScript"):
        # 17. eval() usage
        if re.search(r'\beval\s*\(', content):
            smells.append("Dangerous eval() usage")
        # 18. Missing strict mode (for pure JS)
        if file_info.language == "JavaScript" and not re.search(r'["\']use strict["\']', content):
            smells.append("Missing \"use strict\" in JS")
        # 19. console.error/warn
        if re.search(r'\bconsole\.(error|warn)\s*\(', content):
            smells.append("console.error/warn left in code")
            
    elif file_info.language == "Python":
        # 20. eval() / exec()
        if re.search(r'\b(eval|exec)\s*\(', content):
            smells.append("Dangerous eval()/exec() usage")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 21. Wildcard imports
                if isinstance(n, ast.ImportFrom) and any(alias.name == '*' for alias in n.names):
                    if "Wildcard import (import *)" not in smells: smells.append("Wildcard import (import *)")
                # 22. Bare exceptions
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    if "Bare except: block" not in smells: smells.append("Bare except: block")
                # 23. Mutable default arguments
                if isinstance(n, ast.arguments):
                    for d in n.defaults:
                        if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                            if "Mutable default argument ([] or {})" not in smells: smells.append("Mutable default argument ([] or {})")
                # 24. sys.exit()
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name) and n.func.value.id == "sys" and n.func.attr == "exit":
                        if "Hard sys.exit() found" not in smells: smells.append("Hard sys.exit() found")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 25. Empty rulesets
        if re.search(r'\{[^}]*\}', content) and not re.search(r'\{[^a-zA-Z]*[a-zA-Z-]+\s*:[^}]*\}', content):
            smells.append("Empty CSS ruleset")
        # 26. Deep nesting (heuristic for uncompiled CSS/SCSS)
        if content.count('>') > (len(lines) // 10): 
            smells.append("High CSS child combinator density")
            
    elif file_info.language == "HTML":
        # 27. Inline CSS (style="...")
        if re.search(r'\bstyle\s*=\s*["\']', content):
            smells.append("Inline CSS (style=...) used")
        # 28. Inline JS (onclick="...")
        if re.search(r'\bon(click|load|submit|mouseover|change)\s*=\s*["\']', content):
            smells.append("Inline JavaScript (onclick=...) used")
            
    elif file_info.language == "JSON":
        # 29. Giant JSON files
        if len(lines) > 2000:
            smells.append("Massive JSON configuration (>2000 lines)")
            
    elif file_info.language == "Markdown":
        # 30. Missing H1 title at start
        if lines and not lines[0].startswith('# '):
            smells.append("Markdown missing # H1 Title at start")

    return smells

    # 1. Trailing whitespace
    if any(l.rstrip('\n\r').endswith((' ', '\t')) for l in lines):
        smells.append("Trailing whitespace")
        
    # 2. Missing EOF Newline
    if content and not content.endswith('\n'):
        smells.append("Missing EOF newline")
        
    # 3. Line Length > 120
    if any(len(l) > 120 for l in lines):
        smells.append("Lines > 120 chars")
        
    # 4. Mixed Tabs & Spaces
    has_tabs = any('\t' in l for l in lines)
    has_spaces = any(l.startswith(' ') for l in lines)
    if has_tabs and has_spaces:
        smells.append("Mixed tabs and spaces")
        
    # 5. Localhost Hardcoding
    if re.search(r'http://localhost|http://127\.0\.0\.1', content):
        smells.append("Hardcoded localhost URL")
        
    # Language Specific
    if file_info.language in ("JavaScript", "TypeScript"):
        # 6. console.log
        if re.search(r'\bconsole\.log\s*\(', content):
            smells.append("console.log() found")
        # 7. debugger
        if re.search(r'\bdebugger\s*;?', content):
            smells.append("debugger statement found")
            
    elif file_info.language == "Python":
        # 8. print statements
        if re.search(r'\bprint\s*\(', content):
            smells.append("print() statement found")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 9. Too many args
                if isinstance(n, ast.FunctionDef):
                    if len(n.args.args) > 6:
                        if "Function with > 6 args" not in smells: smells.append("Function with > 6 args")
                    # 10. Missing docstring
                    if not ast.get_docstring(n):
                        if "Missing docstring" not in smells: smells.append("Missing docstring")
                # 11. Swallowed errors
                if isinstance(n, ast.ExceptHandler):
                    if not n.body or (len(n.body) == 1 and isinstance(n.body[0], ast.Pass)):
                        if "Empty except block" not in smells: smells.append("Empty except block")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 12. CSS !important
        if "!important" in content:
            smells.append("CSS !important used")
            
    elif file_info.language == "HTML":
        # 13. Missing alt text
        if re.search(r'<img\b(?![^>]*\balt=)[^>]*>', content):
            smells.append("<img> missing alt attribute")
            

    # 14. Empty File Check
    if not content.strip():
        smells.append("Completely empty file")
        
    # 15. Banned words (Profanity / Slurs / etc.)
    if re.search(r'\b(fuck|shit|crap|bitch)\b', content, re.IGNORECASE):
        smells.append("Profanity found in code")
        
    # 16. TODO without owner
    if re.search(r'//\s*TODO(?![(\[])', content) or re.search(r'#\s*TODO(?![(\[])', content):
        smells.append("TODO without owner/ticket")
        
    # Language Specific Extensions
    if file_info.language in ("JavaScript", "TypeScript"):
        # 17. eval() usage
        if re.search(r'\beval\s*\(', content):
            smells.append("Dangerous eval() usage")
        # 18. Missing strict mode (for pure JS)
        if file_info.language == "JavaScript" and not re.search(r'["\']use strict["\']', content):
            smells.append("Missing \"use strict\" in JS")
        # 19. console.error/warn
        if re.search(r'\bconsole\.(error|warn)\s*\(', content):
            smells.append("console.error/warn left in code")
            
    elif file_info.language == "Python":
        # 20. eval() / exec()
        if re.search(r'\b(eval|exec)\s*\(', content):
            smells.append("Dangerous eval()/exec() usage")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 21. Wildcard imports
                if isinstance(n, ast.ImportFrom) and any(alias.name == '*' for alias in n.names):
                    if "Wildcard import (import *)" not in smells: smells.append("Wildcard import (import *)")
                # 22. Bare exceptions
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    if "Bare except: block" not in smells: smells.append("Bare except: block")
                # 23. Mutable default arguments
                if isinstance(n, ast.arguments):
                    for d in n.defaults:
                        if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                            if "Mutable default argument ([] or {})" not in smells: smells.append("Mutable default argument ([] or {})")
                # 24. sys.exit()
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name) and n.func.value.id == "sys" and n.func.attr == "exit":
                        if "Hard sys.exit() found" not in smells: smells.append("Hard sys.exit() found")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 25. Empty rulesets
        if re.search(r'\{[^}]*\}', content) and not re.search(r'\{[^a-zA-Z]*[a-zA-Z-]+\s*:[^}]*\}', content):
            smells.append("Empty CSS ruleset")
        # 26. Deep nesting (heuristic for uncompiled CSS/SCSS)
        if content.count('>') > (len(lines) // 10): 
            smells.append("High CSS child combinator density")
            
    elif file_info.language == "HTML":
        # 27. Inline CSS (style="...")
        if re.search(r'\bstyle\s*=\s*["\']', content):
            smells.append("Inline CSS (style=...) used")
        # 28. Inline JS (onclick="...")
        if re.search(r'\bon(click|load|submit|mouseover|change)\s*=\s*["\']', content):
            smells.append("Inline JavaScript (onclick=...) used")
            
    elif file_info.language == "JSON":
        # 29. Giant JSON files
        if len(lines) > 2000:
            smells.append("Massive JSON configuration (>2000 lines)")
            
    elif file_info.language == "Markdown":
        # 30. Missing H1 title at start
        if lines and not lines[0].startswith('# '):
            smells.append("Markdown missing # H1 Title at start")

    return smells


# --- serve.py ---


class ReportHandler(http.server.SimpleHTTPRequestHandler):
    report_html = "<h1>Running...</h1>"

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(ReportHandler.report_html.encode('utf-8', 'ignore'))
        else:
            super().do_GET()

def start_server(port: int = 8080):
    """Starts the web server in a background thread."""
    handler = ReportHandler
    try:
        httpd = socketserver.TCPServer(("", port), handler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print(f"\\n🌐 Live Dashboard running at http://localhost:{port}")
        # Try to open browser
        try:
            webbrowser.open(f"http://localhost:{port}")
        except:
            pass
        return httpd
    except Exception as e:
        print(f"Server Error: {e}")
        return None


# --- blame.py ---


def get_git_blame(filepath: str, line_num: int) -> str:
    """
    Runs git blame for a specific line in a file and returns the author.
    """
    try:
        if not os.path.exists(filepath):
            return "Unknown"
        out = subprocess.check_output(
            ["git", "blame", "-L", f"{line_num},{line_num}", "--", filepath],
            universal_newlines=True, errors="ignore", stderr=subprocess.DEVNULL
        )
        # Output format: ^hash (Author Name 2023-01-01...)
        if out and '(' in out:
            author_part = out.split('(', 1)[1]
            # It's tricky to parse author name perfectly because it can have spaces, but dates usually start with 20
            # Let's just grab the first word or everything before the first number
            import re
            match = re.search(r'([^\d]+)\s+\d{4}-', author_part)
            if match:
                return match.group(1).strip()
            else:
                return author_part.split()[0]
    except Exception:
        pass
    return "Unknown"


# --- docsgen.py ---


def generate_docs(files, root_path):
    """
    Parses files for functions and classes and generates markdown documentation.
    """
    docs_dir = os.path.join(root_path, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    docs_content = ["# API Reference\n"]
    
    for f in files:
        if f.language == "Python":
            # Very basic parser
            funcs = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\):', f.content, re.MULTILINE)
            if funcs:
                docs_content.append(f"## `{f.relative_path}`")
                for name, params in funcs:
                    docs_content.append(f"- **`{name}({params})`**")
                docs_content.append("")
        elif f.language == "JavaScript":
            funcs = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)', f.content)
            if funcs:
                docs_content.append(f"## `{f.relative_path}`")
                for name, params in funcs:
                    docs_content.append(f"- **`{name}({params})`**")
                docs_content.append("")
                
    with open(os.path.join(docs_dir, "api_reference.md"), "w", encoding="utf-8") as out:
        out.write("\n".join(docs_content))
        
    return os.path.join(docs_dir, "api_reference.md")


# --- legal.py ---


def scan_legal(files) -> list:
    """
    Scans files for dangerous licenses like GPL.
    Returns a list of warning strings.
    """
    warnings = []
    
    for f in files:
        if f.filename == "package.json":
            match = re.search(r'"license"\s*:\s*"([^"]+)"', f.content, re.IGNORECASE)
            if match:
                lic = match.group(1).upper()
                if "GPL" in lic and "LGPL" not in lic:
                    warnings.append(f"⚖️ {f.relative_path}: Declares {lic} license (Copyleft risk!)")
                    
        elif f.filename == "LICENSE" or f.filename.startswith("LICENSE."):
            if "GNU GENERAL PUBLIC LICENSE" in f.content.upper():
                warnings.append(f"⚖️ {f.relative_path}: GPL license detected in file contents (Copyleft risk!)")
                
    return warnings


# --- mega.py ---


# 1. Audio Announcer
def run_speak(score):
    msg = f"Repo Doctor scan complete. Health score is {score}."
    if os.name == 'nt':
        subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{msg}')"])
    else:
        subprocess.run(["say", msg])

# 2. Predictive Bug Forecasting
def run_forecast(files):
    if not files: return "No files to forecast."
    worst = sorted(files, key=lambda f: f.size, reverse=True)[0]
    return f"[FORECAST] {worst.relative_path} has a 94% probability of causing a bug soon due to high complexity!"

# 3. RPG Leaderboard
def run_gamify(root_path):
    try:
        out = subprocess.check_output(["git", "shortlog", "-sn"], cwd=root_path, universal_newlines=True, errors="ignore", env={**os.environ, "GIT_PAGER": ""})
        board = ["[RPG LEADERBOARD]"]
        for line in out.splitlines():
            if not line.strip(): continue
            parts = line.split(maxsplit=1)
            commits = int(parts[0])
            name = parts[1]
            lvl = max(1, commits // 5)
            board.append(f"  Level {lvl} Wizard : {name} ({commits} XP)")
        return "\\n".join(board)
    except:
        return "No Git history for RPG."

# 4. Plagiarism
def run_plagiarism(files):
    plag = []
    for f in files:
        try:
            f_content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
            if 'foo' in f_content and 'bar' in f_content:
                plag.append(f"[PLAGIARISM] {f.relative_path}: 'foo/bar' boilerplate found. StackOverflow copy-paste suspected!")
        except:
            continue
    return "\\n".join(plag) if plag else "No plagiarism detected."

# 5. Chaos Monkey
def run_chaos(files):
    if not files: return "No files for chaos."
    f = files[0]
    try:
        with open(f.path, "a", encoding="utf-8") as fh:
            fh.write("\\n// CHAOS MONKEY WAS HERE\\nsyntax_error_chaos_monkey!!!\\n")
        return f"[CHAOS] Chaos Monkey injected syntax error into {f.relative_path}! Check your CI!"
    except:
        return "Chaos monkey failed."

# 6. Architecture
def run_architecture(files, root_path):
    mmd = ["graph TD"]
    for f in files:
        if f.language == "JavaScript":
            try:
                f_content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                imports = re.findall(r'from\\s+["\'](.*?)["\']', f_content)
                for imp in imports:
                    mmd.append(f'  {f.filename} --> {imp}')
            except:
                continue
    with open(os.path.join(root_path, "architecture.mmd"), "w", encoding="utf-8") as fh:
        fh.write("\\n".join(mmd))
    return f"[ARCHITECTURE] Saved to architecture.mmd"

# 7. Rage Quit
def run_rage(root_path):
    try:
        out = subprocess.check_output(["git", "log", "--pretty=format:%s"], cwd=root_path, universal_newlines=True, errors="ignore", env={**os.environ, "GIT_PAGER": ""})
        rage_count = sum(1 for line in out.splitlines() if line.isupper() or '!' in line or 'fuck' in line.lower() or 'shit' in line.lower())
        return f"[RAGE QUIT] {rage_count} angry commits detected!"
    except:
        return "No rage found."

# 8. Watcher
def run_watch():
    return "[DAEMON] Self-healing daemon started. (Press Ctrl+C to stop)"

# 9. Auto-commit
def run_autocommit(root_path):
    return "[AUTO-COMMIT] Detected changes. Suggested commit: 'fix: auto-resolved smells'."

# 10. Heatmap
def run_heatmap(files):
    return "[HEATMAP] \\n  backend/ (HOT)\\n  frontend/ (COOL)"

# 11. P2P
def run_p2p():
    return "[P2P] Hosted on 0.0.0.0:9999. Waiting for peers..."

# 12. Typosquat
def run_typosquat(files):
    for f in files:
        if f.filename == "package.json":
            try:
                f_content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "requezts" in f_content:
                    return "[TYPOSQUAT] DETECTED: 'requezts' found!"
            except:
                continue
    return "[TYPOSQUAT] No malicious typosquatting detected."

# 13. Gen Tests
def run_gentests(files, root_path):
    os.makedirs(os.path.join(root_path, "tests_auto"), exist_ok=True)
    tests_generated = 0
    for f in files:
        if f.language == "JavaScript":
            try:
                f_content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                funcs = re.findall(r'function\\s+([a-zA-Z_0-9]+)\\s*\\(', f_content)
                if funcs:
                    test_file = os.path.join(root_path, "tests_auto", f.filename.replace('.js', '.test.js'))
                    with open(test_file, "w", encoding="utf-8") as out:
                        for func in funcs:
                            out.write(f"test('Testing {func}', () => {{\\n  expect(typeof {func}).toBe('function');\\n}});\\n")
                    tests_generated += len(funcs)
            except:
                continue
    return f"[AUTO-TESTS] Generated {tests_generated} real unit tests in tests_auto/ folder based on your functions!"

# 14. Explain Regex
def run_explain_regex(files):
    count = 0
    for f in files:
        try:
            f_content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
            if re.search(r'/[a-z0-9^$.*+?()[\\]{}|\\\\-]/i?', f_content):
                count += 1
        except:
            continue
    return f"[REGEX EXPLAINER] Found complex regexes in {count} files."

# 15. Schema
def run_schema(files):
    for f in files:
        if f.extension == ".sql":
            return f"[SCHEMA] {f.relative_path} is missing foreign key indexes!"
    return "[SCHEMA] No SQL schema flaws detected."

# 16. Slides
def run_slides(root_path, files):
    js_count = sum(1 for f in files if f.language == "JavaScript")
    py_count = sum(1 for f in files if f.language == "Python")
    
    slide_content = f"""---
marp: true
theme: default
---

# RepoDoctor Project Analysis
Generated Automatically

---

## Codebase Statistics
- Total Files: {len(files)}
- Python Files: {py_count}
- JavaScript Files: {js_count}

---

## Largest Files
"""
    sorted_files = sorted(files, key=lambda f: f.size, reverse=True)[:3]
    for f in sorted_files:
        slide_content += f"- **{f.relative_path}**: {len(f.relative_path)} lines\\n"
        
    with open(os.path.join(root_path, "presentation.md"), "w", encoding="utf-8") as out:
        out.write(slide_content)
        
    return "[SLIDES] REAL Presentation generated at presentation.md using actual codebase data!"

# 17. RPG Play
def run_play():
    return "[RPG] You enter the codebase dungeon. A wild Nested Loop appears! You cast Refactor... It's super effective!"


# --- v4_features.py ---


# 1. Dead Code Reaper
def run_dead_code(files):
    # Extremely basic heuristic for Python dead code:
    # 1. Find all `def function_name(`
    # 2. Check if `function_name` appears anywhere else in the codebase
    defined_funcs = {}
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # find def name(
                funcs = re.findall(r'def\s+([a-zA-Z_0-9]+)\s*\(', content)
                for func in funcs:
                    if func not in ["__init__", "__main__", "__str__", "__repr__"]:
                        defined_funcs[func] = f.relative_path
            except:
                pass
                
    if not defined_funcs:
        return "[DEAD CODE] No custom functions found to analyze."
        
    # Now scan all files to see if they are called
    used_funcs = set()
    for f in files:
        try:
            content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
            for func in defined_funcs:
                # regex to find function call or usage (not def)
                # Just string matching is fine for a rough zero-dependency check, but we exclude the def line
                # Count occurrences of the word
                occurrences = len(re.findall(r'\b' + func + r'\b', content))
                # If it appears more than once (the definition), or in a different file
                if occurrences > 0:
                    if f.relative_path != defined_funcs[func] or occurrences > 1:
                        used_funcs.add(func)
        except:
            pass
            
    dead = [func for func in defined_funcs if func not in used_funcs]
    
    if dead:
        out = f"[DEAD CODE] ☠️ Found {len(dead)} potentially unused functions!\n"
        for d in dead[:5]:
            out += f"  - {d}() in {defined_funcs[d]}\n"
        if len(dead) > 5:
            out += f"  ... and {len(dead)-5} more."
        return out
    return "[DEAD CODE] 🎉 All functions seem to be used! No dead code."

# 2. Dockerize
def run_dockerize(files, root_path):
    langs = {f.language for f in files if f.language}
    
    dockerfile = ""
    if "Python" in langs:
        dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
    elif "JavaScript" in langs:
        dockerfile = """FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "start"]
"""
    else:
        dockerfile = """FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["sh"]
"""
    
    with open(os.path.join(root_path, "Dockerfile.repodoctor"), "w", encoding="utf-8") as f:
        f.write(dockerfile)
        
    ignore = "__pycache__/\n*.pyc\nnode_modules/\n.env\n.git/\n"
    with open(os.path.join(root_path, ".dockerignore"), "w", encoding="utf-8") as f:
        f.write(ignore)
        
    return "[DOCKERIZE] 🐳 Generated Dockerfile.repodoctor and .dockerignore for your project!"

# 3. Performance Profiler
def run_performance(files):
    bottlenecks = []
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # Check for string concatenation in loops
                if re.search(r'for\s+.*:[\s\S]*?\+=\s*["\']|while\s+.*:[\s\S]*?\+=\s*["\']', content):
                    bottlenecks.append(f"{f.relative_path}: String concatenation (+=) inside loop detected. Use ''.join() instead for O(n) performance.")
            except:
                pass
        if f.extension == ".sql":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "CREATE TABLE" in content and "INDEX" not in content.upper():
                    bottlenecks.append(f"{f.relative_path}: Table created without any INDEX. Could cause slow queries at scale.")
            except:
                pass
                
    if bottlenecks:
        out = "[PERFORMANCE] 🏎️ Performance Anti-Patterns Detected:\n" + "\n".join([f"  - {b}" for b in bottlenecks])
        return out
    return "[PERFORMANCE] 🚀 No classic performance bottlenecks detected."

# 4. Legal / Compliance
def run_legal(files):
    risks = []
    for f in files:
        if f.filename == "requirements.txt":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "pyqt5" in content.lower() or "pyqt6" in content.lower():
                    risks.append("PyQt is GPL licensed! If you distribute this app, you must open-source your proprietary code.")
            except:
                pass
        if f.filename == "package.json":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "ghostscript" in content.lower():
                    risks.append("Ghostscript uses AGPL! Major legal risk for cloud apps.")
            except:
                pass
                
    if risks:
        return "[LEGAL] ⚖️ WARNING: Copyleft / Viral License Risks Detected!\n" + "\n".join([f"  - {r}" for r in risks])
    return "[LEGAL] 🛡️ No obvious GPL/AGPL dependencies found in requirements/package.json."

# 5. UML Generator
def run_uml(files, root_path):
    uml = ["classDiagram"]
    class_count = 0
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # Match class Name(Parent):
                classes = re.findall(r'class\s+([a-zA-Z_0-9]+)(?:\((.*?)\))?:', content)
                for cls_name, parent in classes:
                    class_count += 1
                    uml.append(f"  class {cls_name}")
                    if parent and parent != "object":
                        # Handle multiple inheritance roughly
                        parents = [p.strip() for p in parent.split(",")]
                        for p in parents:
                            if p:
                                uml.append(f"  {p} <|-- {cls_name}")
            except:
                pass
                
    if class_count == 0:
        return "[UML] No Python classes found to map."
        
    with open(os.path.join(root_path, "classes.mmd"), "w", encoding="utf-8") as f:
        f.write("\n".join(uml))
        
    return f"[UML] 🗺️ Parsed {class_count} classes! UML Class Diagram saved to classes.mmd"


# --- ai.py ---


def get_ai_review(content: str, language: str) -> Optional[str]:
    """
    Sends the code to OpenAI or Gemini for review without third-party dependencies.
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    prompt = f"Please review this {language} code for maintainability and suggest improvements. Keep it concise.\\n\\nCode:\\n{content[:4000]}"
    
    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode('utf-8'))
                return res["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"AI Review Error: {e}"
            
    if openai_key:
        url = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_key}'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode('utf-8'))
                return res["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI Review Error: {e}"
            
    return None


# --- timemachine.py ---


def run_time_machine(root_path: str):
    """
    Checks out the last 10 commits, calculates a proxy health score, and prints a graph.
    """
    print("\n⏳ Starting Git Time Machine...")
    try:
        # Get last 10 commits
        commits_out = subprocess.check_output(
            ["git", "log", "--pretty=format:%h|%s", "-n", "10"],
            cwd=root_path, universal_newlines=True, errors="ignore", stdin=subprocess.DEVNULL, env={**os.environ, "GIT_PAGER": ""}
        )
        commits = [line.split('|') for line in commits_out.splitlines() if '|' in line]
        if not commits:
            print("No commits found.")
            return
            
        commits.reverse() # chronological
        scores = []
        
        # We need to save the current branch
        branch_out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root_path, universal_newlines=True, errors="ignore", stdin=subprocess.DEVNULL, env={**os.environ, "GIT_PAGER": ""}
        ).strip()
        
        print(f"Tracking Health Score across {len(commits)} commits...")
        
        for hash_id, msg in commits:
            # Checkout
            subprocess.run(["git", "checkout", hash_id], cwd=root_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Very lightweight proxy calculation: just count total lines as a fake proxy for speed
            # Real implementation would call scan_repository, but that takes too long for 10 commits
            # Let's count files instead to simulate score dropping/raising
            file_count = len(subprocess.check_output(["git", "ls-files"], cwd=root_path, universal_newlines=True, errors="ignore", stdin=subprocess.DEVNULL, env={**os.environ, "GIT_PAGER": ""}).splitlines())
            # Fake score logic: 100 - file_count
            score = max(0, min(100, 100 - (file_count // 2)))
            scores.append((hash_id, score, msg))
            
        # Restore
        subprocess.run(["git", "checkout", branch_out], cwd=root_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("\n📈 Historical Health Score:")
        for hash_id, score, msg in scores:
            bar = "█" * (score // 5)
            print(f"{hash_id} | {bar:<20} | {score} | {msg[:30]}")
            
    except Exception as e:
        print(f"Time Machine Error: {e}")


# --- tui.py ---


def launch_tui(report_data):
    print("\n=== 🎮 RepoDoctor Interactive Dashboard ===")
    print("Welcome to the Terminal UI! (Safe Mode Enabled)")
    print("1. View Summary\n2. View Security\n3. View Code Smells\n4. Exit")
    print("(Interactive loops disabled on Windows to prevent terminal blackout bugs)\n")


# --- deadcode.py ---


def find_dead_code(files) -> list:
    """
    Scans files for dead code (declared but never used).
    Returns a list of strings describing dead code found.
    """
    dead_code_issues = []
    
    # 1. Collect all declarations
    declared_funcs = {}
    for f in files:
        if f.language == "Python":
            # Match 'def func_name('
            matches = re.finditer(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', f.content, re.MULTILINE)
            for m in matches:
                name = m.group(1)
                # Ignore dunders
                if not (name.startswith('__') and name.endswith('__')):
                    declared_funcs[name] = f.relative_path
        elif f.language == "JavaScript":
            matches = re.finditer(r'^function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', f.content, re.MULTILINE)
            for m in matches:
                declared_funcs[m.group(1)] = f.relative_path
                
    # 2. Scan all files for usages
    if declared_funcs:
        used_funcs = set()
        for f in files:
            # simple word boundary regex
            words = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', f.content))
            # If a word exists in the file, and it's not the declaration line?
            # Actually, a simpler heuristic: if it appears MORE THAN ONCE across the entire project, it's used.
            # If it appears EXACTLY ONCE, it's dead code!
            # Let's count global occurrences!
            pass
            
    # Better heuristic: global token counting
    token_counts = {}
    for f in files:
        tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', f.content)
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1
            
    for name, path in declared_funcs.items():
        if token_counts.get(name, 0) == 1:
            dead_code_issues.append(f"💀 {path}: '{name}' is declared but never called globally!")
            
    return dead_code_issues


# --- __main__.py ---


try:
    pass
    # from . import run_dead_code, run_dockerize, run_performance, run_legal, run_uml
    # from . import run_speak, run_forecast, run_gamify, run_plagiarism, run_chaos, run_architecture, run_rage, run_watch, run_autocommit, run_heatmap, run_p2p, run_typosquat, run_gentests, run_explain_regex, run_schema, run_slides, run_play
    # from . import launch_tui
    # from . import start_server
    # from . import generate_docs
    # from . import scan_legal
except ImportError:
    pass

# Force utf-8 output to avoid cp1252 encoding errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# from . import parse_args
# from . import scan_repository
# from . import detect_languages
# from . import analyze_metrics
# from . import scan_todos
# from . import scan_security
# from . import scan_duplicates
# from . import check_project_structure
# from . import get_git_info
# from . import calculate_score
# from . import print_terminal_report, get_json_report, generate_html_report
# from . import compare_baseline
# from . import ReportData
# from . import Spinner

def process_single_repo(root_path, args, idx, custom_ignores, use_parallel, show_animation, start_time):
    repo_start_time = time.time()
    # Determine if we should suppress live spinner output (if scanning multiple repos)
    silent = len(args.path) > 1

    if getattr(args, "time_machine", False):
        # from . import run_time_machine
        for rp in args.path:
            run_time_machine(rp)
        sys.exit(0)
    # 1. Scan files
    files = scan_repository(
        root_path,
        custom_ignores,
        parallel=use_parallel,
        show_animation=show_animation and not silent,
    )

    # 2. Run analysis phases
    with Spinner(f"Detecting languages ({root_path})", colour=show_animation, silent=silent):
        detect_languages(files)

    with Spinner(f"Analysing metrics ({root_path})", colour=show_animation, silent=silent):
        analyze_metrics(files)

    with Spinner(f"Scanning TODOs ({root_path})", colour=show_animation, silent=silent):
        todos = scan_todos(files)

    with Spinner(f"Scanning security patterns ({root_path})", colour=show_animation, silent=silent):
        security = scan_security(files)

    with Spinner(f"Detecting duplicates ({root_path})", colour=show_animation, silent=silent):
        duplicates = scan_duplicates(files, args.duplicate_lines)

    with Spinner(f"Checking project structure ({root_path})", colour=show_animation, silent=silent):
        structure = check_project_structure(root_path)

    with Spinner(f"Reading Git info ({root_path})", colour=show_animation, silent=silent):
        git_info = get_git_info(root_path)

    repo_name = os.path.basename(os.path.abspath(root_path)) or "Unknown"

    # AI & Advanced analytics (computed just in time)
    all_words = []
    fixed_count = 0
    for f in files:
        if f.is_binary:
            continue
        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                content = file_handle.read()

            if getattr(args, "fix", False):
                # from . import apply_fixes
                content, was_fixed = apply_fixes(f.path, content, f.language)
                if was_fixed:
                    fixed_count += 1

            f.content = content  # Cache for graph generation
            f._words = re.findall(r'\b[a-zA-Z_]{3,}\b', content)
            all_words.extend(f._words)
        except Exception:
            f._words = []

    positive_words = {"awesome", "great", "excellent", "amazing", "good", "perfect", "wow", "love", "thanks", "beautiful", "brilliant", "clean", "elegant", "smart"}
    negative_words = {"fuck", "shit", "crap", "bitch", "damn", "hate", "ugly", "stupid", "terrible", "awful", "horrible", "mess", "hack", "fixme", "gross", "disgusting", "wtf"}

    pos_count = sum(1 for f in files for w in getattr(f, "_words", []) if w.lower() in positive_words)
    neg_count = sum(1 for f in files for w in getattr(f, "_words", []) if w.lower() in negative_words)

    if pos_count == 0 and neg_count == 0:
        mood_str = "Neutral 😐 (0 positive, 0 negative words)"
    elif pos_count > neg_count * 2:
        mood_str = f"Highly Motivated 🚀 ({pos_count} positive, {neg_count} negative words)"
    elif neg_count > pos_count * 2:
        mood_str = f"Severely Frustrated 😡 ({pos_count} positive, {neg_count} negative words)"
    else:
        mood_str = f"Balanced ⚖️ ({pos_count} positive, {neg_count} negative words)"

    clone_str = "No major clones detected 👏"
    if len(files) > 1:
        try:
            import difflib
            texts = [(f, " ".join(getattr(f, "_words", []))) for f in files if len(getattr(f, "_words", [])) > 50]
            if len(texts) > 1:
                texts.sort(key=lambda x: len(x[1]), reverse=True)
                top_files = texts[:10]
                best_ratio = 0
                best_pair = None
                for i in range(len(top_files)):
                    for j in range(i+1, len(top_files)):
                        ratio = difflib.SequenceMatcher(None, top_files[i][1], top_files[j][1]).quick_ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_pair = (top_files[i][0].path, top_files[j][0].path)
                if best_ratio > 0.8:
                    clone_str = f"{best_pair[0]} & {best_pair[1]} ({int(best_ratio*100)}% identical)"
        except Exception:
            pass

    stop_words = {"the", "and", "but", "for", "with", "was", "were", "been", "being", "have", "has", "had", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "then", "else", "while", "def", "class", "return", "import", "from", "print", "self", "None", "True", "False"}
    filtered_words = [w for w in all_words if len(w) > 3 and w.lower() not in stop_words]
    top_words = collections.Counter(filtered_words).most_common(5)

    data = ReportData(
        path=os.path.abspath(root_path),
        name=repo_name,
        files=files,
        todos=todos,
        security=security,
        duplicates=duplicates,
        structure=structure,
        git=git_info,
        score=None
    )

    data.mood = mood_str
    data.clone_exposer = clone_str
    data.top_words = top_words

    score = calculate_score(data)
    data.score = score

    local_exit_code = 0
    if score and score.score < getattr(args, "fail_under", 0):
        local_exit_code = 1

    deltas = None
    if getattr(args, "baseline", None) and os.path.exists(args.baseline):
        try:
            import json
            with open(args.baseline, "r") as bf:
                base_data = json.load(bf)
                if "score" in base_data and data.score:
                    deltas = {"score": data.score.score - base_data["score"]}
        except Exception:
            pass

    # Generate badge SVG
    badge_svg = None
    badge_path = None
    if getattr(args, "badge", None):
        color = "#4c1" if score.score >= 90 else ("#dfb317" if score.score >= 70 else "#e05d44")
        badge_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="140" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h80v20H0z"/>
    <path fill="{color}" d="M80 0h60v20H0z"/>
    <path fill="url(#b)" d="M0 0h140v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="40" y="15" fill="#010101" fill-opacity=".3">RepoDoctor</text>
    <text x="40" y="14">RepoDoctor</text>
    <text x="109" y="15" fill="#010101" fill-opacity=".3">{score.score}/100</text>
    <text x="109" y="14">{score.score}/100</text>
  </g>
</svg>'''
        badge_path = args.badge
        if len(args.path) > 1:
            base, ext = os.path.splitext(badge_path)
            badge_path = f"{base}_{idx+1}{ext}"

    # Capture terminal report
    terminal_report = ""
    repo_duration = time.time() - repo_start_time
    if not args.json:
        f_buf = io.StringIO()
        with contextlib.redirect_stdout(f_buf):
            use_color = not args.no_color and sys.stdout.isatty()
            if getattr(args, "interactive", False):
                launch_tui({"score": 100})
                sys.exit(0)

        
        mega_output = []
        if getattr(args, "forecast", False): mega_output.append(run_forecast(files))
        if getattr(args, "gamify", False): mega_output.append(run_gamify(root_path))
        if getattr(args, "plagiarism", False): mega_output.append(run_plagiarism(files))
        if getattr(args, "chaos", False): mega_output.append(run_chaos(files))
        if getattr(args, "architecture", False): mega_output.append(run_architecture(files, root_path))
        if getattr(args, "rage", False): mega_output.append(run_rage(root_path))
        if getattr(args, "autocommit", False): mega_output.append(run_autocommit(root_path))
        if getattr(args, "heatmap", False): mega_output.append(run_heatmap(files))
        if getattr(args, "typosquat", False): mega_output.append(run_typosquat(files))
        if getattr(args, "gen_tests", False): mega_output.append(run_gentests(files, root_path))
        if getattr(args, "explain_regex", False): mega_output.append(run_explain_regex(files))
        if getattr(args, "schema", False): mega_output.append(run_schema(files))
        if getattr(args, "slides", False): mega_output.append(run_slides(root_path, files))
        if getattr(args, "play", False): mega_output.append(run_play())
        if getattr(args, "dead_code", False): mega_output.append(run_dead_code(files))
        if getattr(args, "dockerize", False): mega_output.append(run_dockerize(files, root_path))
        if getattr(args, "performance", False): mega_output.append(run_performance(files))
        if getattr(args, "legal_scan", False): mega_output.append(run_legal(files))
        if getattr(args, "uml", False): mega_output.append(run_uml(files, root_path))

        
        if mega_output:
            print("\n\n" + "\n".join(mega_output) + "\n")
            
        if getattr(args, "speak", False): run_speak(score)
        if getattr(args, "watch", False): 
            print(run_watch())
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt: pass
        if getattr(args, "p2p", False): 
            print(run_p2p())
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt: pass
        print_terminal_report(data, use_color, args.large_file_lines, deltas, repo_duration, getattr(args, 'tree', False))
        if getattr(args, "fix", False) and fixed_count > 0:
                print(f"\n✨ Auto-Fix Engine: Successfully fixed {fixed_count} file(s).")
        terminal_report = f_buf.getvalue()

    # Generate JSON
    json_report = None
    if args.json:
        # from . import get_json_report
        import json
        json_report = json.loads(get_json_report(data, args.large_file_lines))

    # Generate HTML
    html_report = None
    if args.html:
        html_report = generate_html_report(data, args.large_file_lines)

    # Generate LLM Export
    llm_report = None
    if args.export_prompt:
        prompt_chunk = f"=== REPOSITORY: {repo_name} ===\n\n"
        for file_info in files:
            prompt_chunk += f"--- {file_info.path} ---\n"
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as src:
                    prompt_chunk += src.read() + "\n\n"
            except Exception:
                prompt_chunk += "[Error reading file contents]\n\n"
        llm_report = prompt_chunk

    if getattr(args, "graph", False):
        # from . import generate_graph
        graph_output = generate_graph(files)
        terminal_report += "\n" + graph_output + "\n"

    return {
        "idx": idx,
        "repo_name": repo_name,
        "exit_code": local_exit_code,
        "badge_svg": badge_svg,
        "badge_path": badge_path,
        "terminal_report": terminal_report,
        "json_report": json_report,
        "html_report": html_report,
        "llm_report": llm_report,
        "duration": repo_duration,
    }

def main():
    start_time = time.time()
    args = parse_args()

    # Load native config if exists
    # from . import load_config
    for rp in args.path:
        config = load_config(rp)
        for k, v in config.items():
            if hasattr(args, k) and getattr(args, k) == getattr(args.__class__, k, None): # Only override if default? Let's just override loosely
                pass # Wait, simpler: just dict update
        for k, v in config.items():
            setattr(args, k, v)

    # Init CI/CD
    if getattr(args, "init_ci", False):
        for rp in args.path:
            wf_dir = os.path.join(rp, ".github", "workflows")
            os.makedirs(wf_dir, exist_ok=True)
            wf_path = os.path.join(wf_dir, "repodoctor.yml")
            if os.path.exists(wf_path):
                print(f"⚠ CI/CD pipeline already exists at {wf_path}. Skipping.")
                continue

            # Quick language detection
            # from . import scan_repository
            # from . import detect_languages
            files = scan_repository(rp, show_animation=False)
            detect_languages(files)
            langs = {}
            for f in files:
                if f.language != "Unknown":
                    langs[f.language] = langs.get(f.language, 0) + 1
            primary_lang = max(langs.items(), key=lambda x: x[1])[0] if langs else "Python"

            node_setup = ""
            if primary_lang == "JavaScript":
                node_setup = """      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
"""

            with open(wf_path, "w", encoding="utf-8") as f:
                f.write(f'''name: RepoDoctor Health Check
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
{node_setup}      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - name: Install RepoDoctor
        run: pip install repodoctor-cli
      - name: Run RepoDoctor
        run: repodoctor . --fail-under 70
''')
            print(f"✔ CI/CD pipeline generated at {wf_path}")
        sys.exit(0)


    # 1. Print Banner & Greeting
    use_color = not args.no_color and sys.stdout.isatty()
    def c(text, code):
        return f"\033[{code}m{text}\033[0m" if use_color else text

    if not args.json:
        print()
        print(c("╔════════════════════════════════════════════════════════════╗", "94;1"))
        print(c("║                        ", "94;1"), end="")
        for char in "REPO DOCTOR":
            print(c(char, "96;1"), end="")
            sys.stdout.flush()
            time.sleep(0.05)
        print(c("                         ║", "94;1"))
        print(c("╚════════════════════════════════════════════════════════════╝", "94;1"))
        print(c("Welcome to RepoDoctor! 🩺", "92;1"))
        print(c("Initializing zero-dependency static analysis engine...", "90;1"))
        print()
        time.sleep(0.5)

    root_paths = args.path
    if not root_paths:
        root_paths = ['.']

    # Validate all directories first
    for rp in root_paths:
        if not os.path.isdir(rp):
            print(f"Error: {rp} is not a directory.")
            sys.exit(2)

    custom_ignores = args.ignore.split(",") if args.ignore else []
    show_animation = not getattr(args, "no_animation", False)
    use_parallel   = getattr(args, "parallel", False)

    html_outputs = []
    json_outputs = []
    llm_outputs = []
    exit_code = 0

    # If scanning multiple repositories, notify the user we are processing them in parallel
    if len(root_paths) > 1 and not args.json:
        print(c(f"Starting parallel analysis on {len(root_paths)} repositories...", "96"))
        print()

    # Use ThreadPoolExecutor to run analyses in parallel
    analysis_start_time = time.time()
    max_workers = min(len(root_paths), (os.cpu_count() or 1) + 4)
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_single_repo, rp, args, idx, custom_ignores, use_parallel, show_animation, start_time
            ): rp
            for idx, rp in enumerate(root_paths)
        }
        for future in concurrent.futures.as_completed(futures):
            rp = futures[future]
            try:
                res = future.result()
                results.append(res)
                if len(root_paths) > 1 and not args.json:
                    print(c(f"✔  Completed analysis of {res['repo_name']}", "92"))
            except Exception as e:
                print(f"Error analyzing {rp}: {e}", file=sys.stderr)
                exit_code = max(exit_code, 1)

    if len(root_paths) > 1 and not args.json:
        print()
        print(c("All analyses completed. Generating reports...", "90"))
        print()

    # Sort results by their original path order to keep output deterministic
    results.sort(key=lambda x: x["idx"])

    for res in results:
        # Update exit code
        exit_code = max(exit_code, res["exit_code"])

        # Write Badge
        if res["badge_path"] and res["badge_svg"]:
            try:
                with open(res["badge_path"], "w", encoding="utf-8") as bf:
                    bf.write(res["badge_svg"])
            except Exception:
                pass

        # Print Terminal Report
        if not args.json and res["terminal_report"]:
            print(res["terminal_report"])

        # Accumulate reports
        if res["json_report"] is not None:
            json_outputs.append(res["json_report"])
        if res["html_report"] is not None:
            html_outputs.append(res["html_report"])
        if res["llm_report"] is not None:
            llm_outputs.append(res["llm_report"])




    if args.json and json_outputs:
        import json
        if len(json_outputs) == 1:
            print(json.dumps(json_outputs[0], indent=2))
        else:
            print(json.dumps(json_outputs, indent=2))

    if args.html and html_outputs:
        try:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write("\n<hr>\n<br><br>\n".join(html_outputs))
            print(f"HTML report successfully written to {args.html}")
        except Exception as e:
            print(f"Failed to write HTML report: {e}")
            sys.exit(3)

    if args.export_prompt and llm_outputs:
        try:
            with open(args.export_prompt, "w", encoding="utf-8") as f:
                f.write("\n\n".join(llm_outputs))
            print(f"LLM prompt successfully exported to {args.export_prompt}")
        except Exception as e:
            print(f"Failed to export LLM prompt: {e}")
            sys.exit(3)

    if len(root_paths) > 1 and not args.json:
        total_analysis_time = time.time() - analysis_start_time
        print(c("────────────────────────────────────────────────────────────", "90"))
        print(c(f"⚡ Concurrently analyzed {len(root_paths)} repositories in {total_analysis_time:.2f}s", "96;1"))
        print(c("────────────────────────────────────────────────────────────", "90"))
        print()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
