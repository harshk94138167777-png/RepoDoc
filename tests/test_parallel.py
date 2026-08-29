"""
test_parallel.py — Feature 3: Parallel scanning tests.

Uses ONLY stdlib: unittest, unittest.mock, os, tempfile.
No third-party dependencies.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from repodoctor.scanner import scan_repository


def _make_fixture(tmp_dir: str, n_files: int = 20) -> None:
    """Create n_files small text files in tmp_dir for testing."""
    for i in range(n_files):
        path = os.path.join(tmp_dir, f"file_{i:04d}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# file {i}\ndef func_{i}():\n    pass\n")


class TestParallelScanning(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        _make_fixture(self._tmp, n_files=30)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ------------------------------------------------------------------ #

    def test_parallel_matches_sequential(self):
        """Parallel and sequential scans must return the same set of files."""
        sequential = scan_repository(self._tmp, parallel=False, show_animation=False)
        parallel   = scan_repository(self._tmp, parallel=True,  show_animation=False)

        seq_paths = sorted(f.path for f in sequential)
        par_paths = sorted(f.path for f in parallel)

        self.assertEqual(seq_paths, par_paths,
                         "Parallel scan returned different file paths than sequential scan")

    def test_parallel_file_count(self):
        """Parallel scan must discover exactly the same number of files."""
        sequential = scan_repository(self._tmp, parallel=False, show_animation=False)
        parallel   = scan_repository(self._tmp, parallel=True,  show_animation=False)
        self.assertEqual(len(sequential), len(parallel))

    def test_threadpool_worker_count(self):
        """ThreadPoolExecutor must be created with min(32, cpu_count+4) workers."""
        captured = {}

        import concurrent.futures as _cf
        original_init = _cf.ThreadPoolExecutor.__init__

        def mock_init(self_inner, max_workers=None, **kwargs):
            captured["max_workers"] = max_workers
            original_init(self_inner, max_workers=max_workers, **kwargs)

        with patch.object(_cf.ThreadPoolExecutor, "__init__", mock_init):
            scan_repository(self._tmp, parallel=True, show_animation=False)

        expected = min(32, (os.cpu_count() or 1) + 4)
        self.assertEqual(captured.get("max_workers"), expected,
                         f"Expected {expected} workers, got {captured.get('max_workers')}")

    def test_results_are_deterministic(self):
        """Running parallel scan 5× on the same fixture must give identical results."""
        runs = [
            sorted(f.path for f in scan_repository(self._tmp, parallel=True, show_animation=False))
            for _ in range(5)
        ]
        for i in range(1, 5):
            self.assertEqual(runs[0], runs[i],
                             f"Run {i} produced different results than run 0 (non-deterministic)")

    def test_sequential_unchanged_for_empty_dir(self):
        """Empty directory must return empty list in both modes."""
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(scan_repository(empty, parallel=False, show_animation=False), [])
            self.assertEqual(scan_repository(empty, parallel=True,  show_animation=False), [])


if __name__ == "__main__":
    unittest.main()
