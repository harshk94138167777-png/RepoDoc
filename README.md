# RepoDoctor

> RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure and Git issues using only the language standard library.

## Problem
Modern development tools rely on heavy dependency chains that are hard to audit, difficult to install in restricted environments, and prone to breaking changes.

## Solution
RepoDoctor is a production-quality CLI tool that analyzes a software repository and provides an actionable health, security, and maintainability report without a single third-party runtime dependency.


## 🚀 Installation

You can install RepoDoctor globally on any OS directly from PyPI:

```bash
pip install repodoctor-cli
```

Once installed, simply navigate to any repository and run:
```bash
repodoctor .
```



## 🧠 What's New in v4.0.0 (The Ultimate Intelligence Update)
- **Live Web Dashboard (`--serve`)**: Instantly spins up a local web server on `localhost:8080` to view your repository health in a gorgeous browser UI.
- **Interactive TUI (`--interactive`)**: A blazing fast, fully navigable terminal dashboard. Use your arrow keys to explore your repository's health natively!
- **Auto-Documentation (`--docs`)**: Parses every function and class across your project to automatically generate a `docs/api_reference.md` file.
- **The Blame Game (`--blame`)**: Runs a `git blame` on every Code Smell, Duplicate Block, and Security Flaw to name the exact developer who wrote it!
- **God Function Profiler**: Mathematically calculates cyclomatic complexity to crown the single most confusing block of code in your project as the "🧟‍♂️ God Function."
- **Git Time Machine (`--time-machine`)**: Run RepoDoctor across your last 10 commits to generate a historical ASCII timeline of your codebase health.
- **Live AI Code Review (`--ai-review`)**: Connects natively to OpenAI or Gemini APIs to provide human-readable refactoring advice for your worst files directly in the terminal.
- **Dead Code Eliminator**: Scans for variables and functions that are declared but never actually used anywhere in your project.
- **Legal & Compliance Scanner (`--legal`)**: Parses `package.json` and `LICENSE` files to warn you of dangerous GPL/Copyleft licenses.
- **Cloud/DevOps Security**: Deep scans `Dockerfile` and `docker-compose.yml` to prevent running containers as `root` and exposing dangerous ports.

## 🔥 What's New in v2.0 (The Enterprise Upgrade)
- **Auto-Fix Engine (`--fix`)**: Automatically rewrites code to fix safe smells (trailing whitespace, missing EOF newlines, missing JS `use strict`).
- **ASCII Dependency Graph (`--graph`)**: Generates a beautiful ASCII tree showing exactly how your Python and JavaScript files import each other.
- **GitHub Actions CI/CD (`--init-ci`)**: Instantly generates a `.github/workflows/repodoctor.yml` pipeline to block bad Pull Requests.
- **Bus Factor Analyzer**: Analyzes Git history to flag critical files that are only understood by a single developer.
- **Deep-Scan Security**: Advanced credential detection for AWS Keys, Stripe Secrets, GitHub PATs, Slack Tokens, and Discord Webhooks.
- **Native Config Files**: Configure RepoDoctor directly in `repodoctor.json` or `pyproject.toml` so you never have to type flags again.


## Features
- **Multi-Threaded Parallel Scanning**: Asynchronously processes massive codebases in milliseconds.\n- **Animated Terminal UI**: Beautiful typewriter animations and progress spinners.\n- **Multi-Repository Aggregation**: Scan multiple codebases simultaneously and generate unified or independent reports across all flags (HTML, JSON, LLM prompt).\n- **Zero Runtime Dependencies**: Built entirely with Python's standard library.
- **Single-File Portability**: Can be compiled into a single `repodoctor_single.py` script for extreme portability.
- **Developer Mood Analyzer**: Scans code comments and commit messages to calculate the emotional state of the project team.
- **Code Clone Exposer**: Mathematically cross-references all files to expose the two most identical copy-pasted files in the project.
- **Micro-Linter Engine**: Instantly flags 30+ code smells including profanity filters, wildcard imports, massive JSON configs, and missing alt-text.
- **LLM Prompt Exporter**: Instantly bundle your entire codebase into a single text file ready for ChatGPT/Claude (`--export-prompt`).
- **SVG Badge Generator**: Generate valid GitHub-style SVG health badges without image processing libraries (`--badge`).
- **Terminal ASCII Tree & Bar Charts**: Visual breakdown of your project's folders (`--tree`) and languages natively in your terminal.
- **AST Cyclomatic Complexity**: Parses Python Abstract Syntax Trees mathematically to score code logic complexity.
- **Security Scanner**: Detects exposed API keys, credentials, and `.env` files and automatically redacts findings.
- **Git Analytics & Hotspots**: Leverages native Git to report top contributors, uncommitted changes, and your most frequently edited file (Hotspot).
- **Codebase Vocabulary Cloud**: Automatically extracts the most frequently used variable and function names across all your files.
- **Rich Output Formats**: Choose between Animated ANSI-colored terminal, HTML (`--html`), or JSON (`--json`).
- **Baseline Tracking**: Compare current scans against past reports (`--baseline`) to track regressions over time.

