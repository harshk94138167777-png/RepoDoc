import unittest
from repodoctor.models import ReportData, GitInfo, FileInfo, FileMetrics, SecurityFinding, DuplicateBlock, TodoItem
from repodoctor.scoring import calculate_score

class TestScoring(unittest.TestCase):
    def test_perfect_score(self):
        data = ReportData(
            path=".", name="test", files=[], todos=[], security=[], duplicates=[],
            structure={"README": "PASS", "Tests": "PASS", ".gitignore": "PASS"},
            git=GitInfo(True)
        )
        score = calculate_score(data)
        self.assertEqual(score.score, 100)

    def test_penalties(self):
        data = ReportData(
            path=".", name="test", files=[], todos=[TodoItem("", 1, "TODO", "TODO")],
            security=[SecurityFinding("", 1, "test", "HIGH", "test", "***")],
            duplicates=[DuplicateBlock(["a", "b"], (1, 10), "exact")],
            structure={"README": "PASS"},
            git=GitInfo(True)
        )
        score = calculate_score(data)
        self.assertLess(score.score, 100)
        breakdown_names = [b[0] for b in score.breakdown]
        self.assertIn("Potential secrets", breakdown_names)
        self.assertIn("Duplicate blocks", breakdown_names)
        self.assertIn("TODO/FIXME count", breakdown_names)

if __name__ == "__main__":
    unittest.main()
