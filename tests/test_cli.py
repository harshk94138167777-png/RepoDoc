import unittest
from repodoctor.cli import parse_args

class TestCLI(unittest.TestCase):
    def test_default_args(self):
        args = parse_args([])
        self.assertEqual(args.path, ".")
        self.assertFalse(args.json)
        self.assertFalse(args.no_color)
        self.assertEqual(args.ignore, "")
        self.assertEqual(args.large_file_lines, 500)
        self.assertEqual(args.duplicate_lines, 8)
        self.assertFalse(args.security)
        self.assertFalse(args.todos)
        self.assertFalse(args.git)
        self.assertFalse(args.verbose)

    def test_custom_args(self):
        args = parse_args(["/my/path", "--json", "--ignore", "node_modules", "--large-file-lines", "1000", "--duplicate-lines", "10", "--git"])
        self.assertEqual(args.path, "/my/path")
        self.assertTrue(args.json)
        self.assertEqual(args.ignore, "node_modules")
        self.assertEqual(args.large_file_lines, 1000)
        self.assertEqual(args.duplicate_lines, 10)
        self.assertTrue(args.git)

if __name__ == "__main__":
    unittest.main()
