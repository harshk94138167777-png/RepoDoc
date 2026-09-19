"""
Typo scanner using Python standard library only.
Scans for potential typos in code and documentation.
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


# Common programming terms and words to avoid false positives
PROGRAMMING_TERMS = {
    'api', 'app', 'arg', 'args', 'argv', 'ascii', 'async', 'auth', 'auto', 'avg',
    'bool', 'btn', 'buf', 'calc', 'cfg', 'char', 'cli', 'cmd', 'config', 'const',
    'ctx', 'curr', 'db', 'debug', 'def', 'del', 'desc', 'dev', 'dict', 'dir', 'div',
    'doc', 'docs', 'elem', 'env', 'err', 'eval', 'exec', 'expr', 'func', 'github',
    'html', 'http', 'https', 'idx', 'impl', 'init', 'int', 'iter', 'json', 'len',
    'lib', 'linux', 'log', 'max', 'min', 'msg', 'num', 'obj', 'os', 'param', 'params',
    'pkg', 'prev', 'proc', 'ptr', 'py', 'regex', 'repo', 'req', 'res', 'ret', 'src',
    'std', 'str', 'struct', 'sub', 'sync', 'sys', 'temp', 'tmp', 'txt', 'ui', 'url',
    'usr', 'util', 'utils', 'val', 'var', 'vars', 'ver', 'xml', 'yml', 'admin',
    'backend', 'boolean', 'frontend', 'middleware', 'namespace', 'stdout', 'stderr',
    'stdin', 'github', 'gitlab', 'bitbucket', 'webpack', 'node', 'npm', 'localhost',
}

# Common typos with their corrections
COMMON_TYPOS = {
    'recieve': 'receive',
    'reciept': 'receipt',
    'teh': 'the',
    'tehm': 'them',
    'thier': 'their',
    'becuase': 'because',
    'occured': 'occurred',
    'seperate': 'separate',
    'definately': 'definitely',
    'occurance': 'occurrence',
    'existance': 'existence',
    'persistance': 'persistence',
    'resistence': 'resistance',
    'maintainance': 'maintenance',
    'performence': 'performance',
    'reponse': 'response',
    'responce': 'response',
    'succesful': 'successful',
    'sucessful': 'successful',
    'successfull': 'successful',
    'untill': 'until',
    'wierd': 'weird',
    'yeild': 'yield',
    'lenght': 'length',
    'widht': 'width',
    'heigth': 'height',
    'colour': 'color',  # US spelling preference in code
    'favour': 'favor',
    'behaviour': 'behavior',
    'initialise': 'initialize',
    'organise': 'organize',
    'recognise': 'recognize',
}


class TypoFinding:
    """Represents a potential typo found in a file."""
    def __init__(self, file_path: str, line_num: int, word: str, suggestion: str = None):
        self.file_path = file_path
        self.line_num = line_num
        self.word = word
        self.suggestion = suggestion


def scan_typos(files: List) -> List[TypoFinding]:
    """
    Scan files for potential typos.
    
    Args:
        files: List of FileInfo objects
        
    Returns:
        List of TypoFinding objects
    """
    findings = []
    seen_findings = set()  # Track unique findings to avoid duplicates
    
    for file_info in files:
        if file_info.is_binary:
            continue
        
        # Only scan text-based files
        if not _should_scan_file(file_info.path):
            continue
        
        try:
            with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    # Extract words from the line
                    words = re.findall(r'[a-zA-Z]{3,}', line)
                    
                    for word in words:
                        word_lower = word.lower()
                        
                        # Skip programming terms
                        if word_lower in PROGRAMMING_TERMS:
                            continue
                        
                        # Check against known typos
                        if word_lower in COMMON_TYPOS:
                            finding_key = (file_info.path, line_num, word_lower)
                            if finding_key not in seen_findings:
                                findings.append(TypoFinding(
                                    file_path=file_info.path,
                                    line_num=line_num,
                                    word=word_lower,
                                    suggestion=COMMON_TYPOS[word_lower]
                                ))
                                seen_findings.add(finding_key)
        except Exception:
            # Skip files that can't be read
            continue
    
    return findings


def _should_scan_file(file_path: str) -> bool:
    """Determine if a file should be scanned for typos."""
    path = Path(file_path)
    ext = path.suffix.lower()
    
    # Scan text files, code files, and documentation
    scannable_extensions = {
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
        '.rs', '.rb', '.php', '.swift', '.kt', '.m', '.mm',
        '.md', '.txt', '.rst', '.adoc',
        '.json', '.yaml', '.yml', '.toml', '.xml', '.html', '.css', '.scss',
        '.sh', '.bash', '.zsh', '.fish',
        '.sql', '.r', '.lua', '.vim', '.pl',
    }
    
    return ext in scannable_extensions


def format_typo_report(findings: List[TypoFinding], files_scanned: int, use_color: bool = True) -> str:
    """
    Format the typo scan results into a human-readable report.
    
    Args:
        findings: List of TypoFinding objects
        files_scanned: Number of files that were scanned
        use_color: Whether to use ANSI color codes
        
    Returns:
        Formatted report string
    """
    def color(text, code):
        return f"\033[{code}m{text}\033[0m" if use_color else text
    
    report = []
    report.append("")
    report.append(color("Typo Scan", "96;1"))
    report.append(color("─────────", "90"))
    report.append(f"Files scanned: {files_scanned}")
    report.append(f"Potential typos found: {len(findings)}")
    report.append("")
    
    if len(findings) == 0:
        report.append(color("✓ No potential typos found.", "92"))
    else:
        # Group findings by file
        by_file = {}
        for finding in findings:
            if finding.file_path not in by_file:
                by_file[finding.file_path] = []
            by_file[finding.file_path].append(finding)
        
        # Display findings
        for file_path, file_findings in sorted(by_file.items()):
            report.append(color(f"\n{file_path}", "93"))
            for finding in file_findings:
                report.append(f"  Line {finding.line_num}: {color(finding.word, '91')}")
                if finding.suggestion:
                    report.append(f"    → suggested: {color(finding.suggestion, '92')}")
    
    report.append("")
    return "\n".join(report)
