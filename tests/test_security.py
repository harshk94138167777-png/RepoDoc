import unittest
import os
import tempfile
import shutil
from repodoctor.models import FileInfo
from repodoctor.security import scan_security, redact

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_redact(self):
        self.assertEqual(redact("sk-1234567890abcdef"), "sk-...ef")
        # Since logic is `value[:3] + "..." + value[-2:]`:
        self.assertEqual(redact("abcdefghi"), "abc...hi")
        self.assertEqual(redact("short"), "***")

    def test_scan_security(self):
        filepath = os.path.join(self.test_dir, ".env")
        with open(filepath, "w", encoding='utf-8') as f:
            f.write("API_KEY='sk-1234567890abcdef123456'\n")

        f_info = FileInfo(filepath, ".env", "", 100, 1, False, "Unknown", ".env")
        findings = scan_security([f_info])
        
        # Should flag .env itself, and the sk- token, and the API_KEY assignment
        self.assertGreaterEqual(len(findings), 2)
        categories = [f.category for f in findings]
        self.assertIn("Environment File", categories)
        self.assertIn("Potential API Key", categories)
        self.assertIn("API Key or Token", categories)

if __name__ == "__main__":
    unittest.main()
