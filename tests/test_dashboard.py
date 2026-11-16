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
        self.assertIn('id="graph-label-mode"', html)
        self.assertIn('id="graph-spacing-mode"', html)
        self.assertIn('id="graph-zoom-level"', html)
        self.assertIn("computeClusterCenters", html)
        self.assertIn("updateSemanticZoom", html)
        self.assertIn("updateClusterRegions", html)
        self.assertIn("updateLinkPaths", html)

    def test_generate_multi_cluster_graph_dashboard(self):
        metadata = {"owner": "multi-org", "input_url": "https://github.com/multi-org"}
        clusters_data = {
            "clusters": [
                {
                    "id": "core",
                    "name": "Core Services",
                    "description": "Core backend",
                    "color": "#3B82F6",
                    "repo_count": 2,
                    "total_stars": 120,
                    "repositories": [1, 2],
                },
                {
                    "id": "frontend",
                    "name": "Frontend Apps",
                    "description": "Web portals",
                    "color": "#06B6D4",
                    "repo_count": 1,
                    "total_stars": 80,
                    "repositories": [3],
                },
            ],
            "repositories": [
                {"id": 1, "name": "api-gateway", "cluster_id": "core", "cluster_name": "Core Services", "cluster_color": "#3B82F6", "stars": 70},
                {"id": 2, "name": "user-service", "cluster_id": "core", "cluster_name": "Core Services", "cluster_color": "#3B82F6", "stars": 50},
                {"id": 3, "name": "web-console", "cluster_id": "frontend", "cluster_name": "Frontend Apps", "cluster_color": "#06B6D4", "stars": 80},
            ],
        }
        graph_data = {
            "nodes": [
                {"id": 1, "name": "api-gateway", "cluster_id": "core", "cluster_name": "Core Services", "cluster_color": "#3B82F6", "is_hub": True, "is_bridge": True, "total_degree": 2},
                {"id": 2, "name": "user-service", "cluster_id": "core", "cluster_name": "Core Services", "cluster_color": "#3B82F6", "is_hub": False, "is_bridge": False, "total_degree": 1},
                {"id": 3, "name": "web-console", "cluster_id": "frontend", "cluster_name": "Frontend Apps", "cluster_color": "#06B6D4", "is_hub": False, "is_bridge": True, "total_degree": 1},
            ],
            "edges": [
                {"source": 1, "target": 2, "type": "depends_on", "label": "Depends on", "is_cross_cluster": False, "source_cluster": "core", "target_cluster": "core", "weight": 2.0},
                {"source": 3, "target": 1, "type": "depends_on", "label": "Consumes API", "is_cross_cluster": True, "source_cluster": "frontend", "target_cluster": "core", "weight": 2.0},
            ],
            "cluster_connectivity_matrix": {"core": {"core": 1, "frontend": 0}, "frontend": {"core": 1, "frontend": 0}},
            "hub_repositories": ["api-gateway"],
            "bridge_repositories": ["api-gateway", "web-console"],
            "cross_cluster_edges_count": 1,
            "intra_cluster_edges_count": 1,
        }

        dash_path = self.generator.generate(metadata, clusters_data, graph_data)
        with open(dash_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("api-gateway", html)
        self.assertIn("web-console", html)
        self.assertIn("graph-zoom-bar", html)
        self.assertIn("recomputeGraphSpacing", html)


if __name__ == "__main__":
    unittest.main()
