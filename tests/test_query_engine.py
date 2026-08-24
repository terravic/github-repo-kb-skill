import os
import unittest
from scripts.query_engine import RepositoryQueryEngine


class TestRepositoryQueryEngine(unittest.TestCase):
    def setUp(self):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "examples",
            "synthetic_sample_org.json"
        )
        self.engine = RepositoryQueryEngine(kb_path=fixture_path)

    def test_medical_query(self):
        res = self.engine.query("Clinical patient electronic health records and FHIR")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "sample-patient-records")
        self.assertEqual(res["best_match"]["cluster_name"], "Medical & Healthcare")

    def test_genomics_query(self):
        res = self.engine.query("Bioinformatics DNA and RNA sequencing variant analysis")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "sample-genomics-pipeline")
        self.assertEqual(res["best_match"]["cluster_name"], "Life Sciences & Bioinformatics")

    def test_exact_technology_query(self):
        res = self.engine.query("Python client SDK for platform API")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "sample-python-sdk")
        self.assertEqual(res["best_match"]["confidence"], "High")

    def test_domain_capability_query(self):
        res = self.engine.query("OAuth2 and user login authentication service")
        self.assertTrue(res["matched"])
        self.assertIsNotNone(res["best_match"])
        self.assertEqual(res["best_match"]["name"], "sample-auth-service")

    def test_telehealth_portal_query(self):
        res = self.engine.query("Next.js telehealth web portal and physician appointments")
        self.assertTrue(res["matched"])
        self.assertEqual(res["best_match"]["name"], "sample-telehealth-portal")

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
