import unittest
import os
import tempfile
import shutil
from repodoctor.models import FileInfo
from repodoctor.todos import scan_todos

class TestTodos(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_todos(self):
        filepath = os.path.join(self.test_dir, "test.py")
        with open(filepath, "w", encoding='utf-8') as f:
            f.write("# TODO: implement this\nprint('hello')\n# FIXME: broken\n# just a comment\n")

        f_info = FileInfo(filepath, "test.py", ".py", 100, 4, False, "Python", "test.py")
        todos = scan_todos([f_info])
        
        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0].marker, "TODO")
        self.assertEqual(todos[0].line_number, 1)
        self.assertEqual(todos[1].marker, "FIXME")
        self.assertEqual(todos[1].line_number, 3)

if __name__ == "__main__":
    unittest.main()
