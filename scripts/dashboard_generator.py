"""
Interactive Canvas UI Dashboard Generator.

Generates a standalone, highly interactive HTML5 Canvas application with dynamic D3.js
force-directed knowledge graphs, expandable cluster cards, searchable repository
data tables, deep inspection drawers, a built-in client-side scanner, and an intelligent
Repository Matcher & Search Assistant.
"""

import json
import os
from typing import Any, Dict


class DashboardGenerator:
    """Generates an interactive HTML5 Canvas UI dashboard."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir

    def generate(
        self,
        metadata: Dict[str, Any],
        clusters_data: Dict[str, Any],
        graph_data: Dict[str, Any],
    ) -> str:
        """
        Produce standalone dashboard.html tailored for Canvas iframe and browser rendering.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        dashboard_path = os.path.join(self.output_dir, "dashboard.html")

        embedded_payload = {
            "metadata": metadata,
            "clusters": clusters_data.get("clusters", []),
            "repositories": clusters_data.get("repositories", []),
            "graph": {
                "nodes": graph_data.get("nodes", []),
                "links": graph_data.get("edges", []),
                "connectivity_matrix": graph_data.get("cluster_connectivity_matrix", {}),
                "hub_repositories": graph_data.get("hub_repositories", []),
                "bridge_repositories": graph_data.get("bridge_repositories", []),
                "cross_cluster_count": graph_data.get("cross_cluster_edges_count", 0),
                "intra_cluster_count": graph_data.get("intra_cluster_edges_count", 0),
            },
        }

        html_content = self._build_html(embedded_payload)
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return dashboard_path

    def _build_html(self, data: Dict[str, Any]) -> str:
        json_data_str = json.dumps(data)
        owner_name = data.get("metadata", {}).get("owner", "Repository Organization")
        target_url = data.get("metadata", {}).get("input_url", "GitHub Target")

        template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Repository Knowledge Base & Architecture Canvas - __OWNER_NAME__</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    :root {
      --bg-base: #0f172a;
      --bg-surface: #1e293b;
      --bg-surface-elevated: #334155;
      --bg-surface-subtle: rgba(30, 41, 59, 0.7);
      --border-color: #334155;
      --border-hover: #475569;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #06b6d4;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    [data-theme="light"] {
      --bg-base: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #f1f5f9;
      --bg-surface-subtle: rgba(241, 245, 249, 0.8);
      --border-color: #e2e8f0;
      --border-hover: #cbd5e1;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #94a3b8;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.5;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;
      background-color: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 50;
      gap: 16px;
      flex-wrap: wrap;
    }

    .topbar-brand {
      display: flex;
      flex-direction: column;
    }

    .topbar-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }

    .topbar-subtitle {
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .scan-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      background-color: var(--bg-base);
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      flex: 1;
      max-width: 520px;
    }

    .scan-input {
      flex: 1;
      background: none;
      border: none;
      color: var(--text-main);
      font-size: 0.85rem;
      font-family: var(--font-mono);
      outline: none;
      padding: 4px 6px;
    }

    .scan-input::placeholder {
      color: var(--text-dim);
    }

    .btn {
      padding: 6px 12px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 5px;
      border: 1px solid var(--border-color);
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }

    .btn:hover {
      background-color: var(--border-hover);
      border-color: var(--text-muted);
    }

    .btn-primary {
      background-color: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }

    .btn-primary:hover {
      background-color: var(--primary-hover);
      border-color: var(--primary-hover);
    }

    .btn-sm {
      padding: 4px 8px;
      font-size: 0.75rem;
    }

    .topbar-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      padding: 16px 20px;
    }

    .metric-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-sm);
      transition: transform 0.15s, border-color 0.15s;
    }

    .metric-card:hover {
      border-color: var(--primary);
      transform: translateY(-2px);
    }

    .metric-label {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 4px;
    }

    .metric-value {
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.1;
    }

    .metric-subtext {
      font-size: 0.72rem;
      color: var(--text-dim);
      margin-top: 4px;
    }

    .main-container {
      padding: 0 20px 30px;
      flex: 1;
    }

    .nav-tabs {
      display: flex;
      gap: 6px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 16px;
      overflow-x: auto;
    }

    .tab-btn {
      padding: 8px 16px;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: var(--text-main);
    }

    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }

    .tab-pane {
      display: none;
    }

    .tab-pane.active {
      display: block;
    }

    /* Graph Section */
    .graph-layout {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 16px;
      height: 700px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
      position: relative;
    }

    @media (max-width: 900px) {
      .graph-layout {
        grid-template-columns: 1fr;
        height: auto;
      }
    }

    .graph-canvas-container {
      position: relative;
      width: 100%;
      height: 100%;
      min-height: 500px;
      background: radial-gradient(circle at center, var(--bg-surface-elevated) 0%, var(--bg-base) 100%);
      overflow: hidden;
    }

    .graph-controls {
      position: absolute;
      top: 12px;
      left: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      background-color: var(--bg-surface-subtle);
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      z-index: 10;
      backdrop-filter: blur(8px);
    }

    .graph-controls select, .graph-controls input {
      padding: 5px 8px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 4px;
      font-size: 0.78rem;
    }

    svg.graph-svg {
      width: 100%;
      height: 100%;
      cursor: grab;
    }

    svg.graph-svg:active {
      cursor: grabbing;
    }

    .graph-link {
      stroke: #64748b;
      stroke-opacity: 0.5;
      transition: stroke-opacity 0.2s, stroke-width 0.2s;
    }

    .graph-link.cross-cluster {
      stroke: #94a3b8;
      stroke-dasharray: 4, 3;
    }

    .graph-link.highlighted {
      stroke: #38bdf8 !important;
      stroke-opacity: 1 !important;
      stroke-width: 2.5px !important;
    }

    .graph-node {
      cursor: pointer;
      transition: transform 0.2s;
    }

    .graph-node circle {
      stroke-width: 2px;
      transition: all 0.2s;
    }

    .graph-node text {
      font-size: 11px;
      fill: var(--text-main);
      pointer-events: none;
      font-family: var(--font-mono);
      font-weight: 500;
    }

    .graph-node.dimmed {
      opacity: 0.15;
    }

    .graph-link.dimmed {
      opacity: 0.05;
    }

    .graph-node.active circle {
      stroke: #ffffff;
      stroke-width: 3.5px;
      filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.8));
    }

    .graph-sidebar {
      background-color: var(--bg-surface);
      border-left: 1px solid var(--border-color);
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .drawer-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      color: var(--text-dim);
      font-size: 0.85rem;
      padding: 20px;
      line-height: 1.4;
    }

    .badge {
      display: inline-block;
      padding: 2px 7px;
      font-size: 0.72rem;
      font-weight: 600;
      border-radius: 4px;
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      border: 1px solid var(--border-color);
    }

    .tag {
      display: inline-block;
      padding: 2px 6px;
      font-size: 0.68rem;
      border-radius: 3px;
      background-color: var(--bg-surface-elevated);
      color: #93c5fd;
      margin: 2px;
      font-family: var(--font-mono);
      border: 1px solid var(--border-color);
    }

    /* Query Matcher Tab */
    .matcher-container {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      box-shadow: var(--shadow-sm);
    }

    .matcher-search-box {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .matcher-input {
      flex: 1;
      padding: 10px 14px;
      background-color: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 0.95rem;
    }

    .chips-container {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .chip-btn {
      padding: 4px 10px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      color: var(--text-muted);
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .chip-btn:hover {
      background-color: var(--border-hover);
      color: var(--text-main);
      border-color: var(--primary);
    }

    .matcher-result-card {
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    /* Cluster Cards Grid */
    .cluster-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
    }

    .cluster-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      cursor: pointer;
      transition: all 0.15s ease;
      border-left-width: 4px;
      box-shadow: var(--shadow-sm);
    }

    .cluster-card:hover {
      border-color: var(--text-muted);
      transform: translateY(-2px);
    }

    .cluster-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .cluster-card-title {
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .cluster-card-desc {
      font-size: 0.82rem;
      color: var(--text-muted);
    }

    .cluster-card-stats {
      display: flex;
      gap: 14px;
      font-size: 0.78rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border-color);
      padding-top: 10px;
    }

    .cluster-repos-list {
      display: none;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px dashed var(--border-color);
    }

    .cluster-card.expanded .cluster-repos-list {
      display: block;
    }

    .cluster-repo-item {
      font-size: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 8px;
      background: var(--bg-surface-elevated);
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.15s ease;
    }

    .cluster-repo-item:hover {
      background: var(--border-hover);
      color: var(--primary);
    }

    /* Repository Data Table */
    .table-container {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow-x: auto;
      box-shadow: var(--shadow-sm);
    }

    .table-controls {
      padding: 12px 16px;
      display: flex;
      gap: 10px;
      border-bottom: 1px solid var(--border-color);
      flex-wrap: wrap;
    }

    .table-search {
      flex: 1;
      min-width: 220px;
      padding: 6px 10px;
      background-color: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 5px;
      color: var(--text-main);
      font-size: 0.85rem;
    }

    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      text-align: left;
    }

    table.data-table th {
      background-color: var(--bg-surface-elevated);
      padding: 10px 14px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      cursor: pointer;
      user-select: none;
    }

    table.data-table th:hover {
      color: var(--text-main);
    }

    table.data-table td {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
    }

    table.data-table tr:hover td {
      background-color: var(--bg-surface-elevated);
    }

    /* Matrix Table */
    .matrix-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      margin-top: 14px;
    }

    .matrix-table th, .matrix-table td {
      border: 1px solid var(--border-color);
      padding: 8px;
      text-align: center;
    }

    .matrix-table th {
      background-color: var(--bg-surface-elevated);
      color: var(--text-muted);
    }

    .matrix-cell-active {
      background-color: rgba(59, 130, 246, 0.2);
      color: #93c5fd;
      font-weight: 700;
      cursor: pointer;
    }

    .matrix-cell-active:hover {
      background-color: rgba(59, 130, 246, 0.4);
      color: #ffffff;
    }

    .graph-tooltip {
      position: absolute;
      padding: 8px 12px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 0.78rem;
      pointer-events: none;
      z-index: 100;
      max-width: 260px;
      box-shadow: var(--shadow-lg);
    }

    .toast-msg {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      padding: 10px 16px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-lg);
      z-index: 999;
      font-size: 0.82rem;
      display: none;
    }
  </style>
