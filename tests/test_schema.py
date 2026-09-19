"""
Unit tests for schema generation.
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from repodoctor.schema import generate_schema
from repodoctor.models import ReportData, FileInfo, HealthScore


class TestSchema(unittest.TestCase):
    """Test JSON schema generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name) / "schema.json"
        
        # Create test data with files
        test_files = [
            FileInfo(
                path="/test/repo/main.py",
                filename="main.py",
                extension=".py",
                size=1000,
                lines=50,
                language="Python",
                is_binary=False,
                relative_path="main.py"
            ),
            FileInfo(
                path="/test/repo/utils.py",
                filename="utils.py",
                extension=".py",
                size=500,
                lines=25,
                language="Python",
                is_binary=False,
                relative_path="utils.py"
            ),
        ]
        
        self.test_data = ReportData(
            path="/test/repo",
            name="TestRepo",
            files=test_files,
            todos=[],
            security=[],
            duplicates=[],
            structure={'README': 'PASS'},
            git={'available': True, 'branch': 'main'},
            score=HealthScore(score=85, breakdown={})
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_schema_creation(self):
        """Test that schema file is created."""
        result = generate_schema(self.test_data, str(self.output_path))
        self.assertTrue(result)
        self.assertTrue(self.output_path.exists())
    
    def test_schema_is_valid_json(self):
        """Test that generated schema is valid JSON."""
        generate_schema(self.test_data, str(self.output_path))
        
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        
        # Should not raise exception
        self.assertIsInstance(data, dict)
    
    def test_schema_contains_required_fields(self):
        """Test that schema contains all required fields."""
        generate_schema(self.test_data, str(self.output_path))
        
        with open(self.output_path, 'r') as f:
            schema = json.load(f)
        
        # Check for required top-level fields
        self.assertIn('schema_version', schema)
        self.assertIn('generated_at', schema)
        self.assertIn('repository', schema)
        self.assertIn('statistics', schema)
        self.assertIn('languages', schema)
        self.assertIn('metadata', schema)
    
    def test_schema_statistics(self):
        """Test that statistics are correctly computed."""
        generate_schema(self.test_data, str(self.output_path))
        
        with open(self.output_path, 'r') as f:
            schema = json.load(f)
        
        stats = schema['statistics']
        self.assertEqual(stats['total_files'], 2)
        self.assertEqual(stats['total_lines'], 75)
        self.assertEqual(stats['binary_files'], 0)
    
    def test_schema_languages(self):
        """Test that languages are correctly identified."""
        generate_schema(self.test_data, str(self.output_path))
        
        with open(self.output_path, 'r') as f:
            schema = json.load(f)
        
        languages = schema['languages']
        self.assertIn('Python', languages)
        self.assertEqual(languages['Python'], 2)
    
    def test_schema_metadata(self):
        """Test that metadata is included."""
        generate_schema(self.test_data, str(self.output_path))
        
        with open(self.output_path, 'r') as f:
            schema = json.load(f)
        
        metadata = schema['metadata']
        self.assertIsInstance(metadata['has_readme'], bool)
        self.assertIsInstance(metadata['is_git_repo'], bool)
        self.assertEqual(metadata['is_git_repo'], True)
        self.assertEqual(metadata['git_branch'], 'main')


if __name__ == "__main__":
    unittest.main()
