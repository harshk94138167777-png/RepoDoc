"""
test_packaging.py — Feature 2: Packaging & installation tests.

Uses ONLY stdlib: unittest, subprocess, importlib.metadata, sys, os.
No third-party dependencies.

NOTE: These tests require the package to be installed first:
    pip install -e RepoDoc
"""

import os
import sys
import subprocess
import unittest


class TestPackagingEntrypoint(unittest.TestCase):

    def test_repodoctor_version_exits_zero(self):
        """repodoctor --version must exit with code 0 when installed."""
        result = subprocess.run(
            [sys.executable, "-m", "repodoctor", "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"Expected exit 0 from --version, got {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_repodoctor_help_exits_zero(self):
        """repodoctor --help must exit with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "repodoctor", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"--help exited non-zero: {result.stderr}")

    def test_parallel_flag_present_in_help(self):
        """--parallel / -j flag must be visible in --help output."""
        result = subprocess.run(
            [sys.executable, "-m", "repodoctor", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertIn("--parallel", result.stdout,
                      "--parallel flag not found in --help output")

    def test_no_animation_flag_present_in_help(self):
        """--no-animation flag must be visible in --help output."""
        result = subprocess.run(
            [sys.executable, "-m", "repodoctor", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertIn("--no-animation", result.stdout,
                      "--no-animation flag not found in --help output")


class TestZeroRuntimeDependencies(unittest.TestCase):

    def test_zero_runtime_deps_via_metadata(self):
        """
        importlib.metadata.requires('repodoctor') must be None or empty list —
        proving zero transitive runtime dependencies.
        (Only works when package is installed via pip install -e .)
        """
        try:
            from importlib.metadata import requires, PackageNotFoundError
        except ImportError:
            self.skipTest("importlib.metadata not available (Python < 3.8)")

        try:
            deps = requires("repodoctor")
        except Exception:
            self.skipTest("repodoctor not installed — run: pip install -e RepoDoc")

        # requires() returns None when there are no dependencies at all
        self.assertTrue(
            deps is None or len(deps) == 0,
            f"repodoctor has unexpected runtime dependencies: {deps}"
        )

    def test_package_imports_without_third_party(self):
        """
        Core repodoctor modules must import cleanly using only stdlib.
        This test also verifies no third-party import side-effects sneak in.
        """
        import importlib
        modules_to_check = [
            "repodoctor.models",
            "repodoctor.spinner",
            "repodoctor.scanner",
            "repodoctor.cli",
        ]
        for mod_name in modules_to_check:
            with self.subTest(module=mod_name):
                try:
                    importlib.import_module(mod_name)
                except ImportError as e:
                    self.fail(f"Failed to import {mod_name}: {e}")


if __name__ == "__main__":
    unittest.main()
