# RepoDoctor

> RepoDoctor diagnoses a codebase for maintainability, security, duplication, project-structure and Git issues using only the language standard library.

## Problem
Modern development tools rely on heavy dependency chains that are hard to audit, difficult to install in restricted environments, and prone to breaking changes.

## Solution
RepoDoctor is a production-quality CLI tool that analyzes a software repository and provides an actionable health, security, and maintainability report without a single third-party runtime dependency.

## Features
- **Zero Runtime Dependencies**: Built entirely with Python's standard library.
- **Repository Scanning**: Fast filesystem traversal with configurable ignores.
- **Security Scanner**: Detects exposed API keys, credentials, and `.env` files using robust heuristics and automatically redact findings.
- **Maintainability Metrics**: Identifies complex code, huge files, excessive nesting, and counts lines and functions.
- **Duplicate Code Detection**: Finds duplicated logical blocks across the codebase using rolling hashes.
- **Project Structure Validation**: Enforces standard repository practices (README, tests, gitignore, CI config).
- **Git Integration**: Leverages native Git to report branch, commit counts, and uncommitted changes.
- **Rich Terminal Output**: ANSI-colored reporting without external rendering packages like Rich or Colorama.
- **JSON Output**: Machine-readable output via `--json`.

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
| `--no-color` | Disable ANSI color output |
| `--ignore` | Comma-separated list of custom directories to ignore |
| `--large-file-lines` | Threshold for large file lines (default: 500) |
| `--duplicate-lines` | Minimum lines for duplicate detection (default: 8) |
| `--security` | Focus only on security analysis (WIP) |
| `--todos` | Focus only on TODO/FIXME analysis (WIP) |
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
