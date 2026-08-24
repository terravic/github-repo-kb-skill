import unittest
from scripts.clusterer import RepositoryClusterer


class TestRepositoryClusterer(unittest.TestCase):
    def setUp(self):
        self.clusterer = RepositoryClusterer()

    def test_classify_core_service(self):
        repo = {
            "id": 1,
            "name": "auth-service",
            "description": "OAuth2 authentication service with gRPC endpoints",
            "primary_language": "Go",
            "topics": ["auth", "grpc", "microservice"],
            "tech_stack": ["Go", "gRPC", "PostgreSQL"],
        }
        cluster_id = self.clusterer._classify_repository(repo)
        self.assertEqual(cluster_id, "core-services")

    def test_classify_frontend(self):
        repo = {
            "id": 2,
            "name": "web-dashboard",
            "description": "User portal dashboard built with React",
            "primary_language": "TypeScript",
            "topics": ["react", "frontend", "ui"],
            "tech_stack": ["React", "Tailwind CSS"],
        }
        cluster_id = self.clusterer._classify_repository(repo)
        self.assertEqual(cluster_id, "frontend-ui")

    def test_classify_sdk(self):
        repo = {
            "id": 3,
            "name": "python-sdk",
            "description": "Python client library and SDK",
            "primary_language": "Python",
            "topics": ["sdk", "client-library"],
            "tech_stack": ["Python"],
        }
        cluster_id = self.clusterer._classify_repository(repo)
        self.assertEqual(cluster_id, "developer-tooling")

    def test_custom_rule_override(self):
        custom_clusterer = RepositoryClusterer(custom_rules=[
            {"pattern": "special-.*", "cluster_id": "infrastructure-devops"}
        ])
        repo = {
            "id": 4,
            "name": "special-service",
            "description": "General service",
            "primary_language": "Go",
            "topics": [],
        }
        cluster_id = custom_clusterer._classify_repository(repo)
        self.assertEqual(cluster_id, "infrastructure-devops")

    def test_cluster_repositories_aggregation(self):
        repos = [
            {"id": 1, "name": "api-service", "description": "Core API", "primary_language": "Go", "topics": ["api"], "stars": 100, "forks": 10},
            {"id": 2, "name": "web-ui", "description": "Web UI", "primary_language": "TypeScript", "topics": ["react", "ui"], "stars": 50, "forks": 5},
        ]
        result = self.clusterer.cluster_repositories(repos)
        self.assertEqual(result["cluster_count"], 2)
        self.assertEqual(len(result["repositories"]), 2)


if __name__ == "__main__":
    unittest.main()
