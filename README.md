# GitHub Repository Knowledge Base and Canvas UI Dashboard (github-repo-kb)

An agent skill and Python engine that analyzes GitHub organizations, user profiles, or repository collections to generate an architecture knowledge base, domain clustering taxonomy, relationship knowledge graph, an interactive HTML5 Canvas UI dashboard, and conversational repository search.

---

## Table of Contents

- [Overview](#overview)
- [Architecture and Workflow](#architecture-and-workflow)
- [Project Structure and File Tree](#project-structure-and-file-tree)
- [Non-Technical User Guide: How to Use This Skill](#non-technical-user-guide-how-to-use-this-skill)
  - [What This Skill Does in Plain Terms](#what-this-skill-does-in-plain-terms)
  - [Core Concepts Explained](#core-concepts-explained)
  - [Step-by-Step Instructions](#step-by-step-instructions)
  - [Real-World Usage Scenarios and Example Prompts](#real-world-usage-scenarios-and-example-prompts)
  - [Asking Questions and Searching for Programs in Chat](#asking-questions-and-searching-for-programs-in-chat)
  - [How to Interact with the Visual Canvas Dashboard](#how-to-interact-with-the-visual-canvas-dashboard)
  - [Troubleshooting Common Situations](#troubleshooting-common-situations)
- [Canvas UI Integration and Architecture](#canvas-ui-integration-and-architecture)
- [Key Features](#key-features)
- [Requirements](#requirements)
- [Configuration Guide](#configuration-guide)
- [Running the Python Code Directly](#running-the-python-code-directly)
  - [1. Quick Start with Offline Synthetic Data](#1-quick-start-with-offline-synthetic-data)
  - [2. Scanning a Live GitHub Organization or User](#2-scanning-a-live-github-organization-or-user)
  - [3. Querying the Knowledge Base via CLI](#3-querying-the-knowledge-base-via-cli)
  - [4. Scanning a Single Repository](#4-scanning-a-single-repository)
  - [5. CLI Reference](#5-cli-reference)
  - [6. Running Automated Tests](#6-running-automated-tests)
- [Architecture and Data Model](#architecture-and-data-model)
  - [Domain Taxonomy](#domain-taxonomy)
  - [Knowledge Graph Schema](#knowledge-graph-schema)
  - [Centrality and Hub Classification](#centrality-and-hub-classification)
- [Interactive Canvas UI Elements](#interactive-canvas-ui-elements)
- [Security and Synthetic Data Compliance](#security-and-synthetic-data-compliance)
- [License](#license)

---

## Overview

Modern software organizations often maintain dozens or hundreds of repositories spanning microservices, client applications, SDKs, data pipelines, infrastructure scripts, and documentation. Navigating and understanding the high-level architecture across these codebases is challenging.

The `github-repo-kb` skill automates the entire ingestion, analysis, and visualization process:
1. Ingests metadata from live GitHub accounts or offline synthetic datasets.
2. Classifies repositories into logical domain clusters using keyword, topic, and language taxonomy rules.
3. Constructs an architectural knowledge graph mapping intra-cluster and cross-cluster relationships (dependencies, API routing, client SDKs, shared infrastructure).
4. Provides semantic repository search so users can ask questions in natural language and find the best-suited repository for any software capability.
5. Generates structured documentation (`KNOWLEDGE_BASE.md`, `knowledge_base.json`, `knowledge_graph.json`) and a standalone interactive Canvas UI dashboard (`dashboard.html`).

---

## Architecture and Workflow

![Architecture and Workflow Overview](assets/workflow_overview.png)

The diagram above illustrates the end-to-end processing pipeline:
- **Input**: GitHub target address (organization or user URL), configuration settings in `scanner_config.json`, or offline synthetic datasets.
- **Processing Engine**:
  1. *Repository Scanner*: Fetches repository metadata, dependencies, topics, languages, and star metrics.
  2. *Domain Taxonomy Clustering*: Classifies codebases into logical domain clusters.
  3. *Knowledge Graph Builder*: Links repositories, evaluates centrality scores, and detects architectural hubs.
  4. *Repository Query Engine*: Evaluates natural language requests to recommend specific repositories or report when no codebase meets the requirement.
- **Output Deliverables**:
  - *Structured Knowledge Base Files*: Machine-readable JSON specifications and formatted Markdown catalogs.
  - *Interactive Canvas Web Dashboard*: Single-file HTML5/D3.js application with force-directed graph physics, domain cards, interactive repository matcher, and inspection panels.

---

## Project Structure and File Tree

Below is the complete file tree of the project:

```
github-repo-kb-skill/
├── LICENSE                           # Apache License 2.0 terms and conditions
├── SKILL.md                          # Agent skill definition and instructions for AI harnesses
├── README.md                         # Project documentation and non-technical guide
├── scanner_config.json               # Default editable scanner configuration file
├── scanner_config.template.json      # Configuration template with clean placeholders
├── requirements.txt                  # Minimal requirements definition (Python stdlib by default)
├── assets/
│   └── workflow_overview.png         # Architecture and workflow diagram image
├── scripts/
│   ├── __init__.py                   # Python package initialization
│   ├── cli.py                        # Command-line interface and execution pipeline orchestrator
│   ├── scanner.py                    # GitHub API ingestion engine and fixture loader
│   ├── clusterer.py                  # Domain taxonomy classifier and clustering rules engine
│   ├── graph_builder.py              # Knowledge graph builder and centrality scoring analyzer
│   ├── query_engine.py               # Repository search, semantic matching, and recommendation engine
│   ├── kb_generator.py               # Markdown and JSON Knowledge Base artifact generator
│   └── dashboard_generator.py        # Standalone interactive Canvas UI dashboard generator
├── examples/
│   ├── synthetic_terravic_org.json   # 15-repository synthetic dataset for offline testing
│   └── sample_output/                # Pre-generated sample output files
│       ├── dashboard.html            # Pre-rendered interactive Canvas dashboard
│       ├── KNOWLEDGE_BASE.md         # Pre-rendered technical Markdown report
│       ├── knowledge_base.json       # Pre-rendered complete structured JSON database
│       └── knowledge_graph.json      # Pre-rendered node-link graph specification
├── output/                           # Default directory where generated files are saved
│   ├── dashboard.html                # Generated Canvas UI dashboard
│   ├── KNOWLEDGE_BASE.md             # Generated Markdown knowledge base catalog
│   ├── knowledge_base.json           # Generated JSON knowledge base
│   └── knowledge_graph.json          # Generated node-link graph JSON
└── tests/
    ├── __init__.py                   # Test package initialization
    ├── test_scanner.py               # Unit tests for URL parsing and metadata normalization
    ├── test_clusterer.py             # Unit tests for domain clustering and regex rules
    ├── test_graph_builder.py         # Unit tests for node, edge, and centrality logic
    ├── test_query_engine.py          # Unit tests for natural language repository search
    ├── test_kb_generator.py          # Unit tests for Markdown and JSON output formatting
    ├── test_dashboard.py             # Unit tests for Canvas HTML dashboard generation
    └── test_e2e.py                   # End-to-end integration tests for the full pipeline
```

---

## Non-Technical User Guide: How to Use This Skill

### What This Skill Does in Plain Terms

You do not need to write code or use complex developer commands to use this tool.

When you point this skill at a GitHub account (such as `https://github.com/terravic` or any company GitHub page), the skill automatically inspects all the code projects in that account, organizes them into logical categories (like Web Apps, Backend Services, or Developer Tools), figures out how those projects connect to each other, builds an interactive visual dashboard in Canvas, and allows you to chat about any program or software capability you need.

---

### Core Concepts Explained

- **Repository (Repo)**: A single project or software folder stored on GitHub.
- **Organization / Account**: A collection of multiple repositories belonging to a company, open-source project, or individual.
- **Domain Cluster**: A functional grouping of related projects. For example, grouping all user-facing websites into "Frontend UI" and all background processing systems into "Data Engineering".
- **Knowledge Graph**: An interactive visual map where every circle is a software project and the lines connecting them show how projects share code, talk to each other, or depend on one another.
- **Repository Matcher & Search**: A search engine that tells you exactly which repository in the organization is best suited to your request, or tells you if no repository fits your need.
- **Canvas UI**: The visual interactive panel that opens next to your chat conversation in AI assistant apps (such as Gemini Enterprise App or Antigravity).

---

### Step-by-Step Instructions

#### Step 1: Open Your AI Chat Interface
Open your AI assistant (Gemini Enterprise App, Antigravity, or any app equipped with this skill).

#### Step 2: Ask the AI to Run the Analysis
Type a natural message giving the GitHub address you want to analyze.
For example:
> "Please scan https://github.com/terravic using the github-repo-kb skill and open the visual dashboard in Canvas."

#### Step 3: Review the Results
The AI assistant will:
1. Scan and categorize the repositories.
2. Provide a clean summary table in the chat showing total projects, domain categories, and central hub systems.
3. Open the interactive visual dashboard in your Canvas panel.

#### Step 4: Ask Questions or Explore the Dashboard
You can ask questions directly in the chat (e.g. *"Which repository should I use to build a Python integration?"*) or click the **Repository Matcher** tab inside Canvas to search visually.

---

### Asking Questions and Searching for Programs in Chat

After an organization is analyzed, you can ask the AI about any tool or capability. The skill will identify the best repository or inform you if no repository matches.

#### Example 1: Finding an Integration SDK
- **Your Question in Chat**: *"Which repository should I use if I want to write automation scripts in Python to talk to the platform API?"*
- **Skill Response**:
  > **Best Matched Repository**: `terravic-python-sdk` (High Confidence)
  >
  > **Domain**: Developer Tooling & SDKs | **Language**: Python
  >
  > **GitHub URL**: `https://github.com/terravic/terravic-python-sdk`
  >
  > **Why this fits**: The repository provides an official Python SDK and CLI client with Pydantic serialization specifically designed for automation scripts and backend integration.

#### Example 2: Finding an Authentication Service
- **Your Question in Chat**: *"Where is OAuth2 login and token authentication handled?"*
- **Skill Response**:
  > **Best Matched Repository**: `terravic-auth-service` (High Confidence)
  >
  > **Domain**: Core Services & Backend APIs | **Language**: Go
  >
  > **Why this fits**: This repository implements the OAuth2 / OIDC identity provider, JWT token signing, and role-based access control (RBAC).

#### Example 3: Searching for a Feature Not Present in the Organization
- **Your Question in Chat**: *"Is there a repository for video transcoding and media streaming?"*
- **Skill Response**:
  > **No matching repository found**: No repository in this organization can answer your need for *"video transcoding and media streaming"*.
  >
  > The organization currently contains repositories across these domains: *Core Services & Backend APIs*, *Frontend & User Interfaces*, *Developer Tooling & SDKs*, *Data Engineering & AI/ML*, *Infrastructure & DevOps*, *Shared Libraries & Utilities*, and *Documentation & Specifications*.

---

### Real-World Usage Scenarios and Example Prompts

#### Scenario 1: Exploring a New Organization
```
Please run the github-repo-kb skill on https://github.com/terravic. Group all projects into logical domains, map out the architecture knowledge graph, and display the dashboard in Canvas.
```

#### Scenario 2: Running a Quick Safe Demonstration (Offline)
```
Run the github-repo-kb skill using the built-in synthetic sample dataset in examples/synthetic_terravic_org.json and show the interactive dashboard.
```

#### Scenario 3: Customizing Scan Settings in a File
1. Open the file `scanner_config.json` in your file editor.
2. Change the `"target_url"` field to your organization (e.g. `"https://github.com/your-organization"`).
3. Save the file.
4. Send this prompt:
```
Please execute the github-repo-kb skill using the settings configured in scanner_config.json.
```

---

### How to Interact with the Visual Canvas Dashboard

Once the dashboard loads in your Canvas panel:

1. **Repository Matcher & Chat Tab**:
   - Click the **Repository Matcher & Chat** tab at the top.
   - Type any question or capability (e.g. *"React UI dashboard"*, *"Kafka streaming"*, *"Video transcoding"*) into the search box and press Enter.
   - The result card will display the best-suited repository with a **Locate on Knowledge Graph** button that switches to the visual graph and centers on that repository!
2. **Top Search Bar & Preset Switcher**:
   - You can type or paste any new GitHub URL directly into the search bar at the top of the dashboard and click **Scan Address** to analyze a new organization immediately inside the dashboard.
   - Use the **Presets** dropdown to quickly switch between the Synthetic demo platform, Pallets (Flask ecosystem), or FastAPI.
3. **Knowledge Graph Canvas**:
   - **Zoom and Pan**: Scroll with your mouse wheel or trackpad to zoom in and out. Click and drag the canvas background to move around.
   - **Move Nodes**: Click and drag any circle to rearrange the visual layout.
   - **Pause Physics**: Click the "Pause Physics" button to lock the visual map in place.
   - **Filter Categories**: Use the "All Clusters" dropdown to isolate one area (such as "Frontend & User Interfaces" or "Core Services").
4. **Inspection Side Drawer**:
   - When you click on any repository circle, a detailed panel slides in from the right.
   - It shows the repository description, star count, programming language, and exact list of dependencies.
5. **Cluster Explorer & Repository Catalog**:
   - Summary cards and sortable spreadsheet tables for all repositories in the organization.

---

### Troubleshooting Common Situations

- **GitHub Rate Limit Warning**:
  - Unauthenticated public GitHub searches are limited to 60 requests per hour.
  - Paste a GitHub Personal Access Token into `"auth_token"` in `scanner_config.json`, or ask the AI: "Run the skill in offline mode using the synthetic sample dataset."
- **Opening the Dashboard Outside the AI Chat**:
  - The generated file `output/dashboard.html` is a standalone web page. You can double-click it or open it in Google Chrome, Mozilla Firefox, Apple Safari, or Microsoft Edge at any time without needing an internet connection.

---

## Canvas UI Integration and Architecture

Agent harnesses such as **Gemini Enterprise App**, **Spark**, and **Antigravity** provide built-in Canvas support. Canvas renders rich, interactive web applications directly within an iframe side-by-side with the agent conversation.

This skill is architected specifically to maximize the Canvas experience:
- **Iframe Sandboxing Compatibility**: Built with pure native HTML, CSS, and vanilla JavaScript without external build steps or server-side dependencies.
- **Embedded Real-Time Scanner**: The Canvas UI contains an address bar where users can type any GitHub address or select presets directly inside the Canvas panel to trigger instant live scans and graph re-clustering.
- **Interactive Repository Matcher**: Instant client-side scoring and recommendation engine built directly into the Canvas web application.
- **Responsive Layout**: Designed to adapt fluidly across varying Canvas panel widths.
- **Full Offline Portability**: Works offline with zero network dependency when loaded with synthetic datasets.

---

## Key Features

- Standard Library Python Implementation: Runs directly with Python 3.8+ without mandatory external pip dependencies.
- Dual Ingestion Modes: Works against the live GitHub REST API v3 or completely offline using synthetic JSON fixtures.
- Embedded Client-Side Scanner: The Canvas UI includes a live GitHub API scanner that can fetch public repositories and re-render the knowledge graph directly in the browser/iframe.
- Conversational Repository Matcher: Evaluates natural language queries to recommend best-suited codebases or report when requirements cannot be met.
- Intelligent Domain Clustering: Categorizes repositories into domains such as Core Services, Frontend UI, Data Engineering & AI/ML, Developer Tooling, DevOps & Infrastructure, Shared Libraries, and Documentation.
- Clean Architecture Knowledge Graph: Builds directed relationships between repositories with concise labels, detailed relationship descriptions, degree centrality scoring, and automated hub/bridge detection.
- Interactive Inspection Side Drawer: Slide-in panel displaying repository details, stars, forks, issues, language, topics, and clickable incoming/outgoing connections.
- Agent Skill Standard: Full compatibility with Gemini Enterprise App, Spark, Antigravity, Claude Code, Cursor, and standard Skill Plug-in architectures via `SKILL.md`.
- Fully Synthetic Test Suite: Includes realistic, non-PHI synthetic datasets and a complete automated unit test suite.

---

## Requirements

- Python 3.8 or higher.
- Standard Python libraries (`urllib`, `json`, `re`, `argparse`, `math`, `collections`, `os`, `sys`, `unittest`).
- Optional: `pytest` (if running tests via pytest instead of unittest).

---

## Configuration Guide

The file `scanner_config.json` is the primary configuration file:

```json
{
  "target_url": "https://github.com/terravic",
  "auth_token": "",
  "scan_options": {
    "include_forks": false,
    "include_archived": true,
    "max_repos": 100,
    "offline_fixture": "examples/synthetic_terravic_org.json"
  },
  "clustering_rules": [
    {
      "pattern": ".*-sdk|.*-client|.*-cli",
      "cluster_id": "developer-tooling"
    },
    {
      "pattern": ".*-gateway|.*-auth|.*-service|.*-engine",
      "cluster_id": "core-services"
    },
    {
      "pattern": ".*-portal|.*-app|.*-ui|.*-design",
      "cluster_id": "frontend-ui"
    },
    {
      "pattern": ".*-pipeline|.*-ai-.*|.*-analytics",
      "cluster_id": "data-analytics"
    },
    {
      "pattern": ".*-infra|.*-infrastructure",
      "cluster_id": "infrastructure-devops"
    },
    {
      "pattern": ".*-core-lib|.*-common|.*-utils",
      "cluster_id": "libraries-shared"
    },
    {
      "pattern": ".*-docs|.*-specs",
      "cluster_id": "documentation-specs"
    }
  ],
  "output": {
    "output_dir": "output",
    "generate_dashboard": true,
    "generate_markdown": true,
    "generate_json": true
  }
}
```

---

## Running the Python Code Directly

### 1. Quick Start with Offline Synthetic Data

```bash
# Run using the default configuration (points to synthetic dataset)
python3 scripts/cli.py --config scanner_config.json

# Or explicitly pass the synthetic fixture path
python3 scripts/cli.py --fixture examples/synthetic_terravic_org.json --output-dir output/
```

### 2. Scanning a Live GitHub Organization or User

```bash
# Scan using the command line flag
python3 scripts/cli.py --url https://github.com/terravic

# Scan with an authenticated token
python3 scripts/cli.py --url https://github.com/terravic --token ghp_yourPersonalAccessTokenHere
```

### 3. Querying the Knowledge Base via CLI

Search for the best-suited repository for any software request directly from the terminal:

```bash
# Query an existing knowledge base
python3 scripts/cli.py --query "Python client SDK for platform API"

# Query for user authentication
python3 scripts/cli.py --query "Where is OAuth2 and user login authentication handled?"

# Query for a non-matching capability
python3 scripts/cli.py --query "Blockchain cryptocurrency mining smart contract"
```

### 4. Scanning a Single Repository

```bash
python3 scripts/cli.py --url https://github.com/terravic/terravic-api-gateway
```

### 5. CLI Reference

```
usage: cli.py [-h] [--url URL] [--config CONFIG] [--fixture FIXTURE]
              [--output-dir OUTPUT_DIR] [--token TOKEN] [--max-repos MAX_REPOS]
              [--include-forks] [--query QUERY] [--kb KB] [--verbose]

Options:
  -h, --help            Show help message and exit
  --url URL, -u URL     GitHub URL or owner handle (e.g. 'https://github.com/terravic')
  --config CONFIG, -c CONFIG
                        Path to configuration JSON file (default: scanner_config.json)
  --fixture FIXTURE, -f FIXTURE
                        Path to offline synthetic dataset JSON
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Directory to save generated artifacts (default: output/)
  --token TOKEN, -t TOKEN
                        GitHub Personal Access Token (or GITHUB_TOKEN env variable)
  --max-repos MAX_REPOS Maximum repositories to scan (default: 100)
  --include-forks       Include forked repositories in scan
  --query QUERY, -q QUERY
                        Ask about a software need or program to find the best suited repository
  --kb KB               Path to knowledge_base.json for query resolution
  --verbose, -v         Enable verbose logging
```

### 6. Running Automated Tests

Run the complete test suite using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests -v
```

All 21 unit and integration tests verify URL parsing, metadata normalization, domain clustering, custom rules, graph construction, edge calculation, repository search engine, knowledge base generation, and HTML dashboard rendering.

---

## Architecture and Data Model

### Domain Taxonomy

| Domain ID | Domain Name | Typical Technologies / Keywords |
|---|---|---|
| `core-services` | Core Services & Backend APIs | Go, Python, gRPC, REST, FastAPI, microservices, auth, gateways, servers |
| `frontend-ui` | Frontend & User Interfaces | TypeScript, React, Next.js, Vue, Tailwind CSS, dashboards, web portals, mobile apps |
| `data-analytics` | Data Engineering & AI/ML | Python, Spark, Kafka, ETL, ClickHouse, PyTorch, LLM, embeddings, vector search |
| `developer-tooling` | Developer Tooling & SDKs | TypeScript, Python, Go, SDKs, CLI utilities, linters, test harnesses, code generators |
| `infrastructure-devops` | Infrastructure & DevOps | HCL, Terraform, Kubernetes, Helm, Docker, CI/CD, GitOps, ArgoCD |
| `libraries-shared` | Shared Libraries & Utilities | Proto definitions, common utilities, shared logging, telemetry, base schemas |
| `documentation-specs` | Documentation & Specifications | Markdown, OpenAPI, RFCs, architectural decision records, technical guides |

---

### Knowledge Graph Schema

#### Node Properties

```json
{
  "id": 101,
  "name": "terravic-api-gateway",
  "full_name": "terravic/terravic-api-gateway",
  "html_url": "https://github.com/terravic/terravic-api-gateway",
  "description": "High-performance edge reverse proxy and authentication gateway routing traffic to core microservices.",
  "primary_language": "Go",
  "topics": ["api-gateway", "reverse-proxy", "auth", "grpc"],
  "tech_stack": ["Go", "gRPC", "Redis", "Docker"],
  "stars": 482,
  "forks": 65,
  "open_issues": 12,
  "cluster_id": "core-services",
  "cluster_name": "Core Services & Backend APIs",
  "cluster_color": "#3B82F6",
  "in_degree": 4,
  "out_degree": 3,
  "total_degree": 7,
  "centrality_score": 0.50,
  "is_hub": true,
  "is_bridge": true
}
```

#### Edge Properties

```json
{
  "source": 105,
  "target": 110,
  "type": "depends_on",
  "label": "Consumes SDK",
  "description": "terravic-web-portal uses terravic-js-sdk for API integration.",
  "weight": 2.0,
  "is_cross_cluster": true,
  "source_cluster": "frontend-ui",
  "target_cluster": "developer-tooling"
}
```

---

### Centrality and Hub Classification

- **Degree Centrality**: Calculated as `total_connections / (total_repositories - 1)`.
- **Architecture Hubs (`is_hub`)**: Repositories in the top 30% of total degree distribution (or degree >= 4), representing critical infrastructure or libraries upon which many other repositories depend.
- **Cross-Domain Bridges (`is_bridge`)**: Repositories that connect two or more distinct functional clusters.

---

## Interactive Canvas UI Elements

The generated Canvas UI (`output/dashboard.html`) provides the following interactive controls:

1. **Top Action & Ingestion Bar**:
   - Live URL text field and `Scan Address` button.
   - Preset selector (Synthetic Platform, Pallets, FastAPI, Current Dataset).
   - Theme toggle (Slate Dark / Clean Light).
   - `Export JSON` and `Print View` buttons.
2. **Repository Matcher & Chat Tab**:
   - Natural language search box for querying software capabilities.
   - Clickable suggestion chips.
   - Ranked result card with match score, confidence, reasoning, and "Locate on Knowledge Graph" button.
3. **Metric Summary Counters**:
   - Live counters for Total Repositories, Domain Clusters, Graph Relationships, Aggregate Stars, and Architectural Hubs.
4. **Knowledge Graph Canvas (D3 Force Simulation)**:
   - Dynamic zoom, pan, and smooth node dragging.
   - Nodes color-coded by domain cluster.
   - Directed relationship edges with dashed styling for cross-domain boundaries.
   - Live search filter with auto-dimming of non-matching nodes.
   - Domain filter dropdown and relationship filter dropdown.
   - Physics pause and resume toggle.
5. **Deep Inspection Side Drawer**:
   - Selecting any node opens a right drawer detailing the repository's description, technology stack, star count, language, incoming consumers, and outgoing dependencies.
   - Clicking any connection in the drawer automatically navigates to and focuses the connected node.
6. **Cluster Explorer Tab**:
   - Grid of interactive cards for each domain with expandable repository lists.
7. **Repository Catalog Data Table**:
   - Searchable and sortable spreadsheet table of all repositories.
8. **Cross-Domain Flow Matrix & Raw JSON Tab**:
   - Inter-cluster connectivity matrix and raw JSON inspector with clipboard copy utility.

---

## Security and Synthetic Data Compliance

- **No PHI/PII**: All sample files in `examples/` and test suites use 100% synthetic, fictional project names, repositories, and documentation. No Protected Health Information (PHI) or Personally Identifiable Information (PII) is included.
- **Token Protection**: Configuration files and CLI flags sanitize tokens from output logs. Tokens are only passed as authorization headers directly to the standard GitHub REST API endpoint over HTTPS.
- **Offline Capable**: The skill can operate completely disconnected from external networks when provided an offline fixture JSON.

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for the full license text and terms.
