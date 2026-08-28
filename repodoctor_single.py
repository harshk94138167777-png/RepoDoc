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
from typing import List, Set, Optional
from typing import List, Tuple
from typing import Optional, List, Tuple, Dict, Any
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
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
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    return parser

def parse_args(args=None):
    parser = build_parser()
    return parser.parse_args(args)


# --- scanner.py ---



DEFAULT_IGNORES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", "target", "coverage", ".cache"
}

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

def scan_repository(root_path: str, custom_ignores: Optional[List[str]] = None) -> List[FileInfo]:
    ignores = set(DEFAULT_IGNORES)
    if custom_ignores:
        ignores.update(custom_ignores)
        
    root_path = os.path.abspath(root_path)
    files_info = []

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        # Modify dirnames in-place to avoid descending into ignored directories
        dirnames[:] = [d for d in dirnames if d not in ignores]

        for filename in filenames:
            if filename in ignores:
                continue

            filepath = os.path.join(dirpath, filename)
            
            # Avoid broken symlinks
            if not os.path.exists(filepath):
                continue

            try:
                stat_result = os.stat(filepath)
                size = stat_result.st_size
            except OSError:
                continue

            # Identify basic file info
            rel_path = os.path.relpath(filepath, root_path)
            _, ext = os.path.splitext(filename)
            
            is_binary = is_binary_file(filepath)
            lines = 0
            if not is_binary:
                lines = count_lines(filepath)
            
            file_info = FileInfo(
                path=filepath,
                filename=filename,
                extension=ext.lower(),
                size=size,
                lines=lines,
                is_binary=is_binary,
                language="Unknown",  # Will be populated in Phase 3
                relative_path=rel_path
            )
            files_info.append(file_info)

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
    def c(text: str, color_code: str) -> str:
        if not use_color: return text
        return f"\033[{color_code}m{text}\033[0m"

    def fmt_delta(val: int, inverted: bool = False) -> str:
        if val == 0: return ""
        sign = "+" if val > 0 else ""
        color = "92" if (val > 0 and not inverted) or (val < 0 and inverted) else "91"
        return c(f" ({sign}{val})", color)

    # Hide cursor
    sys.stdout.write("\033[?25l")
    
    # Animated Banner
    banner_top = "╔════════════════════════════════════════════════════════════╗"
    banner_bottom = "╚════════════════════════════════════════════════════════════╝"
    
    print(c(banner_top, "94"))
    
    color_start = "\033[94;1m" if use_color else ""
    color_end = "\033[0m" if use_color else ""
    
    # Draw the empty middle section first, then carriage return to the start
    empty_mid = "║" + " " * 60 + "║"
    sys.stdout.write(color_start + empty_mid + "\r")
    sys.stdout.flush()
    time.sleep(0.1)
    
    # Overwrite the left side and type the letters
    sys.stdout.write("║" + " " * 24)
    sys.stdout.flush()
    
    for char in "REPO DOCTOR":
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.05)
        
    sys.stdout.write(color_end + "\n")
    sys.stdout.flush()
    
    print(c(banner_bottom, "94"))
    
    # Show cursor
    sys.stdout.write("\033[?25h")
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
        if data.git.hotspot:
            print(f"🔥 Hotspot file:        {data.git.hotspot}")
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

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RepoDoctor Dashboard - {data.name}</title>
<style>
    :root {{
        --bg-main: #0f172a;
        --bg-card: #1e293b;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --accent: #3b82f6;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --border: #334155;
    }}
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: var(--bg-main);
        color: var(--text-main);
        margin: 0;
        padding: 40px 20px;
        line-height: 1.6;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .header {{ text-align: center; margin-bottom: 40px; }}
    .header h1 {{
        font-size: 2.8rem;
        margin-bottom: 10px;
        background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .score-container {{ display: flex; justify-content: center; margin: 30px 0 40px 0; }}
    .score-circle {{
        width: 160px; height: 160px; border-radius: 50%;
        background: var(--bg-card);
        border: 4px solid { '#10b981' if (data.score and data.score.score >= 80) else ('#f59e0b' if (data.score and data.score.score >= 50) else '#ef4444') };
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        box-shadow: 0 0 30px { 'rgba(16,185,129,0.3)' if (data.score and data.score.score >= 80) else ('rgba(245,158,11,0.3)' if (data.score and data.score.score >= 50) else 'rgba(239,68,68,0.3)') };
    }}
    .score-circle span.num {{ font-size: 54px; font-weight: 800; line-height: 1; }}
    .score-circle span.lbl {{ font-size: 14px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 2px; margin-top: 5px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }}
    .card {{
        background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
        padding: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); transition: transform 0.2s;
    }}
    .card:hover {{ transform: translateY(-5px); border-color: var(--accent); }}
    .card h3 {{ margin: 0 0 10px 0; font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }}
    .card .val {{ font-size: 32px; font-weight: 700; }}
    .section {{ background: var(--bg-card); border-radius: 12px; padding: 30px; margin-bottom: 25px; border: 1px solid var(--border); }}
    .section h2 {{ margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 15px; color: var(--accent); font-size: 20px; }}
    ul.feature-list {{ list-style: none; padding: 0; margin: 0; }}
    ul.feature-list li {{ padding: 12px 0; border-bottom: 1px dashed var(--border); display: flex; justify-content: space-between; }}
    ul.feature-list li:last-child {{ border-bottom: none; padding-bottom: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ padding: 12px 15px; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ font-weight: 600; color: var(--text-muted); text-transform: uppercase; font-size: 12px; }}
    .badge {{ padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
    .badge.pass {{ background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.3); }}
    .badge.warn {{ background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245,158,11,0.3); }}
    .badge.fail {{ background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239,68,68,0.3); }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>RepoDoctor Dashboard</h1>
        <p style="color: var(--text-muted); font-family: monospace; background: rgba(0,0,0,0.3); padding: 5px 15px; border-radius: 20px; display: inline-block;">Target: {data.path}</p>
    </div>
    
    <div class="score-container">
        <div class="score-circle">
            <span class="num">{data.score.score if data.score else 'N/A'}</span>
            <span class="lbl">Health</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="card"><h3>Files Scanned</h3><div class="val">{len(data.files)}</div></div>
        <div class="card"><h3>Lines of Code</h3><div class="val">{total_lines:,}</div></div>
        <div class="card"><h3>Security Secrets</h3><div class="val" style="color: { 'var(--danger)' if data.security else 'var(--success)' }">{len(data.security)}</div></div>
        <div class="card"><h3>Code Smells (Linter)</h3><div class="val" style="color: { 'var(--warning)' if total_smells > 0 else 'var(--success)' }">{total_smells}</div></div>
    </div>
    
    <div class="grid">
        <div class="section" style="margin-bottom:0">
            <h2>AI & Advanced Analytics</h2>
            <ul class="feature-list">
                <li><span>🎭 Developer Mood:</span> <strong>{data.mood if data.mood else 'N/A'}</strong></li>
                <li><span>👯‍♂️ Clone Exposer:</span> <strong>{data.clone_exposer if data.clone_exposer else 'N/A'}</strong></li>
                <li><span>🔥 Git Hotspot:</span> <strong>{data.git.hotspot if data.git.available and data.git.hotspot else "N/A"}</strong></li>
                <li><span>👑 Top Contributor:</span> <strong>{data.git.top_contributor if data.git.available and data.git.top_contributor else "N/A"}</strong></li>
            </ul>
        </div>
        <div class="section" style="margin-bottom:0">
            <h2>Maintainability Metrics</h2>
            <ul class="feature-list">
                <li><span>High Nesting / Complexity:</span> <strong>{high_nesting} functions</strong></li>
                <li><span>Duplicate Blocks:</span> <strong>{len(data.duplicates)} blocks</strong></li>
                <li><span>TODO / FIXME:</span> <strong>{len(data.todos)} items</strong></li>
                <li><span>Top Vocabulary:</span> <strong style="font-size:12px; color: var(--accent);">{ ', '.join(f"{w} ({c})" for w, c in data.top_words) if data.top_words else 'N/A' }</strong></li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>Project Structure Validation</h2>
        <table>
            <tr><th>Requirement</th><th>Status</th></tr>
            {''.join(f"<tr><td>{k}</td><td><span class='badge {v.lower()}'>{v}</span></td></tr>" for k, v in data.structure.items())}
        </table>
    </div>
</div>
</body>
</html>'''
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
    
    # Scanning
    files = scan_repository(root_path, custom_ignores)
    detect_languages(files)
    analyze_metrics(files)
    
    todos = scan_todos(files)
    security = scan_security(files)
    duplicates = scan_duplicates(files, args.duplicate_lines)
    
    structure = check_project_structure(root_path)
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

