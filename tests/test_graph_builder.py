import unittest
from scripts.graph_builder import KnowledgeGraphBuilder


class TestKnowledgeGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = KnowledgeGraphBuilder()
        self.clusters = [
            {"id": "core-services", "name": "Core Services & Backend APIs"},
            {"id": "frontend-ui", "name": "Frontend & User Interfaces"},
            {"id": "developer-tooling", "name": "Developer Tooling & SDKs"},
        ]

    def test_graph_construction_with_dependencies(self):
        repos = [
            {
                "id": 1,
                "name": "core-api",
                "cluster_id": "core-services",
                "dependencies": [],
                "tech_stack": ["Go", "PostgreSQL"],
                "stars": 100,
            },
            {
                "id": 2,
                "name": "client-sdk",
                "cluster_id": "developer-tooling",
                "dependencies": ["core-api"],
                "tech_stack": ["TypeScript"],
                "stars": 50,
            },
            {
                "id": 3,
                "name": "web-portal",
                "cluster_id": "frontend-ui",
                "dependencies": ["client-sdk"],
                "tech_stack": ["TypeScript", "React"],
                "stars": 80,
            },
        ]
        graph = self.builder.build_graph(repos, self.clusters)
        self.assertEqual(graph["total_nodes"], 3)
        self.assertGreaterEqual(graph["total_edges"], 2)
        self.assertTrue(any(e["is_cross_cluster"] for e in graph["edges"]))

    def test_shared_tech_relationship(self):
        repos = [
            {
                "id": 1,
                "name": "service-alpha",
                "cluster_id": "core-services",
                "dependencies": [],
                "tech_stack": ["Go", "Kafka"],
            },
            {
                "id": 2,
                "name": "service-beta",
                "cluster_id": "core-services",
                "dependencies": [],
                "tech_stack": ["Python", "Kafka"],
            },
        ]
        graph = self.builder.build_graph(repos, self.clusters)
        self.assertTrue(any(e["type"] == "shares_tech" for e in graph["edges"]))


if __name__ == "__main__":
    unittest.main()
