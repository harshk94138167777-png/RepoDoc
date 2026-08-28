import unittest
import os
import tempfile
import shutil
from repodoctor.structure import check_project_structure

class TestStructure(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_empty_structure(self):
        results = check_project_structure(self.test_dir)
        self.assertEqual(results["README"], "WARN")
        self.assertEqual(results[".gitignore"], "NOT APPLICABLE")
        self.assertEqual(results["Tests"], "WARN")
        self.assertEqual(results["LICENSE"], "WARN")
        self.assertEqual(results["CI config"], "WARN")

    def test_full_structure(self):
        os.mkdir(os.path.join(self.test_dir, ".git"))
        open(os.path.join(self.test_dir, "README.md"), "w").close()
        open(os.path.join(self.test_dir, ".gitignore"), "w").close()
        open(os.path.join(self.test_dir, "LICENSE"), "w").close()
        os.mkdir(os.path.join(self.test_dir, "tests"))
        os.mkdir(os.path.join(self.test_dir, ".github"))

        results = check_project_structure(self.test_dir)
        self.assertEqual(results["README"], "PASS")
        self.assertEqual(results[".gitignore"], "PASS")
        self.assertEqual(results["Tests"], "PASS")
        self.assertEqual(results["LICENSE"], "PASS")
        self.assertEqual(results["CI config"], "PASS")

if __name__ == "__main__":
    unittest.main()
