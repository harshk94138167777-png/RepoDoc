import sys

try:
    pass
    from .mega import run_speak, run_forecast, run_gamify, run_plagiarism, run_chaos, run_architecture, run_rage, run_watch, run_autocommit, run_heatmap, run_p2p, run_typosquat, run_gentests, run_explain_regex, run_schema, run_slides, run_play
    from .tui import launch_tui
    from .serve import start_server
    from .docsgen import generate_docs
    from .legal import scan_legal
except ImportError:
    pass
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

    if getattr(args, "time_machine", False):
        from .timemachine import run_time_machine
        for rp in args.path:
            run_time_machine(rp)
        sys.exit(0)
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
    fixed_count = 0
    for f in files:
        if f.is_binary:
            continue
        try:
            with open(f.path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                content = file_handle.read()

            if getattr(args, "fix", False):
                from .autofix import apply_fixes
                content, was_fixed = apply_fixes(f.path, content, f.language)
                if was_fixed:
                    fixed_count += 1

            f.content = content  # Cache for graph generation
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
            if getattr(args, "interactive", False):
                launch_tui({"score": 100})
                sys.exit(0)

        
        mega_output = []
        if getattr(args, "forecast", False): mega_output.append(run_forecast(files))
        if getattr(args, "gamify", False): mega_output.append(run_gamify(root_path))
        if getattr(args, "plagiarism", False): mega_output.append(run_plagiarism(files))
        if getattr(args, "chaos", False): mega_output.append(run_chaos(files))
        if getattr(args, "architecture", False): mega_output.append(run_architecture(files, root_path))
        if getattr(args, "rage", False): mega_output.append(run_rage(root_path))
        if getattr(args, "autocommit", False): mega_output.append(run_autocommit(root_path))
        if getattr(args, "heatmap", False): mega_output.append(run_heatmap(files))
        if getattr(args, "typosquat", False): mega_output.append(run_typosquat(files))
        if getattr(args, "gen_tests", False): mega_output.append(run_gentests(files, root_path))
        if getattr(args, "explain_regex", False): mega_output.append(run_explain_regex(files))
        if getattr(args, "schema", False): mega_output.append(run_schema(files))
        if getattr(args, "slides", False): mega_output.append(run_slides(root_path))
        if getattr(args, "play", False): mega_output.append(run_play())
        
        if mega_output:
            print("\n\n" + "\n".join(mega_output) + "\n")
            
        if getattr(args, "speak", False): run_speak(score)
        if getattr(args, "watch", False): 
            print(run_watch())
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt: pass
        if getattr(args, "p2p", False): 
            print(run_p2p())
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt: pass
        print_terminal_report(data, use_color, args.large_file_lines, deltas, repo_duration, getattr(args, 'tree', False))
        if getattr(args, "fix", False) and fixed_count > 0:
                print(f"\n✨ Auto-Fix Engine: Successfully fixed {fixed_count} file(s).")
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

    if getattr(args, "graph", False):
        from .graph import generate_graph
        graph_output = generate_graph(files)
        terminal_report += "\n" + graph_output + "\n"

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
    """Main entry point with comprehensive error handling."""
    start_time = time.time()
    
    # Import scanner early for feature handling
    from .scanner import scan_repository
    from .languages import detect_languages
    from .metrics import analyze_metrics
    from .todos import scan_todos
    from .security import scan_security
    from .duplicates import scan_duplicates
    from .structure import check_project_structure
    from .git import get_git_info
    from .scoring import calculate_score
    
    try:
        args = parse_args()
    except SystemExit as e:
        # argparse calls sys.exit() on error or --help
        raise
    except KeyboardInterrupt:
        print("\nRepoDoctor: operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"RepoDoctor Error: {e}")
        sys.exit(2)

    # Handle special features that run independently
    # --play: Open a report file (early exit)
    if getattr(args, 'play', None):
        from .play import play_file
        success = play_file(args.play)
        sys.exit(0 if success else 1)
    
    # --typo: Scan for typos (early exit)
    if getattr(args, 'typo', False):
        from .typos import scan_typos, format_typo_report
        
        root_path = args.path[0] if args.path else '.'
        custom_ignores = args.ignore.split(",") if args.ignore else []
        use_parallel = getattr(args, "parallel", False)
        show_animation = not getattr(args, "no_animation", False)
        
        files = scan_repository(root_path, custom_ignores, parallel=use_parallel, show_animation=show_animation)
        detect_languages(files)
        
        typo_findings = scan_typos(files)
        files_scanned = sum(1 for f in files if not f.is_binary)
        use_color = not args.no_color and sys.stdout.isatty()
        
        print(format_typo_report(typo_findings, files_scanned, use_color))
        sys.exit(0)

    # Load native config if exists
    from .config import load_config
    for rp in args.path:
        config = load_config(rp)
        for k, v in config.items():
            if hasattr(args, k) and getattr(args, k) == getattr(args.__class__, k, None): # Only override if default? Let's just override loosely
                pass # Wait, simpler: just dict update
        for k, v in config.items():
            setattr(args, k, v)

    # Init CI/CD
    if getattr(args, "init_ci", False):
        for rp in args.path:
            wf_dir = os.path.join(rp, ".github", "workflows")
            os.makedirs(wf_dir, exist_ok=True)
            wf_path = os.path.join(wf_dir, "repodoctor.yml")
            if os.path.exists(wf_path):
                print(f"⚠ CI/CD pipeline already exists at {wf_path}. Skipping.")
                continue

            # Quick language detection
            from .scanner import scan_repository
            from .languages import detect_languages
            files = scan_repository(rp, show_animation=False)
            detect_languages(files)
            langs = {}
            for f in files:
                if f.language != "Unknown":
                    langs[f.language] = langs.get(f.language, 0) + 1
            primary_lang = max(langs.items(), key=lambda x: x[1])[0] if langs else "Python"

            node_setup = ""
            if primary_lang == "JavaScript":
                node_setup = """      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
"""

            with open(wf_path, "w", encoding="utf-8") as f:
                f.write(f'''name: RepoDoctor Health Check
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
{node_setup}      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - name: Install RepoDoctor
        run: pip install repodoctor-cli
      - name: Run RepoDoctor
        run: repodoctor . --fail-under 70
''')
            print(f"✔ CI/CD pipeline generated at {wf_path}")
        sys.exit(0)


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
    
    # Handle new features after analysis is complete
    # Only run if specific feature flags are provided
    if any([getattr(args, 'slides', None), getattr(args, 'schema', None), 
            getattr(args, 'test', False), getattr(args, 'heatmap', None),
            getattr(args, 'auto_commit', False)]):
        try:
            # Need to rescan if we have results (to get FileInfo objects with data)
            if results and len(root_paths) > 0:
                repo_path = root_paths[0]
                
                # Re-run analysis to get complete data
                files = scan_repository(repo_path, custom_ignores, parallel=use_parallel, show_animation=False)
                detect_languages(files)
                analyze_metrics(files)
                todos = scan_todos(files)
                security = scan_security(files)
                duplicates = scan_duplicates(files, args.duplicate_lines)
                structure = check_project_structure(repo_path)
                git_info = get_git_info(repo_path)
                repo_name = os.path.basename(os.path.abspath(repo_path)) or "Unknown"
                
                data = ReportData(
                    path=os.path.abspath(repo_path),
                    name=repo_name,
                    files=files,
                    todos=todos,
                    security=security,
                    duplicates=duplicates,
                    structure=structure,
                    git=git_info,
                    score=None
                )
                data.score = calculate_score(data)
                
                # --slides: Generate PowerPoint presentation
                if getattr(args, 'slides', None):
                    from .slides import create_pptx
                    output_path = args.slides
                    if not output_path:
                        output_path = "reports/repodoctor_report.pptx"
                    
                    print(c("\nGenerating PowerPoint slides...", "96"))
                    success = create_pptx(output_path, data)
                    
                    if success and os.path.exists(output_path):
                        print(c(f"✓ Slides generated successfully", "92"))
                        print(f"\nOutput:\n  {output_path}\n")
                    else:
                        print(c("✗ Failed to generate slides", "91"))
                        exit_code = max(exit_code, 1)
                
                # --schema: Generate JSON schema
                if getattr(args, 'schema', None):
                    from .schema import generate_schema
                    output_path = args.schema
                    if not output_path:
                        output_path = "reports/schema.json"
                    
                    print(c("\nGenerating repository schema...", "96"))
                    success = generate_schema(data, output_path)
                    
                    if success and os.path.exists(output_path):
                        print(c(f"✓ Schema generated successfully", "92"))
                        print(f"\nOutput:\n  {output_path}\n")
                    else:
                        print(c("✗ Failed to generate schema", "91"))
                        exit_code = max(exit_code, 1)
                
                # --test: Generate test files
                if getattr(args, 'test', False):
                    from .testgen import generate_tests, format_test_generation_report
                    
                    print(c("\nGenerating test files...", "96"))
                    count, generated_files = generate_tests(files, verbose=getattr(args, 'verbose', False))
                    
                    use_color = not args.no_color and sys.stdout.isatty()
                    print(format_test_generation_report(count, generated_files, use_color))
                
                # --heatmap: Generate heatmap visualization
                if getattr(args, 'heatmap', None):
                    from .heatmap import generate_heatmap
                    output_path = args.heatmap
                    if not output_path:
                        output_path = "reports/heatmap.html"
                    
                    print(c("\nGenerating repository heatmap...", "96"))
                    success = generate_heatmap(data, output_path)
                    
                    if success and os.path.exists(output_path):
                        print(c(f"✓ Heatmap generated successfully", "92"))
                        print(f"\nOutput:\n  {output_path}\n")
                    else:
                        print(c("✗ Failed to generate heatmap", "91"))
                        exit_code = max(exit_code, 1)
                
                # --auto-commit: Commit changes to Git
                if getattr(args, 'auto_commit', False):
                    from .autocommit import auto_commit, format_auto_commit_report
                    
                    print(c("\nAuto-committing changes...", "96"))
                    success, message = auto_commit(repo_path, verbose=getattr(args, 'verbose', False))
                    
                    use_color = not args.no_color and sys.stdout.isatty()
                    print(format_auto_commit_report(success, message, use_color))
                    
                    if not success:
                        exit_code = max(exit_code, 1)
        
        except KeyboardInterrupt:
            print("\nRepoDoctor: operation cancelled by user.")
            sys.exit(130)
        except Exception as e:
            if getattr(args, 'debug', False):
                import traceback
                traceback.print_exc()
            else:
                print(f"\nRepoDoctor Error: {e}")
            exit_code = max(exit_code, 1)

    
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nRepoDoctor: operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        import sys
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        else:
            print(f"\nRepoDoctor Error: Unexpected error occurred")
            print(f"Run with --debug for more details")
        sys.exit(1)
