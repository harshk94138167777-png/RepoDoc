import sys
import os
import time

# Force utf-8 output to avoid cp1252 encoding errors on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from .cli import parse_args
from .scanner import scan_repository
from .languages import detect_languages
from .metrics import analyze_metrics
from .todos import scan_todos
from .security import scan_security
from .duplicates import scan_duplicates
from .structure import check_project_structure
from .git import get_git_info
from .scoring import calculate_score
from .report import print_terminal_report, get_json_report, generate_html_report
from .baseline import compare_baseline
from .models import ReportData

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
    elif args.export_prompt:
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
    elif args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(generate_html_report(data, args.large_file_lines))
            print(f"HTML report successfully written to {args.html}")
        except Exception as e:
            print(f"Failed to write HTML report: {e}")
            sys.exit(3)
    else:
        # Check if stdout is TTY for color
        use_color = not args.no_color and sys.stdout.isatty()
        exec_time = time.time() - start_time
        print_terminal_report(data, use_color, args.large_file_lines, deltas, exec_time, args.tree)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

