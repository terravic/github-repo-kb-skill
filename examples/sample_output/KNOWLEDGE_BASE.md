# Knowledge Base: terravic

Generated on 2026-08-24 19:30:06 UTC for target `https://github.com/terravic`.

## Executive Summary

| Metric | Value |
|---|---|
| Target Address | https://github.com/terravic |
| Total Repositories | 15 |
| Functional Clusters | 7 |
| Architecture Graph Nodes | 15 |
| Graph Edges (Relationships) | 43 |
| Cross-Cluster Connections | 27 |
| Intra-Cluster Connections | 16 |

**Key Architectural Hubs**: `terravic-api-gateway`, `terravic-auth-service`, `terravic-user-service`, `terravic-billing-engine`, `terravic-web-portal`, `terravic-design-system`, `terravic-mobile-app`, `terravic-data-pipeline`, `terravic-ai-engine`, `terravic-js-sdk`, `terravic-python-sdk`, `terravic-core-lib`, `terravic-infrastructure`

**Cross-Domain Bridge Repositories**: `terravic-api-gateway`, `terravic-auth-service`, `terravic-billing-engine`, `terravic-data-pipeline`, `terravic-ai-engine`, `terravic-js-sdk`, `terravic-python-sdk`, `terravic-core-lib`, `terravic-infrastructure`

## Domain Clusters

Repositories are categorized into the following functional domains based on code analysis, topic taxonomy, and dependencies:

### Core Services & Backend APIs

**Description**: Foundational backend services, microservices, gRPC/REST APIs, authentication, and core business engines.

