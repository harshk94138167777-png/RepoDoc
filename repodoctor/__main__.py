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
from .spinner import Spinner

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
