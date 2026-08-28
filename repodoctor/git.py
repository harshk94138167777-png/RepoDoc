import subprocess
import os
from .models import GitInfo

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