- Repositories: 5
- Aggregate Stars: 1842
- Primary Languages: Go, Python
- Key Technologies: Docker, FastAPI, Fastapi, Go, Grpc, PostgreSQL, PyTorch, Python, Qdrant, RabbitMQ, Redis, gRPC

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-api-gateway](https://github.com/terravic/terravic-api-gateway) | Go | 482 | High-performance edge reverse proxy and authentication gateway routing traffic to core microservices. |
| [terravic-auth-service](https://github.com/terravic/terravic-auth-service) | Go | 315 | OAuth2 / OIDC identity provider and token management service with RBAC enforcement. |
| [terravic-user-service](https://github.com/terravic/terravic-user-service) | Go | 240 | User profiles, tenant management, and organization membership service. |
| [terravic-billing-engine](https://github.com/terravic/terravic-billing-engine) | Python | 195 | Subscription lifecycle, usage meter aggregation, and Stripe payment webhook processing service. |
| [terravic-ai-engine](https://github.com/terravic/terravic-ai-engine) | Python | 610 | LLM inference orchestrator, vector embeddings pipeline, and automated anomaly detection model. |

### Frontend & User Interfaces

**Description**: Client applications, web portals, dashboards, mobile apps, and interactive UI component design systems.

- Repositories: 3
- Aggregate Stars: 960
- Primary Languages: TypeScript
- Key Technologies: Expo, Next.Js, Next.js, React, React Native, Storybook, Tailwind, Tailwind CSS, TypeScript

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-web-portal](https://github.com/terravic/terravic-web-portal) | TypeScript | 520 | Customer facing web portal and administration console built with Next.js and Tailwind CSS. |
| [terravic-design-system](https://github.com/terravic/terravic-design-system) | TypeScript | 280 | Reusable React component library, design tokens, and Storybook documentation. |
| [terravic-mobile-app](https://github.com/terravic/terravic-mobile-app) | TypeScript | 160 | Cross-platform mobile application for incident notifications and operational metrics. |

### Developer Tooling & SDKs

**Description**: Client SDKs, CLI utilities, code generators, testing harnesses, linters, plugins, and agent skills.

- Repositories: 3
- Aggregate Stars: 720
- Primary Languages: TypeScript, Python, Go
- Key Technologies: Cobra, Go, Hatch, Jest, Pydantic, Pytest, Python, Rollup, TypeScript, Viper

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-js-sdk](https://github.com/terravic/terravic-js-sdk) | TypeScript | 295 | Official TypeScript and JavaScript client SDK for integrating with Terravic platform APIs. |
| [terravic-python-sdk](https://github.com/terravic/terravic-python-sdk) | Python | 245 | Python SDK and CLI client for automation scripts, data science workloads, and backend integration. |
| [terravic-cli](https://github.com/terravic/terravic-cli) | Go | 180 | Developer command-line interface for provisioning environments, deploying jobs, and managing tokens. |

### Data Engineering & AI/ML

**Description**: Data pipelines, ETL workflows, stream processing, machine learning models, and analytics infrastructure.

- Repositories: 1
- Aggregate Stars: 390
- Primary Languages: Python
- Key Technologies: Apache Kafka, Apache Spark, ClickHouse, Kafka, Python, Spark

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-data-pipeline](https://github.com/terravic/terravic-data-pipeline) | Python | 390 | Distributed real-time streaming pipeline and ETL workers aggregating telemetry events into data warehouse. |

### Infrastructure & DevOps

**Description**: Cloud infrastructure as code, Kubernetes deployment manifests, CI/CD pipelines, Docker, and monitoring.

- Repositories: 1
- Aggregate Stars: 410
- Primary Languages: HCL
- Key Technologies: AWS, ArgoCD, HCL, Helm, Kubernetes, Terraform

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-infrastructure](https://github.com/terravic/terravic-infrastructure) | HCL | 410 | Terraform modules, Kubernetes Helm charts, and GitOps ArgoCD manifests for cloud environments. |

### Shared Libraries & Utilities

**Description**: Common utilities, protocol definitions, shared data contracts, helper packages, and cross-cutting libraries.

- Repositories: 1
- Aggregate Stars: 340
- Primary Languages: Go
- Key Technologies: Go, Grpc, OpenTelemetry, Protobuf, gRPC

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-core-lib](https://github.com/terravic/terravic-core-lib) | Go | 340 | Shared proto definitions, middleware contracts, structured logging, and telemetry utilities. |

### Documentation & Specifications

**Description**: Architectural blueprints, technical documentation, API specifications, guides, and project roadmaps.

- Repositories: 1
- Aggregate Stars: 130
- Primary Languages: Markdown
- Key Technologies: Docusaurus, Markdown, OpenAPI

| Repository | Language | Stars | Description |
|---|---|---|---|
| [terravic-docs](https://github.com/terravic/terravic-docs) | Markdown | 130 | Developer guides, OpenAPI specifications, architecture RFCs, and deployment blueprints. |

## Knowledge Graph Relationships

The knowledge graph models direct dependencies, API integrations, client SDK usage, and shared technology stacks:

### Depends On (27 relationships)

| Source Repository | Target Repository | Scope | Description |
|---|---|---|---|
| `terravic-api-gateway` | `terravic-core-lib` | Cross-Cluster | terravic-api-gateway imports and depends on terravic-core-lib. |
| `terravic-api-gateway` | `terravic-auth-service` | Intra-Cluster | terravic-api-gateway imports and depends on terravic-auth-service. |
| `terravic-api-gateway` | `terravic-user-service` | Intra-Cluster | terravic-api-gateway imports and depends on terravic-user-service. |
| `terravic-auth-service` | `terravic-core-lib` | Cross-Cluster | terravic-auth-service imports and depends on terravic-core-lib. |
| `terravic-user-service` | `terravic-core-lib` | Cross-Cluster | terravic-user-service imports and depends on terravic-core-lib. |
| `terravic-user-service` | `terravic-auth-service` | Intra-Cluster | terravic-user-service imports and depends on terravic-auth-service. |
| `terravic-billing-engine` | `terravic-user-service` | Intra-Cluster | terravic-billing-engine imports and depends on terravic-user-service. |
| `terravic-billing-engine` | `terravic-python-sdk` | Cross-Cluster | terravic-billing-engine imports and depends on terravic-python-sdk. |
| `terravic-web-portal` | `terravic-js-sdk` | Cross-Cluster | terravic-web-portal imports and depends on terravic-js-sdk. |
| `terravic-web-portal` | `terravic-design-system` | Intra-Cluster | terravic-web-portal imports and depends on terravic-design-system. |
| `terravic-web-portal` | `terravic-python-sdk` | Cross-Cluster | terravic-web-portal uses terravic-python-sdk for API integration. |
| `terravic-design-system` | `terravic-js-sdk` | Cross-Cluster | terravic-design-system uses terravic-js-sdk for API integration. |
| `terravic-design-system` | `terravic-python-sdk` | Cross-Cluster | terravic-design-system uses terravic-python-sdk for API integration. |
| `terravic-mobile-app` | `terravic-js-sdk` | Cross-Cluster | terravic-mobile-app imports and depends on terravic-js-sdk. |
| `terravic-mobile-app` | `terravic-python-sdk` | Cross-Cluster | terravic-mobile-app uses terravic-python-sdk for API integration. |
| `terravic-data-pipeline` | `terravic-core-lib` | Cross-Cluster | terravic-data-pipeline imports and depends on terravic-core-lib. |
| `terravic-ai-engine` | `terravic-data-pipeline` | Cross-Cluster | terravic-ai-engine imports and depends on terravic-data-pipeline. |
| `terravic-ai-engine` | `terravic-python-sdk` | Cross-Cluster | terravic-ai-engine imports and depends on terravic-python-sdk. |
| `terravic-js-sdk` | `terravic-api-gateway` | Cross-Cluster | terravic-js-sdk imports and depends on terravic-api-gateway. |
| `terravic-python-sdk` | `terravic-api-gateway` | Cross-Cluster | terravic-python-sdk imports and depends on terravic-api-gateway. |
| `terravic-cli` | `terravic-api-gateway` | Cross-Cluster | terravic-cli imports and depends on terravic-api-gateway. |
| `terravic-billing-engine` | `terravic-core-lib` | Cross-Cluster | terravic-billing-engine leverages common utilities from terravic-core-lib. |
| `terravic-ai-engine` | `terravic-core-lib` | Cross-Cluster | terravic-ai-engine leverages common utilities from terravic-core-lib. |
| `terravic-infrastructure` | `terravic-api-gateway` | Cross-Cluster | terravic-infrastructure imports and depends on terravic-api-gateway. |
| `terravic-infrastructure` | `terravic-auth-service` | Cross-Cluster | terravic-infrastructure imports and depends on terravic-auth-service. |
| `terravic-infrastructure` | `terravic-data-pipeline` | Cross-Cluster | terravic-infrastructure imports and depends on terravic-data-pipeline. |
| `terravic-docs` | `terravic-api-gateway` | Cross-Cluster | terravic-docs imports and depends on terravic-api-gateway. |

### Routes To (4 relationships)

| Source Repository | Target Repository | Scope | Description |
|---|---|---|---|
| `terravic-api-gateway` | `terravic-auth-service` | Intra-Cluster | terravic-api-gateway routes API requests to terravic-auth-service. |
| `terravic-api-gateway` | `terravic-user-service` | Intra-Cluster | terravic-api-gateway routes API requests to terravic-user-service. |
| `terravic-api-gateway` | `terravic-billing-engine` | Intra-Cluster | terravic-api-gateway routes API requests to terravic-billing-engine. |
| `terravic-api-gateway` | `terravic-ai-engine` | Intra-Cluster | terravic-api-gateway routes API requests to terravic-ai-engine. |

### Interfaces With (2 relationships)

| Source Repository | Target Repository | Scope | Description |
|---|---|---|---|
| `terravic-js-sdk` | `terravic-api-gateway` | Cross-Cluster | terravic-js-sdk provides client bindings for terravic-api-gateway. |
| `terravic-python-sdk` | `terravic-api-gateway` | Cross-Cluster | terravic-python-sdk provides client bindings for terravic-api-gateway. |

### Provisions (3 relationships)

| Source Repository | Target Repository | Scope | Description |
|---|---|---|---|
| `terravic-infrastructure` | `terravic-api-gateway` | Cross-Cluster | terravic-infrastructure manages infrastructure and deployment for terravic-api-gateway. |
| `terravic-infrastructure` | `terravic-auth-service` | Cross-Cluster | terravic-infrastructure manages infrastructure and deployment for terravic-auth-service. |
| `terravic-infrastructure` | `terravic-data-pipeline` | Cross-Cluster | terravic-infrastructure manages infrastructure and deployment for terravic-data-pipeline. |

### Shares Tech (7 relationships)

| Source Repository | Target Repository | Scope | Description |
|---|---|---|---|
| `terravic-api-gateway` | `terravic-ai-engine` | Intra-Cluster | terravic-api-gateway and terravic-ai-engine both utilize docker. |
| `terravic-auth-service` | `terravic-billing-engine` | Intra-Cluster | terravic-auth-service and terravic-billing-engine both utilize postgresql. |
| `terravic-auth-service` | `terravic-ai-engine` | Intra-Cluster | terravic-auth-service and terravic-ai-engine both utilize docker. |
| `terravic-user-service` | `terravic-ai-engine` | Intra-Cluster | terravic-user-service and terravic-ai-engine both utilize docker. |
| `terravic-billing-engine` | `terravic-ai-engine` | Intra-Cluster | terravic-billing-engine and terravic-ai-engine both utilize fastapi. |
| `terravic-web-portal` | `terravic-mobile-app` | Intra-Cluster | terravic-web-portal and terravic-mobile-app both utilize react. |
| `terravic-design-system` | `terravic-mobile-app` | Intra-Cluster | terravic-design-system and terravic-mobile-app both utilize react. |

## Cross-Domain Dependency Matrix

Matrix of relationship counts originating from source cluster (rows) to target cluster (columns):

| Source \ Target | Core Services & Backend APIs | Frontend & User Interfaces | Developer Tooling & SDKs | Data Engineering & AI/ML | Infrastructure & DevOps | Shared Libraries & Utilities | Documentation & Specifications |
|---|---|---|---|---|---|---|---|
| **Core Services & Backend APIs** | 13 | - | 2 | 1 | - | 5 | - |
| **Frontend & User Interfaces** | - | 3 | 6 | - | - | - | - |
| **Developer Tooling & SDKs** | 5 | - | - | - | - | - | - |
| **Data Engineering & AI/ML** | - | - | - | - | - | 1 | - |
| **Infrastructure & DevOps** | 4 | - | - | 2 | - | - | - |
| **Shared Libraries & Utilities** | - | - | - | - | - | - | - |
| **Documentation & Specifications** | 1 | - | - | - | - | - | - |

## Architecture Notes and Recommendations

1. **Modularity**: Hub repositories with high degree centrality should be prioritized for stability, backwards compatibility, and rigorous test coverage.
2. **Boundary Contracts**: Cross-cluster dependencies should enforce versioned API contracts or SDK interfaces to prevent breaking changes across domains.
3. **Shared Tooling**: Shared libraries should maintain minimal third-party dependencies to avoid dependency conflicts across downstream services.
