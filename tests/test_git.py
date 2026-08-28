import unittest
import os
import tempfile
import shutil
from unittest.mock import patch
from repodoctor.git import get_git_info

class TestGit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('repodoctor.git.run_git')
    def test_git_unavailable(self, mock_run):
        mock_run.return_value = ""
        info = get_git_info(self.test_dir)
        self.assertFalse(info.available)

    @patch('repodoctor.git.run_git')
    def test_git_available(self, mock_run):
        def side_effect(cmd, cwd):
            if cmd == ["rev-parse", "--is-inside-work-tree"]:
                return "true"
            elif cmd == ["branch", "--show-current"]:
                return "main"
            elif cmd == ["rev-list", "--count", "HEAD"]:
                return "42"
            elif cmd == ["status", "--porcelain"]:
                return "M file.txt\n?? other.txt"
            return ""
        mock_run.side_effect = side_effect

        info = get_git_info(self.test_dir)
        self.assertTrue(info.available)
        self.assertEqual(info.branch, "main")
        self.assertEqual(info.commits, 42)
        self.assertEqual(info.uncommitted_changes, 2)

if __name__ == "__main__":
    unittest.main()
