"""
Unit tests for heatmap generation.
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.heatmap import generate_heatmap
from repodoctor.models import ReportData, FileInfo, FileMetrics, HealthScore


class TestHeatmap(unittest.TestCase):
    """Test heatmap visualization generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name) / "heatmap.html"
        
        # Create test data with files
        test_files = []
        for i in range(10):
            metrics = FileMetrics(
                code_lines=50 + i * 10,
                comment_lines=5,
                blank_lines=5,
                longest_line=80,
                num_functions=i + 1,
                num_classes=1 if i % 2 == 0 else 0,
                max_nesting=i % 5
            )
            
            file_info = FileInfo(
                path=f"/test/repo/file{i}.py",
                filename=f"file{i}.py",
                extension=".py",
                size=1000 + i * 100,
                lines=60 + i * 10,
                language="Python",
                is_binary=False,
                relative_path=f"file{i}.py"
            )
            file_info.metrics = metrics
            test_files.append(file_info)
        
        self.test_data = ReportData(
            path="/test/repo",
            name="TestRepo",
            files=test_files,
            todos=[],
            security=[],
            duplicates=[],
            structure={},
            git={},
            score=HealthScore(score=75, breakdown={})
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_heatmap_creation(self):
        """Test that heatmap file is created."""
        result = generate_heatmap(self.test_data, str(self.output_path))
        self.assertTrue(result)
        self.assertTrue(self.output_path.exists())
    
    def test_heatmap_is_valid_html(self):
        """Test that generated heatmap is valid HTML."""
        generate_heatmap(self.test_data, str(self.output_path))
        
        content = self.output_path.read_text()
        
        # Check for HTML structure
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
        self.assertIn('<head>', content)
        self.assertIn('<body>', content)
    
    def test_heatmap_contains_title(self):
        """Test that heatmap contains repository information."""
        generate_heatmap(self.test_data, str(self.output_path))
        
        content = self.output_path.read_text()
        
        self.assertIn('TestRepo', content)
        self.assertIn('Heatmap', content)
    
    def test_heatmap_contains_grid(self):
        """Test that heatmap contains visualization grid."""
        generate_heatmap(self.test_data, str(self.output_path))
        
        content = self.output_path.read_text()
        
        # Should have grid container
        self.assertIn('grid', content.lower())
        
        # Should have cell elements
        self.assertIn('cell', content.lower())
    
    def test_heatmap_with_no_files(self):
        """Test heatmap generation with empty file list."""
        empty_data = ReportData(
            path="/test/repo",
            name="EmptyRepo",
            files=[],
            todos=[],
            security=[],
            duplicates=[],
            structure={},
            git={},
            score=HealthScore(score=100, breakdown={})
        )
        
        result = generate_heatmap(empty_data, str(self.output_path))
        
        # Should handle empty data gracefully
        self.assertFalse(result)
    
    def test_heatmap_contains_statistics(self):
        """Test that heatmap includes repository statistics."""
        generate_heatmap(self.test_data, str(self.output_path))
        
        content = self.output_path.read_text()
        
        # Should show total files
        self.assertIn('Total Files', content)
        
        # Should show health score
        self.assertIn('75', content)  # The score value


if __name__ == "__main__":
    unittest.main()
