import os
import shutil
import tempfile
import unittest
from scripts.cli import run_pipeline


class TestEndToEndPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "examples",
            "synthetic_terravic_org.json",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_e2e_pipeline_with_fixture(self):
        result = run_pipeline(
            fixture_path=self.fixture_path,
            output_dir=self.temp_dir,
            include_forks=False,
            include_archived=True,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_repositories"], 15)
        self.assertGreaterEqual(result["total_clusters"], 5)
        self.assertGreaterEqual(result["total_edges"], 10)

        self.assertTrue(os.path.isfile(result["dashboard_path"]))
        self.assertTrue(os.path.isfile(result["knowledge_base_json"]))
        self.assertTrue(os.path.isfile(result["knowledge_base_md"]))
        self.assertTrue(os.path.isfile(result["knowledge_graph_json"]))


if __name__ == "__main__":
    unittest.main()
