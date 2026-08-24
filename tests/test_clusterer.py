import unittest
from scripts.clusterer import RepositoryClusterer


class TestRepositoryClusterer(unittest.TestCase):
    def setUp(self):
        self.clusterer = RepositoryClusterer()

    def test_classify_medical_healthcare(self):
        repo = {
            "id": 1,
            "name": "patient-health-records",
            "description": "FHIR and DICOM medical records storage for clinical patient management",
            "primary_language": "Go",
            "topics": ["medical", "healthcare", "fhir", "patient"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "medical-healthcare")

    def test_classify_life_sciences(self):
        repo = {
            "id": 2,
            "name": "genomics-variant-caller",
            "description": "DNA and RNA sequencing bioinformatics pipeline for molecular genetics research",
            "primary_language": "Python",
            "topics": ["genomics", "bioinformatics", "dna", "biology"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "life-sciences-bio")

    def test_classify_finance_billing(self):
        repo = {
            "id": 3,
            "name": "subscription-billing-service",
            "description": "Automated recurring invoice generation and Stripe checkout integration",
            "primary_language": "Python",
            "topics": ["billing", "payment", "stripe", "finance"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "finance-billing")

    def test_classify_security_identity(self):
        repo = {
            "id": 4,
            "name": "oauth-identity-provider",
            "description": "OIDC single sign-on, JWT token issuance, and RBAC authentication",
            "primary_language": "Go",
            "topics": ["auth", "security", "oauth2", "jwt"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "security-identity")

    def test_classify_developer_tooling(self):
        repo = {
            "id": 5,
            "name": "python-sdk",
            "description": "Python client library and CLI SDK for developer automation",
            "primary_language": "Python",
            "topics": ["sdk", "client-library", "cli"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "developer-tooling")

    def test_classify_utilities(self):
        repo = {
            "id": 6,
            "name": "shared-common-utils",
            "description": "Shared protobuf data contracts, base helpers, and common utility functions",
            "primary_language": "Go",
            "topics": ["utils", "common", "proto", "shared"],
        }
        cluster = self.clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "utilities-libraries")

    def test_custom_rule_override(self):
        custom_clusterer = RepositoryClusterer(custom_rules=[
            {"pattern": "custom-.*", "cluster_id": "medical-healthcare"}
        ])
        repo = {
            "id": 7,
            "name": "custom-tool",
            "description": "General tool",
            "primary_language": "Go",
            "topics": [],
        }
        cluster = custom_clusterer.classify_repository(repo)
        self.assertEqual(cluster["id"], "medical-healthcare")

    def test_cluster_repositories_aggregation(self):
        repos = [
            {"id": 1, "name": "patient-records", "description": "Medical patient EHR records", "primary_language": "Go", "topics": ["medical", "ehr"], "stars": 100, "forks": 10},
            {"id": 2, "name": "dna-pipeline", "description": "Genomics sequencing", "primary_language": "Python", "topics": ["genomics"], "stars": 50, "forks": 5},
        ]
        result = self.clusterer.cluster_repositories(repos)
        self.assertEqual(result["cluster_count"], 2)
        self.assertEqual(len(result["repositories"]), 2)


if __name__ == "__main__":
    unittest.main()