</head>
<body>

  <!-- Top Navigation & Scanning Bar -->
  <header class="topbar">
    <div class="topbar-brand">
      <div class="topbar-title">Repository Architecture Canvas</div>
      <div class="topbar-subtitle" id="active-target-display">Target: __TARGET_URL__</div>
    </div>

    <!-- Live Address Scan Input -->
    <div class="scan-bar">
      <input type="text" id="scan-target-input" class="scan-input" value="__TARGET_URL__" placeholder="Enter GitHub Org or Repo URL (e.g. github.com/pallets)" onkeydown="if(event.key==='Enter') scanAddressInput();" />
      <button class="btn btn-primary btn-sm" onclick="scanAddressInput()">Scan Address</button>
    </div>

    <div class="topbar-actions">
      <select id="preset-selector" class="btn btn-sm" onchange="onPresetChange(this.value)">
        <option value="current">Current Dataset</option>
        <option value="synthetic">Synthetic Platform (15 Repos)</option>
        <option value="pallets">Pallets Org (Flask, Click, Jinja)</option>
        <option value="fastapi">FastAPI Ecosystem</option>
      </select>
      <button class="btn btn-sm" onclick="toggleTheme()">Theme</button>
      <button class="btn btn-sm" onclick="exportDataJson()">Export JSON</button>
      <button class="btn btn-primary btn-sm" onclick="window.print()">Print View</button>
    </div>
  </header>

  <!-- Metric Summary Cards -->
  <section class="metric-grid" id="metric-summary-container">
    <!-- Populated dynamically -->
  </section>

  <!-- Main Container with Tabs -->
  <main class="main-container">
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-graph')">Knowledge Graph</button>
      <button class="tab-btn" onclick="switchTab('tab-matcher')">Repository Matcher & Chat</button>
      <button class="tab-btn" onclick="switchTab('tab-clusters')">Cluster Explorer</button>
      <button class="tab-btn" onclick="switchTab('tab-repos')">Repository Catalog</button>
      <button class="tab-btn" onclick="switchTab('tab-matrix')">Cross-Domain Flow</button>
      <button class="tab-btn" onclick="switchTab('tab-raw')">Raw JSON & Config</button>
    </div>

    <!-- TAB 1: KNOWLEDGE GRAPH -->
    <div id="tab-graph" class="tab-pane active">
      <div class="graph-layout">
        <div class="graph-canvas-container" id="graph-container">
          <div class="graph-controls">
            <input type="text" id="graph-search" placeholder="Search node or tech..." oninput="onGraphSearch(this.value)" />
            <select id="graph-cluster-filter" onchange="onClusterFilterChange(this.value)">
              <option value="all">All Clusters</option>
            </select>
            <select id="graph-edge-filter" onchange="onEdgeFilterChange(this.value)">
              <option value="all">All Relationships</option>
              <option value="depends_on">Dependencies Only</option>
              <option value="cross_cluster">Cross-Cluster Only</option>
              <option value="shares_tech">Shared Tech Stack</option>
            </select>
            <button class="btn btn-sm" onclick="resetGraphView()">Reset View</button>
            <button class="btn btn-sm" id="btn-toggle-physics" onclick="togglePhysics()">Pause Physics</button>
          </div>
          <svg class="graph-svg" id="graph-svg"></svg>
          <div class="graph-tooltip" id="graph-tooltip" style="display: none;"></div>
        </div>

        <div class="graph-sidebar" id="graph-sidebar">
          <div class="drawer-empty">
            Select any node or repository in the graph to inspect architectural dependencies, technology stack, and cluster connections.
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: REPOSITORY MATCHER & CHAT -->
    <div id="tab-matcher" class="tab-pane">
      <div class="matcher-container">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px;">Repository Matcher & Capability Search</h2>
          <p style="font-size: 0.85rem; color: var(--text-muted);">
            Describe what program, library, or software functionality you need. The matcher will evaluate all repositories in this organization to find the best match or report if none fits.
          </p>
        </div>

        <div class="matcher-search-box">
          <input type="text" id="matcher-query-input" class="matcher-input" placeholder="e.g., 'Python SDK for platform API', 'OAuth2 authentication service', 'Video transcoding'..." onkeydown="if(event.key==='Enter') executeMatcherQuery();" />
          <button class="btn btn-primary" onclick="executeMatcherQuery()">Find Best Repository</button>
        </div>

        <div class="chips-container">
          <span style="font-size: 0.78rem; color: var(--text-dim);">Suggestions:</span>
          <button class="chip-btn" onclick="setQueryChip('Python client SDK for API automation')">Python Client SDK</button>
          <button class="chip-btn" onclick="setQueryChip('OAuth2 and user login authentication service')">User Authentication</button>
          <button class="chip-btn" onclick="setQueryChip('React UI web portal and dashboard')">Frontend Portal</button>
          <button class="chip-btn" onclick="setQueryChip('Real-time Kafka data ingestion pipeline')">Kafka Streaming ETL</button>
          <button class="chip-btn" onclick="setQueryChip('Terraform and Kubernetes infrastructure')">Terraform DevOps</button>
          <button class="chip-btn" onclick="setQueryChip('Blockchain cryptocurrency mining smart contract')">Crypto Mining (Non-matching demo)</button>
        </div>

        <div id="matcher-result-area">
          <div style="text-align: center; color: var(--text-dim); padding: 30px; font-size: 0.88rem;">
            Type a capability request above or click a suggestion chip to find the best-suited repository.
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: CLUSTERS EXPLORER -->
    <div id="tab-clusters" class="tab-pane">
      <div class="cluster-grid" id="cluster-cards-container">
        <!-- Populated by JS -->
      </div>
    </div>

    <!-- TAB 4: REPOSITORY CATALOG -->
    <div id="tab-repos" class="tab-pane">
      <div class="table-container">
        <div class="table-controls">
          <input type="text" class="table-search" id="repo-table-search" placeholder="Filter repositories by name, language, or topic..." oninput="filterRepoTable()" />
          <select id="table-cluster-filter" onchange="filterRepoTable()" class="table-search" style="max-width: 200px;">
            <option value="all">All Clusters</option>
          </select>
        </div>
        <table class="data-table" id="repo-data-table">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Repository</th>
              <th onclick="sortTable(1)">Cluster</th>
              <th onclick="sortTable(2)">Language</th>
              <th onclick="sortTable(3)">Stars</th>
              <th onclick="sortTable(4)">Connections</th>
              <th onclick="sortTable(5)">Role</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="repo-table-body">
            <!-- Populated by JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 5: CROSS-DOMAIN FLOW MATRIX -->
    <div id="tab-matrix" class="tab-pane">
      <div style="background-color: var(--bg-surface); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color);">
        <h3 style="margin-bottom: 8px; font-size: 1.1rem;">Inter-Cluster Architecture Connectivity Matrix</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 16px;">
          Rows represent source domain origins; columns represent target domain interfaces. Click any active cell to filter connections on the graph.
        </p>
        <div id="matrix-container" style="overflow-x: auto;">
          <!-- Populated by JS -->
        </div>
      </div>
    </div>

    <!-- TAB 6: RAW JSON & CONFIG -->
    <div id="tab-raw" class="tab-pane">
      <div style="background-color: var(--bg-surface); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 1.1rem;">Raw Knowledge Base Payload</h3>
          <button class="btn btn-sm btn-primary" onclick="copyRawJson()">Copy JSON</button>
        </div>
        <textarea id="raw-json-viewer" readonly style="width: 100%; height: 420px; font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-base); color: var(--text-main); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px;"></textarea>
      </div>
    </div>
  </main>

  <div id="toast" class="toast-msg"></div>

  <script>
    let KB_DATA = __EMBEDDED_JSON__;
    let INITIAL_KB_DATA = JSON.parse(JSON.stringify(KB_DATA));

    let simulation;
    let svg, gLinks, gNodes, linkElements, nodeElements;
    let selectedNodeId = null;
    let isPhysicsPaused = false;
    let activeClusterFilter = 'all';
    let activeEdgeFilter = 'all';

    const GENERIC_TERMS = new Set([
      "service", "engine", "system", "app", "application", "platform",
      "manager", "data", "tool", "module", "base", "core", "handler", "worker"
    ]);

    const STOP_WORDS = new Set([
      "a", "an", "the", "in", "on", "of", "for", "to", "with", "and", "or",
      "is", "are", "do", "does", "have", "has", "want", "need", "looking",
      "find", "which", "repo", "repository", "software", "program", "code",
      "project", "i", "we", "can", "should", "me", "there", "any", "best",
      "tell", "show", "give", "help", "about", "handling", "suited"
    ]);

    document.addEventListener('DOMContentLoaded', () => {
      refreshAllViews();
    });

    function resetSidebarDrawer() {
      selectedNodeId = null;
      const sidebar = document.getElementById('graph-sidebar');
      if (sidebar) {
        sidebar.innerHTML = `
          <div class="drawer-empty">
            Select any node or repository in the graph to inspect architectural dependencies, technology stack, and cluster connections.
          </div>
        `;
      }
      if (nodeElements) nodeElements.classed('active', false);
      if (linkElements) linkElements.classed('highlighted', false);
    }

    function refreshAllViews() {
      resetSidebarDrawer();
      renderMetricSummary();
      initGraph();
      renderClusterCards();
      renderRepoTable();
      renderMatrix();
      populateDropdowns();
      const rawViewer = document.getElementById('raw-json-viewer');
      if (rawViewer) {
        rawViewer.value = JSON.stringify(KB_DATA, null, 2);
      }
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId));
      if (activeBtn) activeBtn.classList.add('active');
      const pane = document.getElementById(tabId);
      if (pane) pane.classList.add('active');

      if (tabId === 'tab-graph' && simulation) {
        simulation.alpha(0.3).restart();
      }
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      showToast('Theme switched to ' + next);
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      if (!t) return;
      t.textContent = msg;
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 2500);
    }

    function renderMetricSummary() {
      const meta = KB_DATA.metadata || {};
      const summary = KB_DATA.graph || {};
      const repos = KB_DATA.repositories || [];
      const clusters = KB_DATA.clusters || [];

      const totalStars = repos.reduce((sum, r) => sum + (r.stars || 0), 0);

      const items = [
        { label: 'Total Repositories', val: repos.length, sub: 'Active codebases' },
        { label: 'Domain Clusters', val: clusters.length, sub: 'Functional partitions' },
        { label: 'Graph Relationships', val: (summary.links || []).length, sub: (summary.cross_cluster_count || 0) + ' cross-cluster' },
        { label: 'Aggregate Stars', val: totalStars.toLocaleString(), sub: 'GitHub community' },
        { label: 'Hub Architectures', val: (summary.hub_repositories || []).length, sub: 'Central dependencies' }
      ];

      const container = document.getElementById('metric-summary-container');
      if (container) {
        container.innerHTML = items.map(it => `
          <div class="metric-card">
            <div class="metric-label">${it.label}</div>
            <div class="metric-value">${it.val}</div>
            <div class="metric-subtext">${it.sub}</div>
          </div>
        `).join('');
      }
    }

    function populateDropdowns() {
      const clusterSelectGraph = document.getElementById('graph-cluster-filter');
      const clusterSelectTable = document.getElementById('table-cluster-filter');

      if (clusterSelectGraph) {
        clusterSelectGraph.innerHTML = '<option value="all">All Clusters</option>';
        (KB_DATA.clusters || []).forEach(c => {
          const opt1 = document.createElement('option');
          opt1.value = c.id;
          opt1.textContent = c.name;
          clusterSelectGraph.appendChild(opt1);
        });
      }

      if (clusterSelectTable) {
        clusterSelectTable.innerHTML = '<option value="all">All Clusters</option>';
        (KB_DATA.clusters || []).forEach(c => {
          const opt2 = document.createElement('option');
          opt2.value = c.id;
          opt2.textContent = c.name;
          clusterSelectTable.appendChild(opt2);
        });
      }
    }

    /* D3.js Force Directed Graph */
    function initGraph() {
      const container = document.getElementById('graph-container');
      if (!container) return;
      const width = container.clientWidth || 800;
      const height = container.clientHeight || 700;

      d3.select('#graph-svg').selectAll('*').remove();

      const rawNodes = (KB_DATA.graph.nodes || []).map(d => Object.assign({}, d));
      const rawLinks = (KB_DATA.graph.links || []).map(d => Object.assign({}, d));

      svg = d3.select('#graph-svg')
        .attr('viewBox', [0, 0, width, height]);

      const g = svg.append('g');

      const zoom = d3.zoom()
        .scaleExtent([0.2, 5])
        .on('zoom', (event) => g.attr('transform', event.transform));
      svg.call(zoom);

      svg.append('defs').selectAll('marker')
        .data(['arrow-default', 'arrow-cross'])
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 22)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => d === 'arrow-cross' ? '#94a3b8' : '#64748b');

      gLinks = g.append('g').attr('class', 'links');
      gNodes = g.append('g').attr('class', 'nodes');

      simulation = d3.forceSimulation(rawNodes)
        .force('link', d3.forceLink(rawLinks).id(d => d.id).distance(d => d.is_cross_cluster ? 130 : 80))
        .force('charge', d3.forceManyBody().strength(-260))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => (d.is_hub ? 32 : 22)));

      linkElements = gLinks.selectAll('line')
        .data(rawLinks)
        .enter().append('line')
        .attr('class', d => 'graph-link ' + (d.is_cross_cluster ? 'cross-cluster' : ''))
        .attr('stroke-width', d => Math.max(1.2, d.weight || 1))
        .attr('marker-end', d => d.is_cross_cluster ? 'url(#arrow-cross)' : 'url(#arrow-default)');

      nodeElements = gNodes.selectAll('g')
        .data(rawNodes)
        .enter().append('g')
        .attr('class', 'graph-node')
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        )
        .on('click', (event, d) => selectNode(d.id))
        .on('mouseover', handleNodeMouseOver)
        .on('mouseout', handleNodeMouseOut);

      nodeElements.append('circle')
        .attr('r', d => d.is_hub ? 16 : (d.is_bridge ? 13 : 10))
        .attr('fill', d => d.cluster_color || '#3b82f6')
        .attr('stroke', d => d.is_hub ? '#fbbf24' : '#1e293b');

      nodeElements.append('text')
        .attr('dy', d => (d.is_hub ? 26 : 20))
        .attr('text-anchor', 'middle')
        .text(d => d.name);

      simulation.on('tick', () => {
        linkElements
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodeElements
          .attr('transform', d => `translate(${d.x},${d.y})`);
      });

      function dragstarted(event, d) {
        if (!event.active && !isPhysicsPaused) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active && !isPhysicsPaused) simulation.alphaTarget(0);
        if (!isPhysicsPaused) {
          d.fx = null;
          d.fy = null;
        }
      }
    }

    function handleNodeMouseOver(event, d) {
      const tooltip = document.getElementById('graph-tooltip');
      if (!tooltip) return;
      tooltip.style.display = 'block';
      tooltip.style.left = (event.pageX + 15) + 'px';
      tooltip.style.top = (event.pageY - 10) + 'px';
      tooltip.innerHTML = `
        <div style="font-weight: 700; color: #38bdf8; margin-bottom: 2px;">${d.name}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">${d.cluster_name}</div>
        <div style="font-size: 0.75rem; line-height: 1.3;">${d.description || 'No description'}</div>
        <div style="margin-top: 6px; font-size: 0.7rem; color: var(--text-dim);">Connections: ${d.total_degree || 0}</div>
      `;
    }

    function handleNodeMouseOut() {
      const tooltip = document.getElementById('graph-tooltip');
      if (tooltip) tooltip.style.display = 'none';
    }

    function selectNode(nodeId) {
      selectedNodeId = nodeId;
      const node = (KB_DATA.graph.nodes || []).find(n => String(n.id) === String(nodeId) || n.name === nodeId);
      if (!node) return;

      const targetActualId = node.id;

      if (nodeElements) {
        nodeElements.classed('active', d => String(d.id) === String(targetActualId));
      }
      if (linkElements) {
        linkElements.classed('highlighted', d => {
          const sId = String(d.source.id || d.source);
          const tId = String(d.target.id || d.target);
          const cId = String(targetActualId);
          return (sId === cId || tId === cId);
        });
      }

      const sidebar = document.getElementById('graph-sidebar');
      if (!sidebar) return;

      const incoming = (KB_DATA.graph.links || []).filter(l => String(l.target.id || l.target) === String(targetActualId));
      const outgoing = (KB_DATA.graph.links || []).filter(l => String(l.source.id || l.source) === String(targetActualId));

      const outgoingHtml = outgoing.length === 0 
        ? '<div style="font-size: 0.75rem; color: var(--text-dim);">No outgoing dependencies</div>'
        : outgoing.map(l => {
            const targetName = (l.target.name || l.target);
            const targetId = (l.target.id || l.target);
            return `<div onclick="focusNodeOnGraph('${targetId}')" style="cursor: pointer; padding: 6px; background: var(--bg-surface-elevated); border-radius: 4px; font-size: 0.78rem;">
              <span style="color: var(--primary);">&rarr; ${targetName}</span>
              <div style="color: var(--text-dim); font-size: 0.7rem;">${l.label || l.type}</div>
            </div>`;
          }).join('');

      const incomingHtml = incoming.length === 0 
        ? '<div style="font-size: 0.75rem; color: var(--text-dim);">No incoming consumers</div>'
        : incoming.map(l => {
            const srcName = (l.source.name || l.source);
            const srcId = (l.source.id || l.source);
            return `<div onclick="focusNodeOnGraph('${srcId}')" style="cursor: pointer; padding: 6px; background: var(--bg-surface-elevated); border-radius: 4px; font-size: 0.78rem;">
              <span style="color: var(--accent);">&larr; ${srcName}</span>
              <div style="color: var(--text-dim); font-size: 0.7rem;">${l.label || l.type}</div>
            </div>`;
          }).join('');

      sidebar.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span class="badge" style="background-color: ${node.cluster_color}20; border-color: ${node.cluster_color}; color: ${node.cluster_color};">${node.cluster_name}</span>
            ${node.is_hub ? '<span class="badge" style="background-color: #f59e0b20; border-color: #f59e0b; color: #f59e0b;">Architecture Hub</span>' : ''}
          </div>
          <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 4px;">${node.name}</h2>
          <a href="${node.html_url}" target="_blank" style="font-size: 0.8rem; color: var(--primary); text-decoration: none;">View on GitHub &rarr;</a>
        </div>

        <div style="font-size: 0.82rem; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 10px;">
          ${node.description || 'No description available.'}
        </div>

        <div>
          <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Tech Stack & Topics</div>
          <div>
            ${(node.topics || []).map(t => `<span class="tag">#${t}</span>`).join('')}
            ${(node.tech_stack || []).map(t => `<span class="tag" style="color: #6ee7b7;">${t}</span>`).join('')}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">
          <div style="background: var(--bg-surface-elevated); padding: 8px; border-radius: 4px;">
            <div style="color: var(--text-dim); font-size: 0.7rem;">Language</div>
            <div style="font-weight: 600;">${node.primary_language || 'Other'}</div>
          </div>
          <div style="background: var(--bg-surface-elevated); padding: 8px; border-radius: 4px;">
            <div style="color: var(--text-dim); font-size: 0.7rem;">Stars / Forks</div>
            <div style="font-weight: 600;">${node.stars || 0} / ${node.forks || 0}</div>
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
          <div style="font-size: 0.8rem; font-weight: 600; margin-bottom: 6px;">Outgoing Dependencies (${outgoing.length})</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${outgoingHtml}
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
          <div style="font-size: 0.8rem; font-weight: 600; margin-bottom: 6px;">Incoming Consumers (${incoming.length})</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${incomingHtml}
          </div>
        </div>
      `;
    }

    /* Focus node and navigate to Graph Tab */
    function focusNodeOnGraph(nodeId) {
      switchTab('tab-graph');
      selectNode(nodeId);
      const node = (KB_DATA.graph.nodes || []).find(n => String(n.id) === String(nodeId) || n.name === nodeId);
      if (node && node.x !== undefined && node.y !== undefined && svg) {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 700;
        svg.transition().duration(750).call(
          d3.zoom().transform,
          d3.zoomIdentity.translate(width / 2 - node.x * 1.5, height / 2 - node.y * 1.5).scale(1.5)
        );
      }
    }

    /* Filter Graph by Cross-Cluster Matrix Cell */
    function filterMatrixCell(srcClusterId, tgtClusterId) {
      switchTab('tab-graph');
      document.getElementById('graph-cluster-filter').value = 'all';
      document.getElementById('graph-edge-filter').value = 'all';
      activeClusterFilter = 'all';
      activeEdgeFilter = 'all';

      nodeElements.classed('dimmed', d => {
        return d.cluster_id !== srcClusterId && d.cluster_id !== tgtClusterId;
      });

      linkElements.classed('dimmed', l => {
        const sCluster = l.source.cluster_id || l.source_cluster;
        const tCluster = l.target.cluster_id || l.target_cluster;
        const match = (sCluster === srcClusterId && tCluster === tgtClusterId) || (sCluster === tgtClusterId && tCluster === srcClusterId);
        return !match;
      });
      showToast(`Filtered graph for ${srcClusterId} &rarr; ${tgtClusterId}`);
    }

    /* Repository Matcher & Chat Engine in JS */
    function setQueryChip(text) {
      const input = document.getElementById('matcher-query-input');
      if (input) {
        input.value = text;
        executeMatcherQuery();
      }
    }

    function executeMatcherQuery() {
      const query = (document.getElementById('matcher-query-input').value || '').trim();
      const area = document.getElementById('matcher-result-area');

      if (!query) {
        showToast('Please type a program or capability query.');
        return;
      }

      const rawTokens = (query.toLowerCase().match(/\b[a-zA-Z0-9_\-\.\+]+\b/g) || []);
      const searchTerms = rawTokens.filter(t => !STOP_WORDS.has(t) && t.length > 1);
      const specificTerms = searchTerms.filter(t => !GENERIC_TERMS.has(t));

      const repos = KB_DATA.repositories || [];
      const scored = [];

      repos.forEach(repo => {
        let score = 0.0;
        const reasons = [];
        let matchedSpecific = 0;

        const name = (repo.name || '').toLowerCase();
        const desc = (repo.description || '').toLowerCase();
        const readme = (repo.readme_summary || '').toLowerCase();
        const lang = (repo.primary_language || '').toLowerCase();
        const topics = (repo.topics || []).map(t => t.toLowerCase());
        const tech = (repo.tech_stack || []).map(t => t.toLowerCase());
        const cluster = (repo.cluster_name || '').toLowerCase();

        if (query.length > 5 && (desc.includes(query.toLowerCase()) || name.includes(query.toLowerCase()))) {
          score += 8.0;
          reasons.push('Exact phrase match in repository description or title');
        }

        searchTerms.forEach(term => {
          const isGen = GENERIC_TERMS.has(term);
          let matched = false;

          const nameParts = new Set([...name.split('-'), ...name.split('_'), name]);
          if (nameParts.has(term)) {
            score += isGen ? 2.0 : 6.0;
            reasons.push(`Repository name includes '${term}'`);
            matched = true;
          } else if (name.includes(term)) {
            score += isGen ? 1.0 : 3.5;
            reasons.push(`Repository name contains '${term}'`);
            matched = true;
          }

          if (topics.includes(term)) {
            score += isGen ? 1.5 : 5.0;
            reasons.push(`Topic tag matches '${term}'`);
            matched = true;
          }

          if (tech.includes(term)) {
            score += isGen ? 1.5 : 4.0;
            reasons.push(`Tech stack includes '${term}'`);
            matched = true;
          }

          if (term === lang) {
            score += 4.0;
            reasons.push(`Primary language is '${term}'`);
            matched = true;
          }

          if (desc.includes(term)) {
            score += isGen ? 1.0 : 3.5;
            reasons.push(`Description mentions '${term}'`);
            matched = true;
          }

          if (readme.includes(term)) {
            score += isGen ? 0.5 : 2.0;
            reasons.push(`Readme mentions '${term}'`);
            matched = true;
          }

          if (cluster.includes(term)) {
            score += isGen ? 0.5 : 2.0;
            reasons.push(`Belongs to domain '${term}'`);
            matched = true;
          }

          if (matched && !isGen) matchedSpecific++;
        });

        if (score > 0) {
          scored.push({ repo, score, reasons: Array.from(new Set(reasons)), matchedSpecific });
        }
      });

      let finalResults = scored;
      if (specificTerms.length > 0) {
        finalResults = scored.filter(s => s.matchedSpecific > 0);
      }

      finalResults.sort((a, b) => b.score - a.score);

      if (finalResults.length === 0 || finalResults[0].score < 3.5) {
        const domainNames = (KB_DATA.clusters || []).map(c => c.name).join(', ');
        area.innerHTML = `
          <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); padding: 18px; border-radius: 8px;">
            <div style="font-weight: 700; color: var(--danger); margin-bottom: 6px; font-size: 1rem;">No matching repository found</div>
            <div style="font-size: 0.85rem; color: var(--text-main); line-height: 1.4;">
              No repository in this organization can answer your need for <strong>"${query}"</strong>.<br/>
              The scanned organization contains repositories across these domains: <em>${domainNames || 'None'}</em>.
            </div>
          </div>
        `;
        return;
      }

      const best = finalResults[0];
      const confidence = best.score >= 6.0 ? 'High Confidence' : 'Moderate Confidence';
      const confColor = best.score >= 6.0 ? 'var(--success)' : 'var(--warning)';

      const alternatives = finalResults.slice(1, 4);

      area.innerHTML = `
        <div class="matcher-result-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
            <div>
              <span class="badge" style="background: ${confColor}20; color: ${confColor}; border-color: ${confColor}; margin-bottom: 6px;">${confidence} (Score: ${best.score.toFixed(1)})</span>
              <h3 style="font-size: 1.3rem; font-weight: 700;">
                <a href="${best.repo.html_url}" target="_blank" style="color: var(--primary); text-decoration: none;">${best.repo.name} &rarr;</a>
              </h3>
            </div>
            <button class="btn btn-primary btn-sm" onclick="focusNodeOnGraph('${best.repo.id}')">Locate on Knowledge Graph</button>
          </div>

          <div style="font-size: 0.9rem; color: var(--text-main);">
            ${best.repo.description}
          </div>

          <div style="display: flex; gap: 12px; font-size: 0.82rem; color: var(--text-muted);">
            <div><strong>Domain:</strong> <span class="badge" style="background: ${best.repo.cluster_color}20; color: ${best.repo.cluster_color};">${best.repo.cluster_name}</span></div>
            <div><strong>Language:</strong> ${best.repo.primary_language || 'Other'}</div>
            <div><strong>Stars:</strong> ${best.repo.stars || 0}</div>
          </div>

          <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
            <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Why this repository matches your query:</div>
            <ul style="padding-left: 20px; font-size: 0.85rem; color: var(--text-main); line-height: 1.4;">
              ${best.reasons.map(r => `<li>${r}</li>`).join('')}
            </ul>
          </div>

          ${alternatives.length > 0 ? `
            <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
              <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Alternative Candidates:</div>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                ${alternatives.map(alt => `
                  <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: var(--bg-surface); border-radius: 4px; font-size: 0.82rem;">
                    <div>
                      <strong style="color: var(--text-main); cursor: pointer;" onclick="focusNodeOnGraph('${alt.repo.id}')">${alt.repo.name}</strong>
                      <span style="color: var(--text-muted); font-size: 0.75rem;"> - ${alt.repo.description}</span>
                    </div>
                    <span class="badge" style="font-size: 0.7rem;">${alt.repo.primary_language}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }

    function onClusterFilterChange(clusterId) {
      activeClusterFilter = clusterId;
      applyGraphFilters();
    }

    function onEdgeFilterChange(edgeType) {
      activeEdgeFilter = edgeType;
      applyGraphFilters();
    }

    function onGraphSearch(query) {
      const q = query.trim().toLowerCase();
      if (!q) {
        nodeElements.classed('dimmed', false);
        linkElements.classed('dimmed', false);
        return;
      }

      nodeElements.classed('dimmed', d => {
        const match = d.name.toLowerCase().includes(q) ||
          (d.description || '').toLowerCase().includes(q) ||
          (d.primary_language || '').toLowerCase().includes(q) ||
          (d.topics || []).some(t => t.toLowerCase().includes(q));
        return !match;
      });
    }

    function applyGraphFilters() {
      nodeElements.classed('dimmed', d => {
        if (activeClusterFilter !== 'all' && d.cluster_id !== activeClusterFilter) return true;
        return false;
      });

      linkElements.classed('dimmed', l => {
        const srcCluster = l.source.cluster_id || l.source_cluster;
        const tgtCluster = l.target.cluster_id || l.target_cluster;

        if (activeClusterFilter !== 'all') {
          if (srcCluster !== activeClusterFilter && tgtCluster !== activeClusterFilter) return true;
        }

        if (activeEdgeFilter === 'depends_on' && l.type !== 'depends_on') return true;
        if (activeEdgeFilter === 'cross_cluster' && !l.is_cross_cluster) return true;
        if (activeEdgeFilter === 'shares_tech' && l.type !== 'shares_tech') return true;

        return false;
      });
    }

    function togglePhysics() {
      isPhysicsPaused = !isPhysicsPaused;
      const btn = document.getElementById('btn-toggle-physics');
      if (isPhysicsPaused) {
        simulation.stop();
        btn.textContent = 'Resume Physics';
      } else {
        simulation.restart();
        btn.textContent = 'Pause Physics';
      }
    }

    function resetGraphView() {
      resetSidebarDrawer();
      if (svg) {
        svg.transition().duration(500).call(
          d3.zoom().transform,
          d3.zoomIdentity
        );
      }
      const clusterSelect = document.getElementById('graph-cluster-filter');
      if (clusterSelect) clusterSelect.value = 'all';
      const edgeSelect = document.getElementById('graph-edge-filter');
      if (edgeSelect) edgeSelect.value = 'all';
      const searchInput = document.getElementById('graph-search');
      if (searchInput) searchInput.value = '';
      activeClusterFilter = 'all';
      activeEdgeFilter = 'all';
      if (nodeElements) nodeElements.classed('dimmed', false).classed('active', false);
      if (linkElements) linkElements.classed('dimmed', false).classed('highlighted', false);
      showToast('Graph view reset.');
    }

    /* Cluster Cards */
    function renderClusterCards() {
      const container = document.getElementById('cluster-cards-container');
      if (!container) return;
      const clusters = KB_DATA.clusters || [];
      const repos = KB_DATA.repositories || [];
      const repoMap = new Map(repos.map(r => [r.id, r]));

      container.innerHTML = clusters.map(c => `
        <div class="cluster-card" style="border-left-color: ${c.color || '#3b82f6'};" onclick="toggleClusterCard(this)">
          <div class="cluster-card-header">
            <div>
              <div class="cluster-card-title">${c.name}</div>
              <div class="cluster-card-desc">${c.description}</div>
            </div>
            <span class="badge" style="background: ${c.color}20; color: ${c.color}; border-color: ${c.color};">${c.repo_count} repos</span>
          </div>

          <div class="cluster-card-stats">
            <div><strong>Stars:</strong> ${c.total_stars}</div>
            <div><strong>Languages:</strong> ${(c.top_languages || []).join(', ') || 'N/A'}</div>
          </div>

          <div class="cluster-repos-list">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Repositories (Click to inspect):</div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
              ${(c.repositories || []).map(rid => {
                const r = repoMap.get(rid);
                if (!r) return '';
                return `<div class="cluster-repo-item" onclick="event.stopPropagation(); focusNodeOnGraph('${r.id}')">
                  <span style="font-family: var(--font-mono);">${r.name}</span>
                  <span style="color: var(--text-muted); font-size: 0.75rem;">${r.primary_language} &rarr;</span>
                </div>`;
              }).join('')}
            </div>
          </div>
        </div>
      `).join('');
    }

    function toggleClusterCard(card) {
      card.classList.toggle('expanded');
    }

    /* Repository Catalog Table */
    let repoSortCol = 0;
    let repoSortAsc = true;

    function renderRepoTable() {
      const repos = KB_DATA.repositories || [];
      const tbody = document.getElementById('repo-table-body');
      if (!tbody) return;

      tbody.innerHTML = repos.map(r => `
        <tr data-name="${r.name.toLowerCase()}" data-cluster="${r.cluster_id}" data-lang="${(r.primary_language || '').toLowerCase()}">
          <td>
            <strong><a href="${r.html_url}" target="_blank" style="color: var(--text-main); text-decoration: none;">${r.name}</a></strong>
            <div style="font-size: 0.75rem; color: var(--text-muted); max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${r.description}</div>
          </td>
          <td><span class="badge" style="background: ${r.cluster_color}20; color: ${r.cluster_color};">${r.cluster_name}</span></td>
          <td>${r.primary_language || 'Other'}</td>
          <td>${r.stars || 0}</td>
          <td>${r.centrality_score ? (r.in_degree + r.out_degree) : 0}</td>
          <td>${r.is_hub ? '<span class="badge" style="color: #fbbf24;">Hub</span>' : (r.is_bridge ? '<span class="badge" style="color: #38bdf8;">Bridge</span>' : '<span style="color: var(--text-dim);">-</span>')}</td>
          <td><button class="btn btn-sm" onclick="focusNodeOnGraph('${r.id}')">Inspect</button></td>
        </tr>
      `).join('');
    }

    function filterRepoTable() {
      const query = (document.getElementById('repo-table-search').value || '').toLowerCase();
      const cluster = document.getElementById('table-cluster-filter').value;
      const rows = document.querySelectorAll('#repo-table-body tr');

      rows.forEach(row => {
        const name = row.getAttribute('data-name');
        const rCluster = row.getAttribute('data-cluster');
        const lang = row.getAttribute('data-lang');

        const matchesQuery = name.includes(query) || lang.includes(query);
        const matchesCluster = (cluster === 'all' || rCluster === cluster);

        row.style.display = (matchesQuery && matchesCluster) ? '' : 'none';
      });
    }

    function sortTable(colIndex) {
      const table = document.getElementById('repo-data-table');
      if (!table) return;
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));

      if (repoSortCol === colIndex) {
        repoSortAsc = !repoSortAsc;
      } else {
        repoSortCol = colIndex;
        repoSortAsc = true;
      }

      rows.sort((a, b) => {
        const cellA = a.children[colIndex].textContent.trim();
        const cellB = b.children[colIndex].textContent.trim();

        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);

        if (!isNaN(numA) && !isNaN(numB)) {
          return repoSortAsc ? numA - numB : numB - numA;
        }
        return repoSortAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
      });

      rows.forEach(r => tbody.appendChild(r));
    }

    /* Matrix */
    function renderMatrix() {
      const container = document.getElementById('matrix-container');
      if (!container) return;
      const matrix = KB_DATA.graph.connectivity_matrix || {};
      const clusters = KB_DATA.clusters || [];

      let html = '<table class="matrix-table"><thead><tr><th>Source \\ Target</th>';
      clusters.forEach(c => {
        html += `<th title="${c.description}">${c.name}</th>`;
      });
      html += '</tr></thead><tbody>';

      clusters.forEach(src => {
        html += `<tr><td style="text-align: left; font-weight: 600;">${src.name}</td>`;
        clusters.forEach(tgt => {
          const count = (matrix[src.id] && matrix[src.id][tgt.id]) || 0;
          const activeClass = count > 0 ? 'matrix-cell-active' : '';
          const clickHandler = count > 0 ? `onclick="filterMatrixCell('${src.id}', '${tgt.id}')"` : '';
          html += `<td class="${activeClass}" ${clickHandler}>${count > 0 ? count : '-'}</td>`;
        });
        html += '</tr>';
      });

      html += '</tbody></table>';
      container.innerHTML = html;
    }

    /* Client-Side Live Scanning in Canvas */
    async function scanAddressInput() {
      const input = document.getElementById('scan-target-input').value.trim();
      if (!input) {
        showToast('Please enter a GitHub URL or handle.');
        return;
      }

      showToast('Scanning ' + input + '...');
      let target = input.replace(/^https?:\/\//, '').replace(/^github\.com\//, '').replace(/^orgs\//, '').replace(/\/$/, '');
      const parts = target.split('/').filter(Boolean);
      const owner = parts[0];
      const repoName = parts.length >= 2 ? parts[1] : null;

      try {
        if (repoName) {
          // Single repository scan
          const res = await fetch(`https://api.github.com/repos/${owner}/${repoName}`);
          if (res.status === 200) {
            const rawRepo = await res.json();
            processClientRepos(owner, input, [rawRepo]);
            showToast(`Successfully loaded repository ${owner}/${repoName}!`);
            return;
          }
        }

        const res = await fetch(`https://api.github.com/orgs/${owner}/repos?per_page=100&sort=updated`);
        if (res.status === 200) {
          const rawRepos = await res.json();
          processClientRepos(owner, input, rawRepos);
          showToast(`Successfully loaded ${rawRepos.length} repos from ${owner}!`);
        } else if (res.status === 404) {
          const userRes = await fetch(`https://api.github.com/users/${owner}/repos?per_page=100&sort=updated`);
          if (userRes.status === 200) {
            const rawRepos = await userRes.json();
            processClientRepos(owner, input, rawRepos);
            showToast(`Loaded ${rawRepos.length} repos from user ${owner}!`);
          } else {
            showToast(`GitHub account not found. Loading synthetic preview.`);
            onPresetChange('synthetic');
          }
        } else {
          showToast(`GitHub API rate limit or error (HTTP ${res.status}).`);
        }
      } catch (err) {
        showToast('Network / CORS limitation in iframe. Use Python CLI or local preset.');
      }
    }

    function processClientRepos(owner, inputUrl, rawRepos) {
      const taxonomy = [
        { id: "medical-healthcare", name: "Medical & Healthcare", description: "Clinical systems, electronic health records (EHR/EMR), patient care, FHIR, and telehealth.", color: "#0EA5E9", keywords: ["medical", "healthcare", "clinical", "patient", "health", "ehr", "emr", "fhir", "hl7", "dicom", "hospital", "telehealth", "hipaa", "diagnosis"] },
        { id: "life-sciences-bio", name: "Life Sciences & Bioinformatics", description: "Genomics sequencing pipelines, DNA/RNA molecular biology, and clinical trials research.", color: "#14B8A6", keywords: ["genomics", "bioinformatics", "biology", "dna", "rna", "sequencing", "protein", "crispr", "pharma", "biotech", "molecular", "clinical-trials", "laboratory"] },
        { id: "finance-billing", name: "Finance, Billing & Commerce", description: "Payment processing, subscription billing, invoices, accounting, and e-commerce checkout.", color: "#10B981", keywords: ["billing", "payment", "invoice", "subscription", "stripe", "checkout", "finance", "banking", "accounting", "ecommerce", "ledger"] },
        { id: "security-identity", name: "Security, Identity & Access", description: "Authentication, OAuth2/OIDC identity providers, token issuance, RBAC, and encryption.", color: "#EC4899", keywords: ["auth", "authentication", "oauth", "oauth2", "oidc", "identity", "security", "rbac", "jwt", "token", "encryption", "sso", "login"] },
        { id: "data-ai-analytics", name: "Data Intelligence & AI/ML", description: "Machine learning models, inference engines, vector search, streaming pipelines, and analytics.", color: "#8B5CF6", keywords: ["ai", "ml", "analytics", "pipeline", "etl", "kafka", "spark", "warehouse", "embeddings", "rag", "llm", "model", "inference"] },
        { id: "developer-tooling", name: "Developer Tooling & SDKs", description: "Client SDKs, CLI tools, API bindings, linters, code generators, and testing harnesses.", color: "#F59E0B", keywords: ["sdk", "cli", "client-library", "tooling", "generator", "plugin", "agent", "linter", "wrapper", "bindings"] },
        { id: "infrastructure-devops", name: "Infrastructure & Cloud Operations", description: "Cloud infrastructure as code, Terraform, Kubernetes, Helm, Docker, and CI/CD.", color: "#EF4444", keywords: ["infra", "infrastructure", "terraform", "k8s", "kubernetes", "docker", "helm", "ci-cd", "cloud", "aws", "gcp", "deploy"] },
        { id: "core-platform", name: "Core Platform & Business Services", description: "Routing gateways, user profiles, tenancy, notification dispatchers, and domain services.", color: "#3B82F6", keywords: ["gateway", "proxy", "user-service", "tenancy", "notification", "dispatch", "engine", "router", "service"] },
        { id: "frontend-applications", name: "User Applications & Web Portals", description: "Web portals, dashboards, customer interfaces, mobile apps, and interactive web apps.", color: "#06B6D4", keywords: ["portal", "app", "ui", "dashboard", "web", "frontend", "mobile", "ios", "android", "console", "react", "vue"] },
        { id: "utilities-libraries", name: "Utilities & Shared Libraries", description: "Shared common utilities, protocol buffer contracts, data schemas, and helper libraries.", color: "#64748B", keywords: ["utils", "utilities", "common", "shared", "core-lib", "proto", "contracts", "schemas", "helpers", "types"] },
        { id: "documentation-specs", name: "Documentation & Specifications", description: "Architectural blueprints, technical guides, OpenAPI specs, and RFC standards.", color: "#475569", keywords: ["docs", "documentation", "spec", "specification", "rfc", "guide", "architecture", "standard", "wiki"] }
      ];

      const repos = rawRepos.map((r, i) => {
        const topics = r.topics || [];
        const name = r.name || '';
        const desc = (r.description || '').toLowerCase();
        
        let assignedCluster = taxonomy[taxonomy.length - 2];
        for (const tax of taxonomy) {
          if (tax.keywords.some(k => name.toLowerCase().includes(k) || topics.includes(k) || desc.includes(k))) {
            assignedCluster = tax;
            break;
          }
        }

        return {
          id: r.id || (i + 1),
          name: r.name,
          full_name: r.full_name || `${owner}/${r.name}`,
          html_url: r.html_url,
          description: r.description || "No description provided.",
          primary_language: r.language || "Other",
          topics: topics,
          tech_stack: [r.language].filter(Boolean),
          stars: r.stargazers_count || 0,
          forks: r.forks_count || 0,
          open_issues: r.open_issues_count || 0,
          cluster_id: assignedCluster.id,
          cluster_name: assignedCluster.name,
          cluster_color: assignedCluster.color,
          dependencies: []
        };
      });

      const clusterMap = {};
      taxonomy.forEach(t => {
        clusterMap[t.id] = { ...t, repositories: [], total_stars: 0, top_languages: [] };
      });

      repos.forEach(r => {
        clusterMap[r.cluster_id].repositories.push(r.id);
        clusterMap[r.cluster_id].total_stars += r.stars;
      });

      const activeClusters = Object.values(clusterMap).filter(c => c.repositories.length > 0);
      activeClusters.forEach(c => { c.repo_count = c.repositories.length; });

      const nodes = repos.map(r => ({
        ...r,
        in_degree: 0,
        out_degree: 0,
        total_degree: 0,
        centrality_score: 0.1,
        is_hub: false,
        is_bridge: false
      }));

      const edges = [];
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const langA = nodes[i].primary_language;
          const langB = nodes[j].primary_language;
          const isSameCluster = nodes[i].cluster_id === nodes[j].cluster_id;
          const isSameLang = (langA === langB && langA !== 'Other');

          if (isSameLang || isSameCluster) {
            const relType = isSameLang ? 'shares_tech' : 'cluster_peer';
            const label = isSameLang ? `Shared ${langA}` : 'Domain Peer';
            edges.push({
              source: nodes[i].id,
              target: nodes[j].id,
              type: relType,
              label: label,
              description: `${nodes[i].name} and ${nodes[j].name} connect via ${label.toLowerCase()}.`,
              weight: 1.0,
              is_cross_cluster: nodes[i].cluster_id !== nodes[j].cluster_id,
              source_cluster: nodes[i].cluster_id,
              target_cluster: nodes[j].cluster_id
            });
            nodes[i].total_degree++;
            nodes[j].total_degree++;
          }
        }
      }

      KB_DATA = {
        metadata: { owner: owner, input_url: inputUrl, is_offline_fixture: false },
        clusters: activeClusters,
        repositories: repos,
        graph: {
          nodes: nodes,
          links: edges,
          hub_repositories: nodes.filter(n => n.total_degree >= 3).map(n => n.name),
          bridge_repositories: [],
          cross_cluster_count: edges.filter(e => e.is_cross_cluster).length,
          intra_cluster_count: edges.filter(e => !e.is_cross_cluster).length,
          connectivity_matrix: {}
        }
      };

      document.getElementById('active-target-display').textContent = 'Target: ' + inputUrl;
      refreshAllViews();
    }

    function onPresetChange(val) {
      if (val === 'current') {
        KB_DATA = JSON.parse(JSON.stringify(INITIAL_KB_DATA));
      } else if (val === 'synthetic') {
        KB_DATA = JSON.parse(JSON.stringify(INITIAL_KB_DATA));
      } else if (val === 'pallets') {
        document.getElementById('scan-target-input').value = 'https://github.com/pallets';
        scanAddressInput();
        return;
      } else if (val === 'fastapi') {
        document.getElementById('scan-target-input').value = 'https://github.com/fastapi';
        scanAddressInput();
        return;
      }
      refreshAllViews();
    }

    function copyRawJson() {
      const viewer = document.getElementById('raw-json-viewer');
      if (viewer) {
        viewer.select();
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(viewer.value);
          } else {
            document.execCommand('copy');
          }
          showToast('JSON copied to clipboard!');
        } catch (e) {
          document.execCommand('copy');
          showToast('JSON copied to clipboard!');
        }
      }
    }

    function exportDataJson() {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(KB_DATA, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', 'knowledge_base_export.json');
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exporting JSON file...');
    }
  </script>
</body>
</html>
"""
        return template.replace("__OWNER_NAME__", owner_name).replace("__TARGET_URL__", target_url).replace("__EMBEDDED_JSON__", json_data_str)
