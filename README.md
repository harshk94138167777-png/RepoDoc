# RepoDoctor

> RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure and Git issues using only the language standard library.

## Problem
Modern development tools rely on heavy dependency chains that are hard to audit, difficult to install in restricted environments, and prone to breaking changes.

## Solution
RepoDoctor is a production-quality CLI tool that analyzes a software repository and provides an actionable health, security, and maintainability report without a single third-party runtime dependency.

## Features
- **Zero Runtime Dependencies**: Built entirely with Python's standard library.
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
python -m repodoctor .
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
