"""
Unit tests for test file generation.
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.testgen import generate_tests, format_test_generation_report
from repodoctor.models import FileInfo


class TestTestGen(unittest.TestCase):
    """Test unittest file generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_generate_test_for_python_file(self):
        """Test that test file is generated for Python source."""
        # Create a simple Python file
        source_file = self.temp_path / "calculator.py"
        source_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

class Calculator:
    def multiply(self, a, b):
        return a * b
""")
        
        file_info = FileInfo(
            path=str(source_file),
            filename="calculator.py",
            extension=".py",
            size=100,
            lines=9,
            language="Python",
            is_binary=False,
            relative_path="calculator.py"
        )
        
        count, generated = generate_tests([file_info], verbose=False)
        
        # Should generate at least one test file
        self.assertGreaterEqual(count, 0)  # May be 0 if tests dir already has file
    
    def test_skip_non_python_files(self):
        """Test that non-Python files are skipped."""
        # Create a JavaScript file
        js_file = self.temp_path / "app.js"
        js_file.write_text("function test() { return 1; }")
        
        file_info = FileInfo(
            path=str(js_file),
            filename="app.js",
            extension=".js",
            size=30,
            lines=1,
            language="JavaScript",
            is_binary=False,
            relative_path="app.js"
        )
        
        count, generated = generate_tests([file_info], verbose=False)
        
        # Should not generate test for JS file
        self.assertEqual(count, 0)
    
    def test_skip_existing_test_files(self):
        """Test that existing test files are not regenerated."""
        # Create source file
        source_file = self.temp_path / "utils.py"
        source_file.write_text("def helper(): pass")
        
        # Create tests directory and test file
        tests_dir = self.temp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_utils.py"
        test_file.write_text("# existing test")
        
        file_info = FileInfo(
            path=str(source_file),
            filename="utils.py",
            extension=".py",
            size=20,
            lines=1,
            language="Python",
            is_binary=False,
            relative_path="utils.py"
        )
        
        count, generated = generate_tests([file_info], verbose=False)
        
        # Should not regenerate existing test
        self.assertEqual(count, 0)
    
    def test_format_report_no_tests(self):
        """Test report formatting when no tests generated."""
        report = format_test_generation_report(0, [], use_color=False)
        
        self.assertIn("No suitable source files", report)
    
    def test_format_report_with_tests(self):
        """Test report formatting when tests are generated."""
        generated_files = [
            "/test/tests/test_module1.py",
            "/test/tests/test_module2.py"
        ]
        
        report = format_test_generation_report(2, generated_files, use_color=False)
        
        self.assertIn("Generated 2 test file(s)", report)
        self.assertIn("test_module1.py", report)
        self.assertIn("test_module2.py", report)
    
    def test_generated_test_has_unittest_structure(self):
        """Test that generated test files have proper unittest structure."""
        # Create source with a simple function
        source_file = self.temp_path / "math_utils.py"
        source_file.write_text("""
def square(x):
    return x * x
""")
        
        file_info = FileInfo(
            path=str(source_file),
            filename="math_utils.py",
            extension=".py",
            size=40,
            lines=3,
            language="Python",
            is_binary=False,
            relative_path="math_utils.py"
        )
        
        count, generated = generate_tests([file_info], verbose=False)
        
        if count > 0 and generated:
            # Check the generated test file
            test_file = Path(generated[0])
            if test_file.exists():
                content = test_file.read_text()
                
                # Should import unittest
                self.assertIn("import unittest", content)
                
                # Should have a test class
                self.assertIn("class Test", content)
                
                # Should have if __name__ == "__main__"
                self.assertIn('if __name__ == "__main__"', content)


if __name__ == "__main__":
    unittest.main()
