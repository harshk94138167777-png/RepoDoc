"""
Unit tests for PowerPoint slide generation.
"""

import unittest
import tempfile
import zipfile
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.slides import create_pptx
from repodoctor.models import ReportData, HealthScore


class TestSlides(unittest.TestCase):
    """Test PowerPoint generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name) / "test_report.pptx"
        
        # Create minimal test data
        self.test_data = ReportData(
            path="/test/repo",
            name="TestRepo",
            files=[],
            todos=[],
            security=[],
            duplicates=[],
            structure={'README': 'PASS', 'Tests': 'PASS'},
            git={'available': True, 'branch': 'main'},
            score=HealthScore(score=85, breakdown={})
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_pptx_creation(self):
        """Test that PowerPoint file is created."""
        result = create_pptx(str(self.output_path), self.test_data)
        self.assertTrue(result)
        self.assertTrue(self.output_path.exists())
    
    def test_pptx_is_valid_zip(self):
        """Test that generated PPTX is a valid ZIP file."""
        create_pptx(str(self.output_path), self.test_data)
        
        # PPTX files are ZIP archives
        self.assertTrue(zipfile.is_zipfile(str(self.output_path)))
    
    def test_pptx_contains_required_files(self):
        """Test that PPTX contains required OOXML structure."""
        create_pptx(str(self.output_path), self.test_data)
        
        with zipfile.ZipFile(str(self.output_path), 'r') as pptx:
            files = pptx.namelist()
            
            # Check for required files
            self.assertIn('[Content_Types].xml', files)
            self.assertIn('_rels/.rels', files)
            self.assertIn('ppt/presentation.xml', files)
            self.assertIn('ppt/_rels/presentation.xml.rels', files)
            
            # Check for at least one slide
            slide_files = [f for f in files if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            self.assertGreater(len(slide_files), 0)
    
    def test_pptx_with_invalid_path(self):
        """Test handling of invalid output path."""
        invalid_path = "/invalid/path/that/does/not/exist/report.pptx"
        # Should not raise exception, just return False
        result = create_pptx(invalid_path, self.test_data)
        # This may succeed if parent dir creation works, or fail gracefully
        # Either way, no exception should be raised
        self.assertIsInstance(result, bool)
    
    def test_pptx_has_multiple_slides(self):
        """Test that multiple slides are generated."""
        create_pptx(str(self.output_path), self.test_data)
        
        with zipfile.ZipFile(str(self.output_path), 'r') as pptx:
            files = pptx.namelist()
            slide_files = [f for f in files if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            
            # Should have at least 5 slides (title, overview, stats, etc.)
            self.assertGreaterEqual(len(slide_files), 5)


if __name__ == "__main__":
    unittest.main()
