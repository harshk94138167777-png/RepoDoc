import unittest
import os
import tempfile
import json
import shutil
from repodoctor.models import ReportData, HealthScore, GitInfo
from repodoctor.baseline import compare_baseline

class TestBaseline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_compare_baseline(self):
        baseline_path = os.path.join(self.test_dir, "baseline.json")
        baseline_data = {
            "summary": {"health_score": 50, "files": 10, "lines": 100},
            "maintainability": {"todos": 5, "duplicates": 2},
            "security": {"potential_secrets": 1}
        }
        with open(baseline_path, "w") as f:
            json.dump(baseline_data, f)
            
        current = ReportData(
            path=".", name="test", files=[1,2,3,4,5,6,7,8,9,10,11,12], 
            todos=[1,2,3], 
            security=[], 
            duplicates=[1,2,3], 
            structure={}, 
            git=GitInfo(False),
            score=HealthScore(60, [])
        )
        
        # Current has:
        # score = 60, baseline = 50 -> delta = +10
        # files = 12, baseline = 10 -> delta = +2
        # lines = 0 (since fake files have no .lines in this mock setup but we can't easily mock so lines=0) -> delta = -100
        # todos = 3, baseline = 5 -> delta = -2
        # duplicates = 3, baseline = 2 -> delta = +1
        # secrets = 0, baseline = 1 -> delta = -1
        
        class FakeFile:
            def __init__(self):
                self.lines = 0
                
        current.files = [FakeFile() for _ in range(12)]
        
        deltas = compare_baseline(current, baseline_path)
        self.assertIsNotNone(deltas)
        self.assertEqual(deltas["score"], 10)
        self.assertEqual(deltas["files"], 2)
        self.assertEqual(deltas["lines"], -100)
        self.assertEqual(deltas["todos"], -2)
        self.assertEqual(deltas["duplicates"], 1)
        self.assertEqual(deltas["secrets"], -1)

if __name__ == "__main__":
    unittest.main()
