import unittest
import os
import tempfile
import shutil
from repodoctor.models import FileInfo
from repodoctor.metrics import analyze_metrics

class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_analyze_python_metrics(self):
        filepath = os.path.join(self.test_dir, "test.py")
        with open(filepath, "w", encoding='utf-8') as f:
            f.write("class A:\n    def b():\n        pass\n\n# comment\n")

        f_info = FileInfo(filepath, "test.py", ".py", 100, 5, False, "Python", "test.py")
        analyze_metrics([f_info])
        
        self.assertIsNotNone(f_info.metrics)
        self.assertEqual(f_info.metrics.num_classes, 1)
        self.assertEqual(f_info.metrics.num_functions, 1)
        self.assertEqual(f_info.metrics.comment_lines, 1)
        self.assertEqual(f_info.metrics.blank_lines, 1)
        self.assertEqual(f_info.metrics.code_lines, 3)
        self.assertEqual(f_info.metrics.max_nesting, 2) # `        pass` is 8 spaces = 2 depth

if __name__ == "__main__":
    unittest.main()
