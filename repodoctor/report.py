import json
import sys
from .models import ReportData

from typing import Dict, Optional

def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas: Optional[Dict[str, int]] = None) -> None:
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
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f6f8fa; color: #24292f; margin: 0; padding: 20px; }}
    .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
    h1 {{ border-bottom: 1px solid #eaecef; padding-bottom: 10px; }}
    h2 {{ margin-top: 30px; border-bottom: 1px solid #eaecef; padding-bottom: 5px; color: #0969da; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
    .stat-card {{ background: #f6f8fa; padding: 15px; border-radius: 6px; border: 1px solid #d0d7de; text-align: center; }}
    .stat-value {{ font-size: 24px; font-weight: bold; color: #24292f; }}
    .stat-label {{ font-size: 14px; color: #57606a; margin-top: 5px; }}
    .score {{ font-size: 48px; font-weight: bold; text-align: center; margin: 20px 0; color: { '#2da44e' if (data.score and data.score.score > 80) else '#cf222e' }; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ padding: 8px 12px; border: 1px solid #d0d7de; text-align: left; }}
    th {{ background: #f6f8fa; }}
    .pass {{ color: #2da44e; font-weight: bold; }}
    .warn {{ color: #bf8700; font-weight: bold; }}
    .fail {{ color: #cf222e; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
    <h1>RepoDoctor Report: {data.name}</h1>
    <div class="score">{data.score.score if data.score else 'N/A'}<span style="font-size:24px;color:#57606a">/100</span></div>
    
    <h2>Summary</h2>
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">{len(data.files)}</div><div class="stat-label">Files Scanned</div></div>
        <div class="stat-card"><div class="stat-value">{total_lines:,}</div><div class="stat-label">Lines of Code</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.todos)}</div><div class="stat-label">TODO/FIXME Items</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.duplicates)}</div><div class="stat-label">Duplicate Blocks</div></div>
        <div class="stat-card"><div class="stat-value">{len(data.security)}</div><div class="stat-label">Potential Secrets</div></div>
    </div>
    
    <h2>Maintainability</h2>
    <ul>
        <li><b>Large Files:</b> {large_files}</li>
        <li><b>Long Functions (Heuristic):</b> {long_functions}</li>
        <li><b>High Nesting:</b> {high_nesting}</li>
        <li><b>Languages:</b> {', '.join(languages) if languages else 'None'}</li>
    </ul>

    <h2>Project Health</h2>
    <table>
        <tr><th>Check</th><th>Status</th></tr>
        {''.join(f"<tr><td>{k}</td><td class='{v.lower()}'>{v}</td></tr>" for k, v in data.structure.items())}
    </table>

    <h2>Security Findings</h2>
    { "<ul>" + "".join(f"<li><b>{s.filepath}:{s.line_number}</b> - {s.category} (Value: {s.redacted_value})</li>" for s in data.security) + "</ul>" if data.security else "<p>No secrets detected.</p>" }
    
    <h2>Git Info</h2>
    <p>{ f"Branch: {data.git.branch} | Commits: {data.git.commits} | Uncommitted Changes: {data.git.uncommitted_changes}" if data.git.available else "Git not available." }</p>
</div>
</body>
</html>"""
    return html

