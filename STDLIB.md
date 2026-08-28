# STDLIB.md

RepoDoctor relies solely on Python's standard library to maintain a zero third-party dependency footprint. Here are the meaningful substitutions made to replace common developer-tool packages:

Normally: requests
Instead: urllib / http.client (Not implemented as RepoDoctor operates completely locally)
Why: RepoDoctor does not require network access.

Normally: Click/Typer
Instead: argparse
Why: standard-library CLI parsing is sufficient for RepoDoctor's argument needs.

Normally: Rich
Instead: sys.stdout + ANSI escapes
Why: terminal rendering for the report is simple enough to implement directly with standard output.

Normally: GitPython
Instead: subprocess + git CLI
Why: Git metadata can be extracted securely by running lightweight subprocess commands without a heavy wrapper package.

Normally: pytest
Instead: unittest
Why: standard-library testing is sufficient to cover our suite without requiring external installation.

Normally: watchdog
Instead: explicit scans
Why: RepoDoctor runs point-in-time diagnostics; a daemon file watcher is unnecessary.

Normally: tabulate
Instead: custom formatter in report.py
Why: reports need only simple fixed-width layouts that are trivial to align with f-strings.

Normally: Pydantic
Instead: dataclasses + manual validation
Why: the internal data model is small, rendering Pydantic overkill.

Normally: python-magic
Instead: lightweight heuristic checking for null bytes
Why: full MIME detection is unnecessary to distinguish text from binary source files.

Normally: colorama
Instead: direct ANSI sequences + `sys.stdout.isatty()` checking
Why: cross-platform support for basic color rendering has improved, and gracefully falling back to plain text satisfies the requirement.
