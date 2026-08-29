# RepoDoctor

> RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure, and Git issues using only the Python standard library.

RepoDoctor is a production-quality CLI tool that analyzes software repositories and provides actionable health, security, and maintainability reports without a single third-party runtime dependency. 

## Key Features

- **Multi-Repository Scanning**: Scan multiple codebases simultaneously and generate unified or independent reports.
- **Zero Runtime Dependencies**: Built entirely with Python's standard library. Portable and fast.
- **Advanced Static Analysis**: Includes AST Cyclomatic Complexity, Developer Mood Analyzer, Code Clone Exposer, and a Micro-Linter Engine.
- **Security Scanner**: Detects exposed API keys, credentials, and `.env` files with automatic redaction.
- **Rich Output Formats**: Animated ANSI-colored terminal, fully offline HTML dashboards (`--html`), or JSON (`--json`).

---

## Installation

No dependencies are required. Clone the repository and run it directly:

```bash
git clone https://github.com/example/repodoctor.git
```

## Quick Start & Usage

Run the package against your target repository (or multiple repositories):

```bash
# Basic scan of a single repository
python -m repodoctor /path/to/your/repo

# Generate a self-contained HTML dashboard
python -m repodoctor /path/to/repo --html report.html

# Multi-repository scanning (aggregate metrics across multiple projects)
python -m repodoctor /path/to/backend /path/to/frontend

```

### Essential CLI Options

| Flag | Description |
|---|---|
| `path` | Path to the repository/repositories (default: `.`) |
| `--html FILE` | Output a standalone HTML dashboard report |
| `--json` | Output machine-readable JSON for CI/CD pipelines |
| `--export-prompt`| Export the entire codebase into a single text file for LLMs |
| `--parallel` | Enable multi-threaded scanning for massive codebases |
| `--tree` | Print an ASCII project directory tree in the terminal |
| `--badge FILE` | Generate a GitHub-style SVG health badge |
| `--security` | Focus exclusively on security and credential analysis |

---

## Architecture

RepoDoctor is built on a highly modular, zero-dependency Python architecture leveraging the standard library for maximum portability.

- **`__main__.py`**: CLI entry point and pipeline orchestration.
- **`scanner.py`**: Parallel execution engine utilizing `ThreadPoolExecutor` for asynchronous, I/O-bound filesystem traversal.
- **`analyzer.py`**: Static analysis core. Utilizes the built-in `ast` module for complexity scoring, rolling-window algorithms for duplication detection, and regex patterns for code smells.
- **`security.py`**: Credential scanner using regex-based pattern matching and confidence scoring.
- **`git_utils.py`**: Safely orchestrates `subprocess` calls to the local Git binary for hotspot and contributor analytics.
- **`report.py`**: Presentation layer for ANSI terminal UI, JSON, HTML templates, and SVG badges.

## Exit Codes

Designed for CI/CD integration:
- `0`: Successful scan, no serious findings (secrets or duplicates).
- `1`: Successful scan with findings (requires attention).
- `2`: Invalid CLI usage.

## License

MIT