## Architecture
Modular Python architecture utilizing built-in `argparse`, `subprocess`, `ast`, and `unittest`. Data structures rely on `dataclasses`.

## Installation
No dependencies are required. Clone the repository or copy the `repodoctor` folder:

```bash
git clone https://github.com/example/repodoctor.git
```

## Usage
Run the package directory against your target repository:

```bash
python -m repodoctor /path/to/your/repo
```

### CLI Options

| Flag | Description |
|---|---|
| `path` | Path to the repository (default: `.`) |
| `--json` | Output valid machine-readable JSON |
| `--html FILE` | Output a self-contained HTML dashboard report |
| `--export-prompt FILE`| Export the codebase into a single text file for LLM prompting |
| `--badge FILE` | Generate a GitHub-style SVG health badge |
| `--tree` | Print an ASCII project directory tree at the top of the report |
| `--baseline FILE` | Path to a previous JSON report to calculate delta trends |
| `--no-color` | Disable animated ANSI color output |
| `--ignore` | Comma-separated list of custom directories to ignore |
| `--large-file-lines` | Threshold for large file lines (default: 500) |
| `--duplicate-lines` | Minimum lines for duplicate detection (default: 8) |
| `--security` | Focus only on security analysis |
| `--todos` | Focus only on TODO/FIXME analysis |
| `--git` | Include Git analysis (Always attempts by default) |
| `--verbose` | Enable verbose logging |
| `--version` | Display version |
| `--help` | Display help |

### Exit Codes
- `0`: Successful scan, no serious findings (secrets or duplicates).
- `1`: Successful scan with findings.
- `2`: Invalid CLI usage.

## JSON Format
Use the `--json` flag to export data.
```json
{
  "repository": { "path": ".", "name": "project" },
  "summary": { "files": 247, "lines": 38421, "health_score": 78 },
  "security": { "potential_secrets": 0, "findings": [] },
  "maintainability": { "large_files": 0, "todos": 5, "duplicates": 0 },
  "git": { "available": true, "branch": "main", "commits": 142, "uncommitted_changes": 0 },
  "structure": { "README": "PASS", "Tests": "PASS" }
}
```

## Performance
- Uses efficient filesystem walking (`os.walk`).
- Early bailing on binary files.
- Rolling window chunking for O(N) deduplication analysis.

## Security Model
- **Local Only**: No data is uploaded or transmitted.
- **Redacted Output**: Secrets are never dumped fully in terminal or JSON.
- **No Evaluation**: Source code is parsed statically (via AST/Regex), never executed.
- **Safe Execution**: Git commands strictly avoid shell interpolation to prevent injection.

## Limitations
- Language detection is extension-based.
- Duplicate detection is line-based rather than AST-based.
- Security scanner may yield false positives; human review is required.

## Zero-Dependency Proof
To verify, run within a fully clean virtual environment:
```bash
python -m venv /tmp/repodoctor-test
source /tmp/repodoctor-test/bin/activate
pip freeze # (Will be empty)
python -m repodoctor /path/to/repo1 /path/to/repo2
```

## Standard Library Substitutions
See [STDLIB.md](STDLIB.md) for details on how we substituted common third-party tools.

## Testing
Tested with Python `unittest`:
```bash
python -m unittest discover -s tests -v
```

## Hackathon Information
Built for the **Zero Dependency | 72-Hour Hackathon**.

## License
MIT
