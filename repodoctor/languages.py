from .models import FileInfo
from typing import List

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
