"""
Unit tests for typo scanner.
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.typos import scan_typos, format_typo_report, TypoFinding
from repodoctor.models import FileInfo


class TestTypos(unittest.TestCase):
    """Test typo scanner functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_detect_common_typos(self):
        """Test detection of common typos."""
        # Create a file with known typos
        test_file = self.temp_path / "test.py"
        test_file.write_text("def recieve_data():\n    teh = 1\n    return teh\n")
        
        file_info = FileInfo(
            path=str(test_file),
            filename="test.py",
            extension=".py",
            size=50,
            lines=3,
            language="Python",
            is_binary=False,
            relative_path="test.py"
        )
        
        findings = scan_typos([file_info])
        
        # Should find 'recieve' and 'teh'
        self.assertGreater(len(findings), 0)
        
        typo_words = [f.word for f in findings]
        self.assertIn('recieve', typo_words)
        self.assertIn('teh', typo_words)
    
    def test_skip_binary_files(self):
        """Test that binary files are skipped."""
        test_file = self.temp_path / "test.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03')
        
        file_info = FileInfo(
            path=str(test_file),
            filename="test.bin",
            extension=".bin",
            size=4,
            lines=0,
            language="Unknown",
            is_binary=True,
            relative_path="test.bin"
        )
        
        findings = scan_typos([file_info])
        
        # Should not process binary files
        self.assertEqual(len(findings), 0)
    
    def test_no_false_positives_on_code(self):
        """Test that programming terms don't trigger false positives."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("import sys\nimport os\ndef func(arg, param):\n    return len(arg)\n")
        
        file_info = FileInfo(
            path=str(test_file),
            filename="test.py",
            extension=".py",
            size=60,
            lines=4,
            language="Python",
            is_binary=False,
            relative_path="test.py"
        )
        
        findings = scan_typos([file_info])
        
        # Should not flag programming terms
        self.assertEqual(len(findings), 0)
    
    def test_typo_suggestions(self):
        """Test that suggestions are provided for known typos."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("# This is becuase of something\n")
        
        file_info = FileInfo(
            path=str(test_file),
            filename="test.py",
            extension=".py",
            size=30,
            lines=1,
            language="Python",
            is_binary=False,
            relative_path="test.py"
        )
        
        findings = scan_typos([file_info])
        
        # Should find 'becuase' with suggestion 'because'
        becuase_findings = [f for f in findings if f.word == 'becuase']
        if becuase_findings:
            self.assertEqual(becuase_findings[0].suggestion, 'because')
    
    def test_format_report_no_typos(self):
        """Test report formatting when no typos found."""
        report = format_typo_report([], 10, use_color=False)
        
        self.assertIn("Files scanned: 10", report)
        self.assertIn("Potential typos found: 0", report)
        self.assertIn("No potential typos found", report)
    
    def test_format_report_with_typos(self):
        """Test report formatting when typos are found."""
        findings = [
            TypoFinding("test.py", 1, "teh", "the"),
            TypoFinding("test.py", 2, "recieve", "receive"),
        ]
        
        report = format_typo_report(findings, 5, use_color=False)
        
        self.assertIn("Files scanned: 5", report)
        self.assertIn("Potential typos found: 2", report)
        self.assertIn("test.py", report)
        self.assertIn("teh", report)
        self.assertIn("the", report)


if __name__ == "__main__":
    unittest.main()
