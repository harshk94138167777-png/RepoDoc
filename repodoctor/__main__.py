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
    root_path = root_paths[0] if root_paths else '.'
    if not os.path.isdir(root_path):
        print(f"Error: {root_path} is not a directory.")
        sys.exit(2)

    custom_ignores = args.ignore.split(",") if args.ignore else []

    # Determine animation mode (disabled by --no-animation or when not a TTY)
    show_animation = not getattr(args, "no_animation", False)
    use_parallel   = getattr(args, "parallel", False)

    all_reports = []
    
    html_outputs = []
    llm_outputs = []
    exit_code = 0

    for idx, rp in enumerate(root_paths):
        root_path = rp
        if not os.path.isdir(root_path):
            print(f"Error: {root_path} is not a directory.")
            continue
            
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
        # Analysis phases
        # ------------------------------------------------------------------ #
        with Spinner(f"Detecting languages ({root_path})", colour=show_animation):
            detect_languages(files)

        with Spinner(f"Analysing metrics ({root_path})", colour=show_animation):
            analyze_metrics(files)

        with Spinner(f"Scanning TODOs ({root_path})", colour=show_animation):
            todos = scan_todos(files)

        with Spinner(f"Scanning security patterns ({root_path})", colour=show_animation):
            security = scan_security(files)

        with Spinner(f"Detecting duplicates ({root_path})", colour=show_animation):
            duplicates = scan_duplicates(files, args.duplicate_lines)

        with Spinner(f"Checking project structure ({root_path})", colour=show_animation):
            structure = check_project_structure(root_path)

        with Spinner(f"Reading Git info ({root_path})", colour=show_animation):
            git_info = get_git_info(root_path)

        repo_name = os.path.basename(os.path.abspath(root_path)) or "Unknown"

        # AI & Advanced analytics (computed just in time)
        positive_words = {"awesome", "great", "excellent", "amazing", "good", "perfect", "wow", "love", "thanks", "beautiful", "brilliant", "clean", "elegant", "smart"}
        negative_words = {"fuck", "shit", "crap", "bitch", "damn", "hate", "ugly", "stupid", "terrible", "awful", "horrible", "mess", "hack", "fixme", "gross", "disgusting", "wtf"}
        pos_count = sum(1 for f in files if f.metrics for _ in f.metrics.words if _ in positive_words)
        neg_count = sum(1 for f in files if f.metrics for _ in f.metrics.words if _ in negative_words)
        
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
                texts = [(f, " ".join(f.metrics.words)) for f in files if f.metrics and len(f.metrics.words) > 50]
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

        import collections
        all_words = []
        for f in files:
            if f.metrics:
                all_words.extend(f.metrics.words)
        word_counter = collections.Counter(all_words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "if", "then", "else", "while", "for", "def", "class", "return", "import", "from", "print", "self", "None", "True", "False"}
        filtered_words = [w for w in all_words if len(w) > 3 and w not in stop_words]
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

        if score and score.score < getattr(args, "fail_under", 0):
            exit_code = max(exit_code, 1)

        if not args.json:
            use_color = not args.no_color and sys.stdout.isatty()
            exec_time = time.time() - start_time
            print_terminal_report(data, use_color, args.large_file_lines, None, exec_time, args.tree)
            
        if args.html:
            html_outputs.append(generate_html_report(data, args.large_file_lines))
            
        if args.export_prompt:
            prompt_chunk = f"=== REPOSITORY: {repo_name} ===\n\n"
            for file_info in files:
                prompt_chunk += f"--- {file_info.path} ---\n"
                try:
                    with open(file_info.path, "r", encoding="utf-8", errors="ignore") as src:
                        prompt_chunk += src.read() + "\n\n"
                except Exception:
                    prompt_chunk += "[Error reading file contents]\n\n"
            llm_outputs.append(prompt_chunk)

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

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
