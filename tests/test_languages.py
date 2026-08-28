import unittest
from repodoctor.models import FileInfo
from repodoctor.languages import detect_languages

class TestLanguages(unittest.TestCase):
    def test_detect_languages(self):
        f1 = FileInfo("", "", ".py", 0, 0, False, "Unknown", "")
        f2 = FileInfo("", "", ".unknown", 0, 0, False, "Unknown", "")
        detect_languages([f1, f2])
        self.assertEqual(f1.language, "Python")
        self.assertEqual(f2.language, "Unknown")

if __name__ == "__main__":
    unittest.main()
