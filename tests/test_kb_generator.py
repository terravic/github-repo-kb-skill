import json
import os
import shutil
import tempfile
import unittest
from scripts.kb_generator import KnowledgeBaseGenerator


class TestKnowledgeBaseGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = KnowledgeBaseGenerator(output_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_all(self):
        metadata = {"owner": "test-org", "input_url": "https://github.com/test-org"}
        clusters_data = {
            "cluster_count": 1,
            "clusters": [
                {
                    "id": "core-services",
                    "name": "Core Services",
                    "description": "Backend services",
                    "repositories": [1],
                    "total_stars": 10,
                }
            ],
            "repositories": [
                {
                    "id": 1,
                    "name": "service-one",
                    "primary_language": "Python",
                    "stars": 10,
                    "description": "A backend service",
                    "cluster_id": "core-services",
                }
            ],
        }
        graph_data = {
            "total_nodes": 1,
            "total_edges": 0,
            "cross_cluster_edges_count": 0,
            "intra_cluster_edges_count": 0,
            "nodes": [{"id": 1, "name": "service-one"}],
            "edges": [],
            "hub_repositories": ["service-one"],
            "bridge_repositories": [],
            "cluster_connectivity_matrix": {},
        }

        files = self.generator.generate_all(metadata, clusters_data, graph_data)

        self.assertTrue(os.path.isfile(files["knowledge_base_json"]))
        self.assertTrue(os.path.isfile(files["knowledge_graph_json"]))
        self.assertTrue(os.path.isfile(files["knowledge_base_md"]))

        with open(files["knowledge_base_json"], "r", encoding="utf-8") as f:
            kb_data = json.load(f)
            self.assertEqual(kb_data["summary"]["total_repositories"], 1)

        with open(files["knowledge_base_md"], "r", encoding="utf-8") as f:
            md_text = f.read()
            self.assertIn("# Knowledge Base: test-org", md_text)
            self.assertIn("Core Services", md_text)


if __name__ == "__main__":
    unittest.main()
