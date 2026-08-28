import os
from pathlib import Path
from typing import List, Set, Optional

from .models import FileInfo

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
