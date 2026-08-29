import sys
import os
import time
import re
import concurrent.futures
import collections
import io
import contextlib

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

def process_single_repo(root_path, args, idx, custom_ignores, use_parallel, show_animation, start_time):
    repo_start_time = time.time()
    # Determine if we should suppress live spinner output (if scanning multiple repos)
    silent = len(args.path) > 1

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
    for f in files:
        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                content = file_handle.read()
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
            print_terminal_report(data, use_color, args.large_file_lines, deltas, repo_duration, getattr(args, 'tree', False))
        terminal_report = f_buf.getvalue()

    # Generate JSON
    json_report = None
    if args.json:
        from .report import get_json_report
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
