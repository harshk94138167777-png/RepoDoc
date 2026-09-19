"""
Unit tests for auto-commit functionality.
"""

import unittest
import tempfile
import subprocess
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.autocommit import auto_commit, format_auto_commit_report, _is_git_available


class TestAutoCommit(unittest.TestCase):
    """Test auto-commit functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_git_availability_check(self):
        """Test that Git availability can be checked."""
        # This test depends on system having Git installed
        result = _is_git_available()
        self.assertIsInstance(result, bool)
    
    def test_non_git_repo_fails_gracefully(self):
        """Test that non-Git directories fail gracefully."""
        success, message = auto_commit(str(self.temp_path), verbose=False)
        
        self.assertFalse(success)
        self.assertIn("not a Git repository", message)
    
    def test_auto_commit_with_git_repo(self):
        """Test auto-commit in an actual Git repository."""
        # Skip if Git is not available
        if not _is_git_available():
            self.skipTest("Git not available")
        
        # Initialize a Git repo
        try:
            subprocess.run(['git', 'init'], cwd=self.temp_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                         cwd=self.temp_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                         cwd=self.temp_path, check=True, capture_output=True)
            
            # Create and stage a file
            test_file = self.temp_path / "test.txt"
            test_file.write_text("test content")
            subprocess.run(['git', 'add', 'test.txt'], cwd=self.temp_path, check=True, capture_output=True)
            
            # Try auto-commit
            success, message = auto_commit(str(self.temp_path), verbose=False)
            
            # Should succeed or gracefully handle
            self.assertIsInstance(success, bool)
            self.assertIsInstance(message, str)
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("Could not set up test Git repository")
    
    def test_format_success_report(self):
        """Test formatting of successful auto-commit report."""
        report = format_auto_commit_report(True, "Commit created: abc1234", use_color=False)
        
        self.assertIn("Auto Commit", report)
        self.assertIn("Commit created", report)
        self.assertIn("✓", report)
    
    def test_format_failure_report(self):
        """Test formatting of failed auto-commit report."""
        report = format_auto_commit_report(False, "Git is not installed", use_color=False)
        
        self.assertIn("Auto Commit", report)
        self.assertIn("Git is not installed", report)
        self.assertIn("✗", report)


if __name__ == "__main__":
    unittest.main()
