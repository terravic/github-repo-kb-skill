---
name: github-repo-kb
description: >-
  Analyzes any GitHub organization, user, or repository URL to construct a thematic domain-clustered
  knowledge base, architecture knowledge graph, interactive Canvas UI dashboard, and conversational repository search.
---

# GitHub Repository Knowledge Base and Canvas UI Skill

## Overview

The `github-repo-kb` skill provides automated thematic analysis of GitHub organizations, user profiles, or repository collections. It ingests repository metadata, clusters codebases into functional thematic domains (such as Medical & Healthcare, Life Sciences & Bioinformatics, Finance & Billing, Security & Identity, AI/ML, Developer Tooling, Infrastructure, and Shared Utilities), computes architectural relationships into a directed knowledge graph, and generates structured knowledge base documentation alongside a native HTML/JS Canvas UI dashboard.

In addition to visual analysis, the skill provides interactive repository query capabilities allowing users to ask questions about specific software programs, clinical systems, scientific tools, or platform capabilities in the organization and receive ranked recommendations.

This skill is engineered for seamless execution across agent harnesses including Gemini Enterprise App, Spark, Antigravity, Claude Code, Cursor, and custom skill plug-in runners supporting Canvas iframe and webview rendering.

---

## Canvas UI and Output Deliverables

The skill generates the following deliverables in the designated output directory (default: `output/`):

1. `dashboard.html` (Canvas UI Application):
   - Native HTML/CSS/JavaScript application designed for direct iframe rendering inside Canvas.
   - Interactive Address Bar: Non-technical users can type or paste any GitHub URL directly into the Canvas header and trigger real-time scanning and thematic clustering.
   - Repository Matcher & Chat Tab: Interactive capability search tool where users can type any software need and find the best-suited repository with confidence scores and reasoning.
   - Preset Switcher: Instant toggling between synthetic demonstration datasets and public organizations.
   - Dynamic D3.js Knowledge Graph: Force-directed graph with thematic cluster filtering, relationship toggles, live search, node dragging, and physics pause/resume.
   - Deep Inspection Side Drawer: Slide-in panel displaying repository descriptions, star counts, languages, topics, incoming consumers, and outgoing dependencies.
   - Expandable Cluster Explorer: Interactive cards breaking down thematic domains and repository rosters.
   - Searchable Data Table: Multi-column sorting and filtering by domain and language.
   - Cross-Domain Flow Matrix: Inter-cluster connectivity matrix.
   - Theme Switcher: Slate Dark and Clean Light themes.

2. `knowledge_base.json`:
   - Machine-readable database containing normalized repository metadata, thematic domain taxonomy assignments, node-link graph data, and inter-cluster connectivity matrices.

3. `KNOWLEDGE_BASE.md`:
   - Formatted Markdown report containing executive summary tables, thematic cluster breakdowns, architectural relationships, and modularity recommendations.

4. `knowledge_graph.json`:
   - Dedicated node-link graph specification formatted for D3.js, Cytoscape, Vis.js, and NetworkX.

---

## Agent Execution Workflow

### Step 1: Scan and Ingest Target

Determine the target from the user prompt or configuration and execute the pipeline:

```bash
# Scan a live GitHub organization or user
python3 scripts/cli.py --url https://github.com/TARGET_ORG_OR_USER

# Scan using configuration file
python3 scripts/cli.py --config scanner_config.json

# Run offline synthetic demonstration
python3 scripts/cli.py --fixture examples/synthetic_sample_org.json --output-dir output/
```

Provide a clickable file link to `output/dashboard.html` for Canvas rendering, along with an executive summary in the chat response.

### Step 2: Conversational Repository Search and Question Answering

When a user asks about a specific program, library, capability, or software need in the scanned organization (e.g. *"Which repo handles patient medical records?"*, *"Where is genomics DNA sequencing done?"*, *"Do you have a Python SDK for automation?"*):

1. Execute the query engine via the CLI or Python module:
   ```bash
   python3 scripts/cli.py --query "user software requirement query here"
   ```
2. Respond to the user with a structured answer:
   - **If a matching repository is found**:
     - State the best-suited repository name, direct link, primary language, and thematic domain cluster.
     - Explain why this repository fits the user's need based on its code, topics, and description.
     - Mention alternative candidates if applicable.
   - **If no repository matches the query**:
     - Clearly state that no repository in the scanned organization meets the requested requirement.
     - List the available thematic domain clusters in the organization to guide the user to existing capabilities.

---

## Configuration Schema (`scanner_config.json`)

The scanner configuration file allows users to edit target URLs, rate limit tokens, scan parameters, and custom thematic clustering regex rules:

```json
{
  "target_url": "https://github.com/pallets",
  "auth_token": "",
  "scan_options": {
    "include_forks": false,
    "include_archived": true,
    "max_repos": 100,
    "offline_fixture": ""
  },
  "clustering_rules": [
    {
      "pattern": ".*-patient|.*-ehr|.*-medical",
      "cluster_id": "medical-healthcare"
    },
    {
      "pattern": ".*-genomics|.*-bio.*|.*-trials",
      "cluster_id": "life-sciences-bio"
    },
    {
      "pattern": ".*-billing|.*-payment",
      "cluster_id": "finance-billing"
    },
    {
      "pattern": ".*-auth|.*-identity|.*-security",
      "cluster_id": "security-identity"
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

## Canvas UI Interaction Reference

When rendered in Canvas:
- **Thematic Cluster Explorer**: View dedicated cards for Medical & Healthcare, Life Sciences & Bioinformatics, Finance, Security, AI/ML, Tooling, and Infrastructure.
- **Repository Matcher Tab**: Type any functional query (e.g., *"FHIR patient records"*, *"DNA sequencing"*, *"OAuth2 authentication"*) to immediately view matched repositories and click **Locate on Knowledge Graph** to focus that node.
- **Change Target URL**: Users can type any organization or repository URL into the top search bar and click `Scan Address` to reload the Canvas view.
- **Node Selection**: Clicking any node opens the inspection drawer showing architectural details and connected repositories.
- **Filtering**: Use the Cluster and Relationship dropdowns to isolate subsets of the architecture.
- **Data Export**: Click `Export JSON` to download the active dataset or `Copy JSON` in the Raw Data tab.
