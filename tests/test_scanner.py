import os
import unittest
from scripts.scanner import GitHubScanner


class TestGitHubScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = GitHubScanner()
        self.fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "examples",
            "synthetic_terravic_org.json",
        )

    def test_parse_github_url_org(self):
        target_type, owner, repo = GitHubScanner.parse_github_url("https://github.com/terravic")
        self.assertEqual(target_type, "owner")
        self.assertEqual(owner, "terravic")
        self.assertIsNone(repo)

    def test_parse_github_url_user(self):
        target_type, owner, repo = GitHubScanner.parse_github_url("github.com/octocat")
        self.assertEqual(target_type, "owner")
        self.assertEqual(owner, "octocat")
        self.assertIsNone(repo)

    def test_parse_github_url_repo(self):
        target_type, owner, repo = GitHubScanner.parse_github_url("https://github.com/terravic/core-api")
        self.assertEqual(target_type, "repo")
        self.assertEqual(owner, "terravic")
        self.assertEqual(repo, "core-api")

    def test_parse_github_url_raw_handle(self):
        target_type, owner, repo = GitHubScanner.parse_github_url("terravic")
        self.assertEqual(target_type, "owner")
        self.assertEqual(owner, "terravic")
        self.assertIsNone(repo)

    def test_load_fixture(self):
        result = self.scanner.load_fixture(self.fixture_path)
        self.assertIn("repositories", result)
        self.assertIn("metadata", result)
        self.assertEqual(result["total_count"], 15)
        self.assertEqual(result["metadata"]["owner"], "terravic")

    def test_normalize_repo(self):
        raw = {
            "name": "sample-repo",
            "description": "A sample repository",
            "language": "Python",
            "stargazers_count": 42,
            "topics": ["python", "api"],
        }
        norm = self.scanner._normalize_repo(raw)
        self.assertEqual(norm["name"], "sample-repo")
        self.assertEqual(norm["primary_language"], "Python")
        self.assertEqual(norm["stars"], 42)
        self.assertIn("python", norm["topics"])


if __name__ == "__main__":
    unittest.main()
