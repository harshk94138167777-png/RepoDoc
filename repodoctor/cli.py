import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repodoctor",
        description="RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure and Git issues using only the language standard library.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "path",
        help="Path to the repository to analyze",
        default=["."],
        nargs="*"
    )
    parser.add_argument("--json", action="store_true", help="Output valid machine-readable JSON")
    parser.add_argument("--html", type=str, help="Output a self-contained HTML report to the specified file", default="")
    parser.add_argument("--baseline", type=str, help="Path to a previous JSON report to compare against", default="")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    parser.add_argument("--badge", type=str, metavar="FILE", help="Generate an SVG health badge", default="")
    parser.add_argument("--tree", action="store_true", help="Print an ASCII project tree")
    parser.add_argument("--export-prompt", type=str, metavar="FILE", help="Export the codebase into a single text file for LLM prompting", default="")
    parser.add_argument("--ignore", type=str, help="Comma-separated list of custom directories to ignore", default="")
    parser.add_argument("--large-file-lines", type=int, help="Threshold for large file lines", default=500)
    parser.add_argument("--duplicate-lines", type=int, help="Minimum lines for duplicate detection", default=8)
    parser.add_argument("--security", action="store_true", help="Focus only on security analysis")
    parser.add_argument("--todos", action="store_true", help="Focus only on TODO/FIXME analysis")
    parser.add_argument("--git", action="store_true", help="Include Git analysis")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--parallel", "-j",
        action="store_true",
        help="Enable parallel file scanning using concurrent.futures.ThreadPoolExecutor (faster on large repos)"
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable live CLI spinner / progress bar animation"
    )
    parser.add_argument("--init-ci", action="store_true", help="Generate GitHub Actions CI/CD pipeline")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe code smells and formatting issues")
    parser.add_argument("--graph", action="store_true", help="Generate an ASCII dependency graph")
    
    # New feature flags
    parser.add_argument("--slides", type=str, metavar="FILE", help="Generate PowerPoint presentation with repository analysis", default="")
    parser.add_argument("--play", type=str, metavar="FILE", help="Open and view a generated report file", default="")
    parser.add_argument("--schema", type=str, metavar="FILE", help="Generate JSON schema describing repository structure", default="")
    parser.add_argument("--test", action="store_true", help="Generate Python unittest test files from source code")
    parser.add_argument("--typo", action="store_true", help="Scan for potential typos in code and documentation")
    parser.add_argument("--heatmap", type=str, metavar="FILE", help="Generate HTML/SVG heatmap visualization", default="")
    parser.add_argument("--auto-commit", action="store_true", help="Automatically commit RepoDoctor changes to Git")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed error tracebacks")

    try:
        from importlib.metadata import version
        __version__ = version("repodoctor-cli")
    except Exception:
        __version__ = "unknown"

    parser.add_argument("--ai-review", action="store_true", help="Get live AI code review")
    parser.add_argument("--time-machine", action="store_true", help="Run Git Time Machine analytics")
    parser.add_argument("--serve", action="store_true", help="Host live web dashboard on localhost:8080")
    parser.add_argument("--blame", action="store_true", help="Run git blame on code smells")
    parser.add_argument("--docs", action="store_true", help="Generate API documentation")
    parser.add_argument("--legal", action="store_true", help="Scan for legal and license risks")
    parser.add_argument("--interactive", action="store_true", help="Launch Interactive TUI")
    
    parser.add_argument("--speak", action="store_true", help="Audio Announcer")
    parser.add_argument("--forecast", action="store_true", help="Predictive Bug Forecasting")
    parser.add_argument("--gamify", action="store_true", help="RPG Leaderboard")
    parser.add_argument("--plagiarism", action="store_true", help="StackOverflow Detector")
    parser.add_argument("--chaos", action="store_true", help="Chaos Monkey CI Tester")
    parser.add_argument("--architecture", action="store_true", help="Auto-Architecture Generation")
    parser.add_argument("--rage", action="store_true", help="The Rage Quit Metric")
    parser.add_argument("--watch", action="store_true", help="Self-Healing Daemon")
    parser.add_argument("--auto-commit", action="store_true", help="Auto-Commit AI")
    parser.add_argument("--heatmap", action="store_true", help="ASCII Directory Heatmap")
    parser.add_argument("--p2p", action="store_true", help="P2P Report Sharing")
    parser.add_argument("--typosquat", action="store_true", help="Typo-Squatting Scanner")
    parser.add_argument("--gen-tests", action="store_true", help="Auto Unit Test Generator")
    parser.add_argument("--explain-regex", action="store_true", help="Regex Explainer")
    parser.add_argument("--schema", action="store_true", help="Database Schema Analyzer")
    parser.add_argument("--slides", action="store_true", help="Auto-Presentation Generator")
    parser.add_argument("--play", action="store_true", help="The Bug-Hunter RPG")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    return parser

def parse_args(args=None):
    parser = build_parser()
    return parser.parse_args(args)
