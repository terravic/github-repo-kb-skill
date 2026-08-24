import os
import shutil
import tempfile
import unittest
from scripts.dashboard_generator import DashboardGenerator


class TestDashboardGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = DashboardGenerator(output_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_dashboard_html(self):
        metadata = {"owner": "test-org", "input_url": "https://github.com/test-org"}
        clusters_data = {
            "clusters": [
                {
                    "id": "core-services",
                    "name": "Core Services",
                    "description": "Backend services",
                    "repo_count": 1,
                    "total_stars": 25,
                    "repositories": [1],
                }
            ],
            "repositories": [
                {
                    "id": 1,
                    "name": "sample-service",
                    "description": "Test description",
                    "primary_language": "Go",
                    "stars": 25,
                    "cluster_id": "core-services",
                    "cluster_name": "Core Services",
                    "cluster_color": "#3B82F6",
                }
            ],
        }
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "name": "sample-service",
                    "cluster_id": "core-services",
                    "cluster_name": "Core Services",
                    "cluster_color": "#3B82F6",
                    "is_hub": True,
                    "is_bridge": False,
                }
            ],
            "edges": [],
            "cluster_connectivity_matrix": {},
            "hub_repositories": ["sample-service"],
            "bridge_repositories": [],
            "cross_cluster_edges_count": 0,
            "intra_cluster_edges_count": 0,
        }

        dash_path = self.generator.generate(metadata, clusters_data, graph_data)

        self.assertTrue(os.path.isfile(dash_path))
        with open(dash_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("test-org", html)
        self.assertIn("d3.forceSimulation", html)
        self.assertIn("sample-service", html)


if __name__ == "__main__":
    unittest.main()
