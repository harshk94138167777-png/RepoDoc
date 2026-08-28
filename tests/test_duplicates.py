import unittest
import os
import tempfile
import shutil
from repodoctor.models import FileInfo
from repodoctor.duplicates import scan_duplicates

class TestDuplicates(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_duplicates(self):
        code_block = "\n".join([f"line_{i} = {i}" for i in range(10)])
        
        f1 = os.path.join(self.test_dir, "file1.py")
        f2 = os.path.join(self.test_dir, "file2.py")
        
        with open(f1, "w") as f: f.write(code_block)
        with open(f2, "w") as f: f.write(code_block)

        info1 = FileInfo(f1, "file1.py", ".py", 100, 10, False, "Python", "file1.py")
        info2 = FileInfo(f2, "file2.py", ".py", 100, 10, False, "Python", "file2.py")
        
        dups = scan_duplicates([info1, info2], min_lines=5)
        self.assertGreater(len(dups), 0)
        
        # Check if file1.py and file2.py are reported together
        found = False
        for d in dups:
            if "file1.py" in d.filepaths and "file2.py" in d.filepaths:
                found = True
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()
