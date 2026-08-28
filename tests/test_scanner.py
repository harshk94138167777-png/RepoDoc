import unittest
import os
import tempfile
import shutil
from repodoctor.scanner import scan_repository

class TestScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_normal_directory(self):
        # Create a text file
        filepath = os.path.join(self.test_dir, "test.txt")
        with open(filepath, "w") as f:
            f.write("Line 1\nLine 2\n")

        # Create a nested directory with an ignored name
        ignored_dir = os.path.join(self.test_dir, "node_modules")
        os.mkdir(ignored_dir)
        with open(os.path.join(ignored_dir, "ignored.txt"), "w") as f:
            f.write("Should not be seen")

        files = scan_repository(self.test_dir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].filename, "test.txt")
        self.assertEqual(files[0].lines, 2)
        self.assertFalse(files[0].is_binary)
        self.assertEqual(files[0].extension, ".txt")

    def test_scan_binary_file(self):
        filepath = os.path.join(self.test_dir, "test.bin")
        with open(filepath, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04")

        files = scan_repository(self.test_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].is_binary)
        self.assertEqual(files[0].lines, 0)

if __name__ == "__main__":
    unittest.main()
