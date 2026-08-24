import os
import unittest
from scripts.query_engine import RepositoryQueryEngine


class TestRepositoryQueryEngine(unittest.TestCase):
    def setUp(self):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "examples",
            "synthetic_terravic_org.json"
        )
        self.engine = RepositoryQueryEngine(kb_path=fixture_path)

    def test_exact_technology_query(self):
        res = self.engine.query("Python client SDK for platform API")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "terravic-python-sdk")
        self.assertEqual(res["best_match"]["confidence"], "High")

    def test_domain_capability_query(self):
        res = self.engine.query("OAuth2 and user login authentication service")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "terravic-auth-service")

    def test_frontend_query(self):
        res = self.engine.query("Next.js web portal dashboard")
        self.assertTrue(res["matched"])
        self.assertEqual(res["best_match"]["name"], "terravic-web-portal")

    def test_non_matching_query(self):
        res = self.engine.query("Blockchain cryptocurrency mining smart contract engine")
        self.assertFalse(res["matched"])
        self.assertIsNone(res["best_match"])
        self.assertIn("No repository in this organization can answer your need", res["message"])

    def test_empty_query(self):
        res = self.engine.query("")
        self.assertFalse(res["matched"])
        self.assertIn("Query string is empty", res["message"])


if __name__ == "__main__":
    unittest.main()
