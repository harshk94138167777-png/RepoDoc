import json
import sys
import time
from .models import ReportData

from typing import Dict, Optional


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

