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
        owner_name = data.get("metadata", {}).get("owner", "")
        target_url = data.get("metadata", {}).get("input_url", "")

        if not target_url or target_url == "GitHub Target":
            target_display = "Target: None (Enter a GitHub URL above to scan)"
            input_value = ""
        else:
            target_display = f"Target: {target_url}"
            input_value = target_url

        if not owner_name or owner_name == "Repository Organization":
            title_name = "Repository Architecture Canvas"
        else:
            title_name = f"Repository Architecture Canvas - {owner_name}"

        template = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE_NAME__</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    :root {
      --bg-base: #0f172a;
      --bg-surface: #1e293b;
      --bg-surface-elevated: #334155;
      --bg-surface-subtle: rgba(30, 41, 59, 0.78);
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
      --graph-link-stroke: #64748b;
      --graph-link-cross: #94a3b8;
      --graph-link-weak: #475569;
      --graph-node-stroke: #0f172a;
      --graph-hub-stroke: #fbbf24;
      --graph-label-halo: rgba(15, 23, 42, 0.92);
      --graph-pill-bg: rgba(15, 23, 42, 0.92);
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
      --bg-surface-subtle: rgba(255, 255, 255, 0.86);
      --border-color: #e2e8f0;
      --border-hover: #cbd5e1;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #94a3b8;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --graph-link-stroke: #64748b;
      --graph-link-cross: #475569;
      --graph-link-weak: #94a3b8;
      --graph-node-stroke: #ffffff;
      --graph-hub-stroke: #d97706;
      --graph-label-halo: rgba(248, 250, 252, 0.94);
      --graph-pill-bg: rgba(255, 255, 255, 0.95);
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
      gap: 0;
      height: clamp(600px, calc(100vh - 260px), 860px);
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
      min-height: 540px;
      background: radial-gradient(circle at center, var(--bg-surface-elevated) 0%, var(--bg-base) 100%);
      overflow: hidden;
    }

    .graph-controls {
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      width: fit-content;
      max-width: calc(100% - 20px);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      background-color: var(--bg-surface-subtle);
      padding: 6px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      z-index: 10;
      backdrop-filter: blur(8px);
    }

    .graph-controls select, .graph-controls input {
      padding: 4px 6px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: 4px;
      font-size: 0.74rem;
    }

    .graph-controls input#graph-search {
      width: 138px;
    }

    .graph-controls .btn-sm {
      padding: 4px 7px;
      font-size: 0.74rem;
    }

    .graph-zoom-bar {
      position: absolute;
      bottom: 14px;
      right: 14px;
      display: flex;
      align-items: center;
      gap: 4px;
      background-color: var(--bg-surface-subtle);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 4px 6px;
      z-index: 10;
      backdrop-filter: blur(8px);
      box-shadow: var(--shadow-md);
    }

    .zoom-btn {
      width: 26px;
      height: 26px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .zoom-btn:hover {
      background-color: var(--border-hover);
      border-color: var(--text-muted);
    }

    .zoom-btn-fit {
      width: auto;
      padding: 0 8px;
      font-size: 0.72rem;
      font-weight: 600;
    }

    .zoom-level {
      min-width: 40px;
      text-align: center;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--text-muted);
      user-select: none;
    }

    svg.graph-svg {
      width: 100%;
      height: 100%;
      cursor: grab;
      display: block;
    }

    svg.graph-svg:active {
      cursor: grabbing;
    }

    .cluster-zone {
      transition: opacity 0.2s ease;
    }

    .cluster-zone.dimmed {
      opacity: 0.18;
    }

    .cluster-hull {
      fill-opacity: 0.065;
      stroke-opacity: 0.24;
      stroke-dasharray: 5, 4;
      cursor: pointer;
      transition: fill-opacity 0.2s ease, stroke-opacity 0.2s ease;
    }

    .cluster-hull:hover {
      fill-opacity: 0.11;
      stroke-opacity: 0.42;
    }

    .cluster-title {
      fill: var(--text-muted);
      font-family: var(--font-sans);
      font-weight: 700;
      letter-spacing: 0.06em;
      cursor: pointer;
      user-select: none;
      paint-order: stroke;
      stroke: var(--graph-label-halo);
      stroke-width: 3px;
      stroke-linejoin: round;
      transition: opacity 0.2s ease, fill 0.15s ease;
    }

    .cluster-title:hover {
      fill: var(--text-main);
    }

    .graph-link {
      fill: none;
      stroke: var(--graph-link-stroke);
      stroke-opacity: 0.44;
      stroke-linecap: round;
      transition: stroke-opacity 0.2s ease, opacity 0.2s ease;
    }

    .graph-link.cross-cluster {
      stroke: var(--graph-link-cross);
      stroke-opacity: 0.36;
      stroke-dasharray: 5, 4;
    }

    .graph-link.weak-link {
      stroke: var(--graph-link-weak);
      stroke-opacity: 0.18;
      stroke-dasharray: 2.5, 3.5;
    }

    .graph-link.highlighted {
      stroke: #38bdf8 !important;
      stroke-opacity: 0.95 !important;
      stroke-dasharray: none !important;
    }

    .graph-link.dimmed {
      opacity: 0.04;
    }

    .edge-labels-layer {
      pointer-events: none;
    }

    .edge-label-bg {
      fill: var(--graph-pill-bg);
      stroke: var(--border-color);
    }

    .edge-label-text {
      fill: var(--text-main);
      font-family: var(--font-sans);
      font-weight: 500;
      user-select: none;
    }

    .graph-node {
      cursor: pointer;
      transition: opacity 0.2s ease;
    }

    .graph-node circle.node-circle {
      transition: opacity 0.2s ease, stroke 0.15s ease;
    }

    .graph-node.dimmed {
      opacity: 0.14;
    }

    .graph-node.active circle.node-circle,
    .graph-node.hovered circle.node-circle {
      stroke: var(--text-main);
    }

    .node-labels-layer {
      pointer-events: none;
    }

    .node-label-group {
      transition: opacity 0.16s ease;
    }

    .node-label-bg {
      fill: var(--graph-pill-bg);
      stroke: var(--border-color);
    }

    .node-label-text {
      fill: var(--text-main);
      font-family: var(--font-mono);
      font-weight: 500;
      user-select: none;
      paint-order: stroke;
      stroke: var(--graph-label-halo);
      stroke-linejoin: round;
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
      <div class="topbar-subtitle" id="active-target-display">__TARGET_DISPLAY__</div>
    </div>

    <!-- Live Address Scan Input -->
    <div class="scan-bar">
      <input type="text" id="scan-target-input" class="scan-input" value="__INPUT_VALUE__" placeholder="Enter any public GitHub Org or Repo URL (e.g. github.com/pallets or https://github.com/fastapi/fastapi)" onkeydown="if(event.key==='Enter') scanAddressInput();" />
      <button class="btn btn-primary btn-sm" onclick="scanAddressInput()">Scan Address</button>
    </div>

    <div class="topbar-actions">
      <select id="preset-selector" class="btn btn-sm" onchange="onPresetChange(this.value)">
        <option value="current">Current Scanned Dataset</option>
        <option value="synthetic">Synthetic Multi-Domain Demo (16 Repos)</option>
        <option value="pallets">Pallets Org (Flask, Click, Jinja, Werkzeug)</option>
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
            <select id="graph-label-mode" onchange="onLabelModeChange(this.value)" title="Node label visibility mode">
              <option value="smart" selected>Labels: Smart (Zoom)</option>
              <option value="all">Labels: All</option>
              <option value="hubs">Labels: Hubs &amp; Hover</option>
            </select>
            <select id="graph-spacing-mode" onchange="onSpacingModeChange(this.value)" title="Node &amp; cluster spacing">
              <option value="balanced" selected>Spacing: Balanced</option>
              <option value="wide">Spacing: Wide</option>
              <option value="compact">Spacing: Compact</option>
            </select>
            <button class="btn btn-sm" onclick="resetGraphView()">Reset View</button>
            <button class="btn btn-sm" id="btn-toggle-physics" onclick="togglePhysics()">Pause Physics</button>
          </div>
          <svg class="graph-svg" id="graph-svg"></svg>
          <div class="graph-zoom-bar" aria-label="Graph zoom controls">
            <button class="zoom-btn" onclick="zoomGraphBy(1.35)" title="Zoom In">+</button>
            <span class="zoom-level" id="graph-zoom-level">100%</span>
            <button class="zoom-btn" onclick="zoomGraphBy(0.74)" title="Zoom Out">&minus;</button>
            <button class="zoom-btn zoom-btn-fit" onclick="zoomToFitAll(true)" title="Fit All Clusters">Fit</button>
          </div>
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
          <button class="chip-btn" onclick="setQueryChip('Patient clinical EHR records and FHIR')">Patient EHR Records</button>
          <button class="chip-btn" onclick="setQueryChip('DNA and RNA bioinformatics genomics pipeline')">Genomics Sequencing</button>
          <button class="chip-btn" onclick="setQueryChip('OAuth2 and user login authentication service')">User Authentication</button>
          <button class="chip-btn" onclick="setQueryChip('Subscription billing and Stripe payments')">Subscription Billing</button>
          <button class="chip-btn" onclick="setQueryChip('Python client SDK for platform API automation')">Python Client SDK</button>
          <button class="chip-btn" onclick="setQueryChip('Terraform and Kubernetes cloud infrastructure')">Terraform DevOps</button>
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
    let svg, gClusters, gLinks, gEdgeLabels, gNodes, gNodeLabels;
    let linkElements, nodeElements, nodeLabelElements;
    let d3Zoom;
    let currentZoomTransform = { k: 1, x: 0, y: 0 };
    let semanticZoomRaf = null;
    let rawNodes = [];
    let rawLinks = [];
    let activeClusterCenters = {};
    let clusterRegionCache = [];
    let layoutBaseRadius = 360;
    let selectedNodeId = null;
    let hoveredNodeId = null;
    let isPhysicsPaused = false;
    let activeClusterFilter = 'all';
    let activeEdgeFilter = 'all';
    let activeLabelMode = 'smart';
    let activeSpacingMode = 'balanced';
    let activeSearchQuery = '';
    let activeMatrixPair = null;

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

    let resizeTimer = null;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const container = document.getElementById('graph-container');
        if (svg && container && container.clientWidth > 0 && container.clientHeight > 0) {
          svg.attr('viewBox', [0, 0, container.clientWidth, container.clientHeight]);
          updateSemanticZoom();
        }
      }, 160);
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
      if (gEdgeLabels) gEdgeLabels.selectAll('*').remove();
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

      if (tabId === 'tab-graph' && svg) {
        const container = document.getElementById('graph-container');
        if (container && container.clientWidth > 0 && container.clientHeight > 0) {
          svg.attr('viewBox', [0, 0, container.clientWidth, container.clientHeight]);
        }
        updateSemanticZoom();
      }
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      updateSemanticZoom();
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

    /* D3.js Force Directed Graph (Spacious Cluster Layout + Semantic Zoom LOD) */
    function clampVal(v, minV, maxV) {
      return Math.max(minV, Math.min(maxV, v));
    }

    function getSpacingMultiplier() {
      if (activeSpacingMode === 'wide') return 1.32;
      if (activeSpacingMode === 'compact') return 0.78;
      return 1.0;
    }

    function getNodeBaseRadius(d) {
      if (d.is_hub) return 14;
      if (d.is_bridge) return 11;
      return 8.5;
    }

    function getNodeWorldRadius(d, k) {
      const safeK = Math.max(k || 1, 0.08);
      const dampScale = clampVal(Math.pow(safeK, -0.35), 0.48, 1.42);
      return getNodeBaseRadius(d) * dampScale;
    }

    function rectsOverlap(a, b) {
      return !(a.x2 <= b.x1 || a.x1 >= b.x2 || a.y2 <= b.y1 || a.y1 >= b.y2);
    }

    function rectOverlapArea(a, b) {
      const ox = Math.max(0, Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1));
      const oy = Math.max(0, Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1));
      return ox * oy;
    }

    function computeClusterCenters(clusters, nodes, links, width, height, spacingMult) {
      const nodeCountByCluster = {};
      nodes.forEach(n => {
        const cid = n.cluster_id || 'general';
        nodeCountByCluster[cid] = (nodeCountByCluster[cid] || 0) + 1;
      });

      const activeIds = Object.keys(nodeCountByCluster);
      const clusterMetaMap = {};
      (clusters || []).forEach(c => { clusterMetaMap[c.id] = c; });

      const activeClusters = activeIds.map(id => {
        const meta = clusterMetaMap[id] || {};
        return {
          id,
          name: meta.name || (nodes.find(n => n.cluster_id === id) || {}).cluster_name || id,
          color: meta.color || (nodes.find(n => n.cluster_id === id) || {}).cluster_color || '#3b82f6',
          count: nodeCountByCluster[id] || 1
        };
      });

      const centers = {};
      const cCount = activeClusters.length;
      if (cCount === 0) return { centers, baseRadius: 320 * spacingMult, orderedClusters: [] };

      // Build inter-cluster affinity weights so connected domains sit adjacent around the ring
      const affinity = {};
      const totalCross = {};
      activeClusters.forEach(c => {
        affinity[c.id] = {};
        totalCross[c.id] = 0;
      });
      const nodeClusterLookup = {};
      nodes.forEach(n => { nodeClusterLookup[String(n.id)] = n.cluster_id || 'general'; });
      (links || []).forEach(l => {
        const sId = String(typeof l.source === 'object' ? l.source.id : l.source);
        const tId = String(typeof l.target === 'object' ? l.target.id : l.target);
        const sc = l.source_cluster || nodeClusterLookup[sId];
        const tc = l.target_cluster || nodeClusterLookup[tId];
        if (sc && tc && sc !== tc && affinity[sc] && affinity[tc]) {
          const w = l.type === 'depends_on' ? 2 : 1;
          affinity[sc][tc] = (affinity[sc][tc] || 0) + w;
          affinity[tc][sc] = (affinity[tc][sc] || 0) + w;
          totalCross[sc] += w;
          totalCross[tc] += w;
        }
      });

      // Greedy connectivity ordering around the ring to reduce cross-graph edge crossings
      const remaining = [...activeClusters].sort((a, b) => (totalCross[b.id] - totalCross[a.id]) || (b.count - a.count));
      const ordered = [];
      if (remaining.length > 0) {
        ordered.push(remaining.shift());
        while (remaining.length > 0) {
          const prev = ordered[ordered.length - 1];
          let bestIdx = 0;
          let bestScore = -1;
          for (let i = 0; i < remaining.length; i++) {
            const cand = remaining[i];
            const score = (affinity[prev.id][cand.id] || 0) * 10 + cand.count * 0.1;
            if (score > bestScore) {
              bestScore = score;
              bestIdx = i;
            }
          }
          ordered.push(remaining.splice(bestIdx, 1)[0]);
        }
      }

      const bubbleRadius = (count) => (count <= 1 ? 62 : (72 + Math.sqrt(count) * 54)) * spacingMult;

      if (cCount === 1) {
        centers[ordered[0].id] = { x: 0, y: 0, angle: -Math.PI / 2, bubbleRadius: bubbleRadius(ordered[0].count) };
        return { centers, baseRadius: Math.max(240, bubbleRadius(ordered[0].count) * 2), orderedClusters: ordered };
      }

      if (cCount === 2) {
        const b0 = bubbleRadius(ordered[0].count);
        const b1 = bubbleRadius(ordered[1].count);
        const halfSep = Math.max(210 * spacingMult, (b0 + b1) * 0.65 + 90 * spacingMult);
        centers[ordered[0].id] = { x: -halfSep, y: 0, angle: Math.PI, bubbleRadius: b0 };
        centers[ordered[1].id] = { x: halfSep, y: 0, angle: 0, bubbleRadius: b1 };
        return { centers, baseRadius: halfSep, orderedClusters: ordered };
      }

      // Proportional arc allocation around a widescreen ellipse matching container aspect ratio
      const interGap = 115 * spacingMult;
      const spans = ordered.map(c => 2 * bubbleRadius(c.count) + interGap);
      const totalPerimeter = spans.reduce((acc, s) => acc + s, 0);
      const baseRadius = Math.max(310 * spacingMult, totalPerimeter / (2 * Math.PI));

      const aspect = clampVal((width || 960) / Math.max(height || 660, 320), 1.05, 1.58);
      const rx = baseRadius * Math.sqrt(aspect);
      const ry = baseRadius / Math.sqrt(aspect);

      let cumSpan = 0;
      ordered.forEach((c, idx) => {
        const midSpan = cumSpan + spans[idx] / 2;
        cumSpan += spans[idx];
        const angle = -Math.PI / 2 + (midSpan / totalPerimeter) * 2 * Math.PI;
        centers[c.id] = {
          x: Math.cos(angle) * rx,
          y: Math.sin(angle) * ry,
          angle,
          bubbleRadius: bubbleRadius(c.count)
        };
      });

      return { centers, baseRadius, orderedClusters: ordered };
    }

    function seedNodePositions(nodes, centers, spacingMult) {
      const grouped = {};
      nodes.forEach(n => {
        const cid = n.cluster_id || 'general';
        if (!grouped[cid]) grouped[cid] = [];
        grouped[cid].push(n);
      });

      const goldenAngle = 2.399963229728653;
      Object.keys(grouped).forEach(cid => {
        const list = grouped[cid].sort((a, b) => (b.total_degree || 0) - (a.total_degree || 0));
        const center = centers[cid] || { x: 0, y: 0 };
        if (list.length === 1) {
          list[0].x = center.x;
          list[0].y = center.y;
          return;
        }
        list.forEach((n, idx) => {
          const r = (idx === 0 && list.length >= 4) ? 0 : (62 * spacingMult * Math.sqrt(idx + 0.6));
          const theta = idx * goldenAngle + (center.angle || 0);
          n.x = center.x + Math.cos(theta) * r;
          n.y = center.y + Math.sin(theta) * r;
        });
      });
    }

    function applySimulationForces(spacingMult) {
      if (!simulation) return;
      const crossDist = Math.max(250, layoutBaseRadius * 0.65);
      const intraDist = 148 * spacingMult;

      simulation
        .force('link', d3.forceLink(rawLinks)
          .id(d => d.id)
          .distance(d => d.is_cross_cluster ? crossDist : intraDist)
          .strength(d => {
            const isWeak = d.type === 'shares_tech' || d.type === 'cluster_peer';
            if (d.is_cross_cluster) return isWeak ? 0.018 : 0.05;
            return isWeak ? 0.12 : 0.28;
          })
        )
        .force('charge', d3.forceManyBody()
          .strength(d => (d.is_hub ? -740 : -540) * spacingMult)
          .distanceMax(Math.max(700, layoutBaseRadius * 1.5))
        )
        .force('collision', d3.forceCollide()
          .radius(d => (d.is_hub ? 78 : 66) * spacingMult)
          .strength(0.92)
          .iterations(4)
        )
        .force('clusterX', d3.forceX(d => (activeClusterCenters[d.cluster_id] ? activeClusterCenters[d.cluster_id].x : 0)).strength(0.24))
        .force('clusterY', d3.forceY(d => (activeClusterCenters[d.cluster_id] ? activeClusterCenters[d.cluster_id].y : 0)).strength(0.24));
    }

    function initGraph() {
      const container = document.getElementById('graph-container');
      if (!container || typeof d3 === 'undefined') return;
      const width = container.clientWidth || 900;
      const height = container.clientHeight || 660;

      if (simulation) simulation.stop();
      d3.select('#graph-svg').selectAll('*').remove();

      rawNodes = (KB_DATA.graph.nodes || []).map(d => Object.assign({}, d));
      rawLinks = (KB_DATA.graph.links || []).map(d => Object.assign({}, d));
      currentZoomTransform = d3.zoomIdentity;
      hoveredNodeId = null;

      // Detect bidirectional link pairs so they curve in opposite directions instead of stacking
      const dirSet = new Set();
      rawLinks.forEach(l => {
        const s = String(typeof l.source === 'object' ? l.source.id : l.source);
        const t = String(typeof l.target === 'object' ? l.target.id : l.target);
        dirSet.add(s + '->' + t);
      });
      rawLinks.forEach((l, idx) => {
        const s = String(typeof l.source === 'object' ? l.source.id : l.source);
        const t = String(typeof l.target === 'object' ? l.target.id : l.target);
        const hasRev = dirSet.has(t + '->' + s);
        if (hasRev) {
          l._curveDir = s < t ? 1 : -1;
          l._curveMag = 0.20;
        } else {
          l._curveDir = (idx % 2 === 0) ? 1 : -1;
          l._curveMag = l.is_cross_cluster ? 0.14 : 0.10;
        }
      });

      svg = d3.select('#graph-svg')
        .attr('viewBox', [0, 0, width, height])
        .on('click', (event) => {
          if (event.target === svg.node()) {
            resetSidebarDrawer();
            refreshGraphHighlights();
          }
        });

      const g = svg.append('g').attr('class', 'graph-viewport');

      d3Zoom = d3.zoom()
        .scaleExtent([0.12, 4.5])
        .on('zoom', (event) => {
          currentZoomTransform = event.transform;
          g.attr('transform', event.transform);
          scheduleSemanticZoom();
        });
      svg.call(d3Zoom);

      const defs = svg.append('defs');
      const markerConfigs = [
        { id: 'arrow-default', fill: 'var(--graph-link-stroke)' },
        { id: 'arrow-cross', fill: 'var(--graph-link-cross)' },
        { id: 'arrow-weak', fill: 'var(--graph-link-weak)' },
        { id: 'arrow-highlight', fill: '#38bdf8' }
      ];
      defs.selectAll('marker')
        .data(markerConfigs)
        .enter().append('marker')
        .attr('id', d => d.id)
        .attr('viewBox', '0 -4 10 8')
        .attr('refX', 8.5)
        .attr('refY', 0)
        .attr('markerUnits', 'userSpaceOnUse')
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-3.5L9,0L0,3.5Z')
        .attr('fill', d => d.fill);

      gClusters = g.append('g').attr('class', 'clusters-layer');
      gLinks = g.append('g').attr('class', 'links');
      gEdgeLabels = g.append('g').attr('class', 'edge-labels-layer');
      gNodes = g.append('g').attr('class', 'nodes');
      gNodeLabels = g.append('g').attr('class', 'node-labels-layer');

      const spacingMult = getSpacingMultiplier();
      const layoutInfo = computeClusterCenters(KB_DATA.clusters || [], rawNodes, rawLinks, width, height, spacingMult);
      activeClusterCenters = layoutInfo.centers;
      layoutBaseRadius = layoutInfo.baseRadius;
      seedNodePositions(rawNodes, activeClusterCenters, spacingMult);

      simulation = d3.forceSimulation(rawNodes)
        .alphaDecay(0.035)
        .velocityDecay(0.42);
      applySimulationForces(spacingMult);

      linkElements = gLinks.selectAll('path')
        .data(rawLinks)
        .enter().append('path')
        .attr('class', d => {
          const classes = ['graph-link'];
          if (d.is_cross_cluster) classes.push('cross-cluster');
          if (d.type === 'shares_tech' || d.type === 'cluster_peer') classes.push('weak-link');
          return classes.join(' ');
        })
        .attr('marker-end', d => getLinkMarkerUrl(d, false));

      nodeElements = gNodes.selectAll('g')
        .data(rawNodes)
        .enter().append('g')
        .attr('class', 'graph-node')
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        )
        .on('click', (event, d) => {
          event.stopPropagation();
          selectNode(d.id);
        })
        .on('mouseover', handleNodeMouseOver)
        .on('mousemove', handleNodeMouseMove)
        .on('mouseout', handleNodeMouseOut);

      nodeElements.append('circle')
        .attr('class', 'node-circle')
        .attr('r', d => getNodeBaseRadius(d))
        .attr('fill', d => d.cluster_color || '#3b82f6')
        .attr('stroke', d => d.is_hub ? 'var(--graph-hub-stroke)' : 'var(--graph-node-stroke)');

      nodeLabelElements = gNodeLabels.selectAll('g')
        .data(rawNodes)
        .enter().append('g')
        .attr('class', 'node-label-group');

      nodeLabelElements.append('rect')
        .attr('class', 'node-label-bg')
        .attr('rx', 4)
        .attr('ry', 4)
        .style('display', 'none');

      nodeLabelElements.append('text')
        .attr('class', 'node-label-text')
        .text(d => d.name);

      // Synchronous warmup ticks so the initial layout renders already calm, spacious, and untangled
      simulation.stop();
      for (let i = 0; i < 120; i++) {
        simulation.tick();
      }
      renderGraphPositions();

      simulation.on('tick', () => {
        renderGraphPositions();
      });

      simulation.on('end', () => {
        renderGraphPositions();
        updateSemanticZoom();
      });

      // Immediately frame the stabilized spacious layout
      zoomToFitAll(false);
      refreshGraphHighlights();

      if (!isPhysicsPaused) {
        simulation.alpha(0.14).restart();
      }

      function dragstarted(event, d) {
        if (!event.active && !isPhysicsPaused) simulation.alphaTarget(0.25).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
        renderGraphPositions();
      }

      function dragended(event, d) {
        if (!event.active && !isPhysicsPaused) simulation.alphaTarget(0);
        if (!isPhysicsPaused) {
          d.fx = null;
          d.fy = null;
        }
      }
    }

    function recomputeGraphSpacing() {
      if (!rawNodes || rawNodes.length === 0 || !simulation) return;
      const container = document.getElementById('graph-container');
      const width = container ? (container.clientWidth || 900) : 900;
      const height = container ? (container.clientHeight || 700) : 700;
      const spacingMult = getSpacingMultiplier();

      const layoutInfo = computeClusterCenters(KB_DATA.clusters || [], rawNodes, rawLinks, width, height, spacingMult);
      activeClusterCenters = layoutInfo.centers;
      layoutBaseRadius = layoutInfo.baseRadius;

      rawNodes.forEach(n => { n.fx = null; n.fy = null; });
      applySimulationForces(spacingMult);

      simulation.stop();
      simulation.alpha(0.7);
      for (let i = 0; i < 90; i++) {
        simulation.tick();
      }
      renderGraphPositions();
      zoomToFitAll(true, 550);
      if (!isPhysicsPaused) {
        simulation.alpha(0.12).restart();
      }
      showToast('Graph spacing set to ' + activeSpacingMode);
    }

    function getLinkMarkerUrl(d, isHighlighted) {
      if (isHighlighted) return 'url(#arrow-highlight)';
      if (d.type === 'shares_tech' || d.type === 'cluster_peer') return 'url(#arrow-weak)';
      return d.is_cross_cluster ? 'url(#arrow-cross)' : 'url(#arrow-default)';
    }

    function renderGraphPositions() {
      if (!nodeElements || !linkElements) return;
      updateLinkPaths();
      nodeElements.attr('transform', d => `translate(${d.x},${d.y})`);
      if (nodeLabelElements) {
        nodeLabelElements.attr('transform', d => `translate(${d.x},${d.y})`);
      }
      updateClusterRegions();
      scheduleSemanticZoom();
    }

    function updateLinkPaths() {
      if (!linkElements) return;
      const k = Math.max(currentZoomTransform.k || 1, 0.1);
      const padScale = 1 / Math.pow(k, 0.55);

      linkElements.attr('d', d => {
        const sx = d.source.x || 0;
        const sy = d.source.y || 0;
        const tx = d.target.x || 0;
        const ty = d.target.y || 0;
        const dx = tx - sx;
        const dy = ty - sy;
        const dist = Math.hypot(dx, dy) || 1;

        const curveOffset = Math.min(dist * (d._curveMag || 0.14), 110) * (d._curveDir || 1);
        const mx = (sx + tx) / 2;
        const my = (sy + ty) / 2;
        const nx = -dy / dist;
        const ny = dx / dist;
        const cx = mx + nx * curveOffset;
        const cy = my + ny * curveOffset;

        // Trim curve start and end precisely at node rims so arrowheads kiss target perimeter cleanly
        const srcR = getNodeWorldRadius(d.source, k) + 1.5 * padScale;
        const tgtR = getNodeWorldRadius(d.target, k) + 4.5 * padScale;

        const sdx = cx - sx;
        const sdy = cy - sy;
        const slen = Math.hypot(sdx, sdy) || 1;
        const startX = dist > srcR + tgtR + 4 ? sx + (sdx / slen) * srcR : sx;
        const startY = dist > srcR + tgtR + 4 ? sy + (sdy / slen) * srcR : sy;

        const tdx = tx - cx;
        const tdy = ty - cy;
        const tlen = Math.hypot(tdx, tdy) || 1;
        const endX = dist > srcR + tgtR + 4 ? tx - (tdx / tlen) * tgtR : tx;
        const endY = dist > srcR + tgtR + 4 ? ty - (tdy / tlen) * tgtR : ty;

        // Store quadratic Bezier geometry & midpoint (t = 0.5) for collision-free hover/select edge labels
        d._p0x = startX;
        d._p0y = startY;
        d._cx = cx;
        d._cy = cy;
        d._p2x = endX;
        d._p2y = endY;
        d._worldLen = dist;
        d._midX = 0.25 * startX + 0.5 * cx + 0.25 * endX;
        d._midY = 0.25 * startY + 0.5 * cy + 0.25 * endY;

        return `M${startX.toFixed(1)},${startY.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${endX.toFixed(1)},${endY.toFixed(1)}`;
      });
    }

    function updateClusterRegions() {
      if (!gClusters || !rawNodes || rawNodes.length === 0) return;

      const spacingMult = getSpacingMultiplier();
      const hullPad = 46 * spacingMult;
      const byCluster = {};
      let sumX = 0, sumY = 0, count = 0;

      rawNodes.forEach(n => {
        if (n.x === undefined || n.y === undefined) return;
        sumX += n.x;
        sumY += n.y;
        count++;
        const cid = n.cluster_id || 'general';
        if (!byCluster[cid]) {
          byCluster[cid] = {
            id: cid,
            name: n.cluster_name || cid,
            color: n.cluster_color || '#3b82f6',
            nodes: []
          };
        }
        byCluster[cid].nodes.push(n);
      });

      const graphMidX = count > 0 ? sumX / count : 0;
      const graphMidY = count > 0 ? sumY / count : 0;
      const hullLine = d3.line().curve(d3.curveCatmullRomClosed.alpha(0.5));
      const octAngles = [0, 1, 2, 3, 4, 5, 6, 7].map(i => (i * Math.PI) / 4);

      const clusterRegions = Object.values(byCluster).map(cluster => {
        const pts = [];
        let cx = 0, cy = 0;
        cluster.nodes.forEach(n => {
          cx += n.x;
          cy += n.y;
          octAngles.forEach(a => {
            pts.push([n.x + Math.cos(a) * hullPad, n.y + Math.sin(a) * hullPad]);
          });
        });
        cx /= cluster.nodes.length;
        cy /= cluster.nodes.length;

        const hull = d3.polygonHull(pts) || pts;
        const pathD = hullLine(hull);

        // Compute hull vertical bounds so cluster title sits cleanly centered above (top half) or below (bottom half)
        let hullMinY = Infinity, hullMaxY = -Infinity;
        hull.forEach(p => {
          if (p[1] < hullMinY) hullMinY = p[1];
          if (p[1] > hullMaxY) hullMaxY = p[1];
        });
        const placeAbove = cy <= graphMidY + 25;

        return {
          id: cluster.id,
          name: cluster.name,
          color: cluster.color,
          pathD,
          cx,
          cy,
          hullMinY,
          hullMaxY,
          placeAbove,
          count: cluster.nodes.length
        };
      });

      const groups = gClusters.selectAll('g.cluster-zone')
        .data(clusterRegions, d => d.id);

      const enter = groups.enter().append('g')
        .attr('class', 'cluster-zone');

      enter.append('path')
        .attr('class', 'cluster-hull')
        .on('click', (event, d) => {
          event.stopPropagation();
          zoomToCluster(d.id, true);
        });

      enter.append('text')
        .attr('class', 'cluster-title')
        .on('click', (event, d) => {
          event.stopPropagation();
          zoomToCluster(d.id, true);
        });

      const merged = enter.merge(groups);
      merged.classed('dimmed', d => {
        if (activeMatrixPair) {
          return d.id !== activeMatrixPair.src && d.id !== activeMatrixPair.tgt;
        }
        return activeClusterFilter !== 'all' && d.id !== activeClusterFilter;
      });

      merged.select('path.cluster-hull')
        .attr('d', d => d.pathD)
        .attr('fill', d => d.color)
        .attr('stroke', d => d.color);

      merged.select('text.cluster-title')
        .text(d => d.name.toUpperCase());

      groups.exit().remove();
      clusterRegionCache = clusterRegions;
    }

    function scheduleSemanticZoom() {
      if (semanticZoomRaf) return;
      semanticZoomRaf = requestAnimationFrame(() => {
        semanticZoomRaf = null;
        updateSemanticZoom();
      });
    }

    function updateSemanticZoom() {
      if (!nodeElements || !nodeLabelElements) return;
      const t = currentZoomTransform || (typeof d3 !== 'undefined' ? d3.zoomIdentity : { k: 1, x: 0, y: 0 });
      const k = Math.max(t.k || 1, 0.08);
      const tx = t.x || 0;
      const ty = t.y || 0;

      const container = document.getElementById('graph-container');
      const viewW = container ? (container.clientWidth || 900) : 900;
      const viewH = container ? (container.clientHeight || 660) : 660;

      // Update zoom indicator badge
      const zoomBadge = document.getElementById('graph-zoom-level');
      if (zoomBadge) {
        zoomBadge.textContent = Math.round(k * 100) + '%';
      }

      // 1. Scale node circles smoothly with zoom (compact when zoomed out, richer when zoomed in)
      const strokeScale = 1 / Math.pow(k, 0.55);
      nodeElements.select('circle.node-circle')
        .attr('r', d => getNodeWorldRadius(d, k))
        .style('stroke-width', d => {
          const isFocus = String(d.id) === String(selectedNodeId) || String(d.id) === String(hoveredNodeId);
          return ((isFocus ? 3.2 : (d.is_hub ? 2.2 : 1.6)) * strokeScale) + 'px';
        });

      // Scale link strokes & arrowhead markers crisply at every zoom level
      if (linkElements) {
        linkElements.style('stroke-width', d => {
          const isWeak = d.type === 'shares_tech' || d.type === 'cluster_peer';
          const base = isWeak ? 1.1 : Math.min(2.2, Math.max(1.3, (d.weight || 1.2) * 0.85));
          return (base * strokeScale) + 'px';
        });
      }
      if (svg) {
        const markerSize = clampVal(8.5 * strokeScale, 4.5, 13.5);
        svg.selectAll('defs marker')
          .attr('markerWidth', markerSize)
          .attr('markerHeight', markerSize);
      }
      updateLinkPaths();

      // 2. Scale & position centered cluster titles above/below each hull, recording screen rects to prevent collisions
      const clusterLabelScreenFont = clampVal(9.2 + (k - 0.5) * 1.4, 8.8, 11.2);
      const clusterLabelWorldFont = clusterLabelScreenFont / k;
      const clusterTitleOpacity = k > 2.35 ? 0.25 : 0.80;
      const clusterTitleBoxes = [];

      if (gClusters) {
        gClusters.selectAll('g.cluster-zone').each(function(d) {
          const isDimmed = d3.select(this).classed('dimmed');
          const offsetWorld = 12 / k;
          const estW = d.name.length * clusterLabelScreenFont * 0.62 + 8;
          const estH = clusterLabelScreenFont + 6;

          // Keep cluster title centered on hull, gently clamped horizontally inside canvas edges when zoomed at overview
          let sx = d.cx * k + tx;
          if (k <= 1.15) {
            sx = clampVal(sx, estW / 2 + 12, viewW - estW / 2 - 12);
          }
          const lx = (sx - tx) / k;
          const ly = d.placeAbove
            ? (d.hullMinY - offsetWorld)
            : (d.hullMaxY + offsetWorld + clusterLabelWorldFont * 0.85);

          d3.select(this).select('path.cluster-hull')
            .style('stroke-width', (1.25 * strokeScale) + 'px');

          d3.select(this).select('text.cluster-title')
            .attr('x', lx)
            .attr('y', ly)
            .attr('text-anchor', 'middle')
            .style('font-size', clusterLabelWorldFont + 'px')
            .style('opacity', isDimmed ? 0.08 : clusterTitleOpacity);

          if (!isDimmed && clusterTitleOpacity > 0.3) {
            const sy = ly * k + ty;
            clusterTitleBoxes.push({
              x1: sx - estW / 2,
              y1: sy - estH + 2,
              x2: sx + estW / 2,
              y2: sy + 4
            });
          }
        });
      }

      // 3. Semantic Zoom + Full-Name-First 4-Quadrant Collision-Free Node Label Placement
      const screenFont = clampVal(9.5 + (k - 0.5) * 2.4, 9.5, 13.5);
      const haloWorldWidth = 3.6 / k;

      const focusId = hoveredNodeId !== null ? String(hoveredNodeId) : (selectedNodeId !== null ? String(selectedNodeId) : null);
      const focusNeighbors = focusId ? getNeighborIdSet(focusId) : new Set();

      // Compute graph centroid for outward-first radial label placement (keeps center web clear)
      let gSumX = 0, gSumY = 0, gCount = 0;
      rawNodes.forEach(n => {
        if (n.x !== undefined && n.y !== undefined) {
          gSumX += n.x;
          gSumY += n.y;
          gCount++;
        }
      });
      const graphMidX = gCount > 0 ? gSumX / gCount : 0;
      const graphMidY = gCount > 0 ? gSumY / gCount : 0;

      // Reserve ALL non-dimmed node circle screen boxes first so NO label ever covers another node
      const occupiedRects = [...clusterTitleBoxes];
      const nodeScreenMeta = new Map();

      nodeElements.each(function(d) {
        const isDimmed = d3.select(this).classed('dimmed');
        const sx = (d.x || 0) * k + tx;
        const sy = (d.y || 0) * k + ty;
        const rScreen = getNodeWorldRadius(d, k) * k;
        nodeScreenMeta.set(String(d.id), { sx, sy, rScreen, isDimmed });
        if (!isDimmed) {
          const pad = 4;
          occupiedRects.push({
            x1: sx - rScreen - pad,
            y1: sy - rScreen - pad,
            x2: sx + rScreen + pad,
            y2: sy + rScreen + pad
          });
        }
      });

      function buildCandidates(meta, estW, estH, labelFontScreen) {
        const gap = meta.rScreen + 6;
        return {
          below: {
            anchor: 'middle',
            x1: meta.sx - estW / 2, y1: meta.sy + gap,
            x2: meta.sx + estW / 2, y2: meta.sy + gap + estH,
            dx: 0, dy: (gap + labelFontScreen * 0.88) / k
          },
          above: {
            anchor: 'middle',
            x1: meta.sx - estW / 2, y1: meta.sy - gap - estH,
            x2: meta.sx + estW / 2, y2: meta.sy - gap,
            dx: 0, dy: -(gap + 4) / k
          },
          right: {
            anchor: 'start',
            x1: meta.sx + gap, y1: meta.sy - estH / 2,
            x2: meta.sx + gap + estW, y2: meta.sy + estH / 2,
            dx: gap / k, dy: (labelFontScreen * 0.34) / k
          },
          left: {
            anchor: 'end',
            x1: meta.sx - gap - estW, y1: meta.sy - estH / 2,
            x2: meta.sx - gap, y2: meta.sy + estH / 2,
            dx: -gap / k, dy: (labelFontScreen * 0.34) / k
          }
        };
      }

      function findBestCandidate(meta, text, labelFontScreen, order) {
        const estW = text.length * labelFontScreen * 0.62 + 10;
        const estH = labelFontScreen + 6;
        const candidates = buildCandidates(meta, estW, estH, labelFontScreen);
        let chosen = null;
        let fallbackInBounds = null;
        let minOverlapChoice = null;
        let minOverlapVal = Infinity;

        for (const dir of order) {
          const cand = candidates[dir];
          let overlapSum = 0;
          let collides = false;
          for (let i = 0; i < occupiedRects.length; i++) {
            if (rectsOverlap(cand, occupiedRects[i])) {
              collides = true;
              overlapSum += rectOverlapArea(cand, occupiedRects[i]);
            }
          }
          const inBounds = cand.x1 >= 6 && cand.x2 <= viewW - 6 && cand.y1 >= 6 && cand.y2 <= viewH - 6;
          if (!collides) {
            if (inBounds) {
              chosen = cand;
              break;
            }
            if (!fallbackInBounds) fallbackInBounds = cand;
          }
          if (overlapSum < minOverlapVal) {
            minOverlapVal = overlapSum;
            minOverlapChoice = cand;
          }
        }
        return {
          chosen: chosen || fallbackInBounds,
          minOverlapChoice: minOverlapChoice || candidates[order[0]],
          estW,
          estH
        };
      }

      // Sort nodes by label display priority
      const prioritized = [...rawNodes].sort((a, b) => getLabelPriority(b, focusId, focusNeighbors) - getLabelPriority(a, focusId, focusNeighbors));
      const placements = new Map();

      prioritized.forEach(d => {
        const idStr = String(d.id);
        const meta = nodeScreenMeta.get(idStr);
        if (!meta) return;

        const isPrimaryFocus = idStr === focusId;
        const isNeighbor = focusNeighbors.has(idStr);
        const isSearchHit = Boolean(activeSearchQuery) && !meta.isDimmed;

        if (meta.isDimmed && !isPrimaryFocus) {
          placements.set(idStr, { visible: false });
          return;
        }

        if (activeLabelMode === 'hubs' && !d.is_hub && !isPrimaryFocus && !isNeighbor && !isSearchHit) {
          placements.set(idStr, { visible: false });
          return;
        }

        const rawName = d.name || '';
        const labelFontScreen = isPrimaryFocus ? Math.min(screenFont + 1.2, 14.5) : screenFont;

        // Order quadrants outward-first from graph centroid so labels sit cleanly away from central edges
        const vx = (d.x || 0) - graphMidX;
        const vy = (d.y || 0) - graphMidY;
        let order;
        if (Math.abs(vx) > Math.abs(vy) * 1.15) {
          order = vx >= 0 ? ['right', 'below', 'above', 'left'] : ['left', 'below', 'above', 'right'];
        } else {
          order = vy >= 0 ? ['below', 'right', 'left', 'above'] : ['above', 'right', 'left', 'below'];
        }

        // Full-name-first placement: show full name whenever it fits without collision; fall back to 18-char truncation only when tight
        let finalText = rawName;
        let result = findBestCandidate(meta, rawName, labelFontScreen, order);
        const forceFull = isPrimaryFocus || isSearchHit || k >= 0.95;

        if (!result.chosen && !forceFull && rawName.length > 18) {
          const shortName = rawName.slice(0, 17) + '…';
          const shortRes = findBestCandidate(meta, shortName, labelFontScreen, order);
          if (shortRes.chosen || activeLabelMode === 'all') {
            finalText = shortName;
            result = shortRes;
          }
        }

        const mustShow = isPrimaryFocus || activeLabelMode === 'all';
        if (result.chosen || mustShow) {
          const pick = result.chosen || result.minOverlapChoice;
          occupiedRects.push({ x1: pick.x1, y1: pick.y1, x2: pick.x2, y2: pick.y2 });
          placements.set(idStr, {
            visible: true,
            text: finalText,
            anchor: pick.anchor,
            dx: pick.dx,
            dy: pick.dy,
            fontWorld: labelFontScreen / k,
            estWWorld: result.estW / k,
            estHWorld: result.estH / k,
            isPrimaryFocus,
            isNeighbor
          });
        } else {
          placements.set(idStr, { visible: false });
        }
      });

      nodeLabelElements.each(function(d) {
        const idStr = String(d.id);
        const p = placements.get(idStr);
        const group = d3.select(this);
        const textEl = group.select('text.node-label-text');
        const bgEl = group.select('rect.node-label-bg');

        if (!p || !p.visible) {
          group.style('opacity', 0);
          bgEl.style('display', 'none');
          return;
        }

        group.style('opacity', 1);
        textEl
          .text(p.text)
          .attr('x', p.dx)
          .attr('y', p.dy)
          .attr('text-anchor', p.anchor)
          .style('font-size', p.fontWorld + 'px')
          .style('stroke-width', haloWorldWidth + 'px')
          .style('font-weight', (p.isPrimaryFocus || d.is_hub) ? '600' : '500');

        if (p.isPrimaryFocus) {
          const padX = 5 / k;
          const padY = 3 / k;
          const boxW = p.estWWorld;
          const boxH = p.estHWorld;
          let bx = p.dx - boxW / 2;
          if (p.anchor === 'start') bx = p.dx - padX;
          else if (p.anchor === 'end') bx = p.dx - boxW + padX;
          const by = p.dy - p.fontWorld * 0.85 - padY * 0.6;
          bgEl
            .style('display', 'block')
            .attr('x', bx)
            .attr('y', by)
            .attr('width', boxW)
            .attr('height', boxH)
            .attr('rx', 4 / k)
            .attr('ry', 4 / k)
            .style('stroke-width', (1 / k) + 'px');
          group.raise();
        } else {
          bgEl.style('display', 'none');
        }
      });

      // 4. Render concise collision-free relationship badges ONLY on active/hovered connected edges
      renderActiveEdgeLabels(focusId, k, tx, ty, occupiedRects);
    }

    function getLabelPriority(d, focusId, focusNeighbors) {
      const idStr = String(d.id);
      if (idStr === focusId) return 10000;
      if (focusNeighbors.has(idStr)) return 5000 + (d.total_degree || 0);
      let score = (d.total_degree || 0) * 15 + Math.log1p(d.stars || 0) * 2;
      if (d.is_hub) score += 400;
      if (d.is_bridge) score += 150;
      return score;
    }

    function getNeighborIdSet(targetIdStr) {
      const set = new Set();
      (rawLinks || []).forEach(l => {
        const sId = String(l.source.id !== undefined ? l.source.id : l.source);
        const tId = String(l.target.id !== undefined ? l.target.id : l.target);
        if (sId === targetIdStr) set.add(tId);
        else if (tId === targetIdStr) set.add(sId);
      });
      return set;
    }

    function renderActiveEdgeLabels(focusId, k, tx, ty, occupiedRects) {
      if (!gEdgeLabels) return;
      if (!focusId) {
        gEdgeLabels.selectAll('*').remove();
        return;
      }

      const candidateLinks = (rawLinks || []).filter(l => {
        const sId = String(l.source.id !== undefined ? l.source.id : l.source);
        const tId = String(l.target.id !== undefined ? l.target.id : l.target);
        if (sId !== focusId && tId !== focusId) return false;
        if (activeEdgeFilter === 'depends_on' && l.type !== 'depends_on') return false;
        if (activeEdgeFilter === 'cross_cluster' && !l.is_cross_cluster) return false;
        if (activeEdgeFilter === 'shares_tech' && l.type !== 'shares_tech') return false;
        return l._midX !== undefined && l._midY !== undefined;
      }).sort((a, b) => {
        const aArch = a.type === 'depends_on' ? 1 : 0;
        const bArch = b.type === 'depends_on' ? 1 : 0;
        if (aArch !== bArch) return bArch - aArch;
        return (b._worldLen || 0) - (a._worldLen || 0);
      });

      const edgeFontScreen = clampVal(8.5 + (k - 0.5) * 1.5, 8.5, 11);
      const edgeFontWorld = edgeFontScreen / k;
      const edgeOccupied = (occupiedRects || []).slice();
      const placedEdges = [];
      const tCandidates = [0.5, 0.36, 0.64];

      candidateLinks.forEach(l => {
        if (placedEdges.length >= 10) return;
        const rawLabel = l.label || l.type || '';
        const text = rawLabel.length > 22 ? rawLabel.slice(0, 21) + '…' : rawLabel;
        const wScreen = text.length * edgeFontScreen * 0.56 + 10;
        const hScreen = edgeFontScreen + 6;
        const screenLen = (l._worldLen || 0) * k;

        // Skip short edges where a midpoint pill would collide with endpoint nodes
        if (screenLen < Math.max(92, wScreen * 0.85)) return;

        let chosenPos = null;
        for (const t of tCandidates) {
          const mt = 1 - t;
          const wx = l._p0x !== undefined
            ? (mt * mt * l._p0x + 2 * mt * t * l._cx + t * t * l._p2x)
            : l._midX;
          const wy = l._p0y !== undefined
            ? (mt * mt * l._p0y + 2 * mt * t * l._cy + t * t * l._p2y)
            : l._midY;
          const sx = wx * k + (tx || 0);
          const sy = wy * k + (ty || 0);
          const rect = {
            x1: sx - wScreen / 2 - 2,
            y1: sy - hScreen / 2 - 2,
            x2: sx + wScreen / 2 + 2,
            y2: sy + hScreen / 2 + 2
          };
          let collides = false;
          for (let i = 0; i < edgeOccupied.length; i++) {
            if (rectsOverlap(rect, edgeOccupied[i])) {
              collides = true;
              break;
            }
          }
          if (!collides) {
            chosenPos = { wx, wy, rect };
            break;
          }
        }

        if (chosenPos) {
          edgeOccupied.push(chosenPos.rect);
          placedEdges.push({
            key: `${l.source.id || l.source}-${l.target.id || l.target}-${l.type}`,
            text,
            wx: chosenPos.wx,
            wy: chosenPos.wy,
            wWorld: wScreen / k,
            hWorld: hScreen / k
          });
        }
      });

      const items = gEdgeLabels.selectAll('g.edge-label-item')
        .data(placedEdges, d => d.key);

      const enter = items.enter().append('g').attr('class', 'edge-label-item');
      enter.append('rect').attr('class', 'edge-label-bg');
      enter.append('text').attr('class', 'edge-label-text').attr('text-anchor', 'middle');

      const merged = enter.merge(items);
      merged.attr('transform', d => `translate(${d.wx},${d.wy})`);

      merged.each(function(d) {
        const gItem = d3.select(this);
        gItem.select('rect.edge-label-bg')
          .attr('x', -d.wWorld / 2)
          .attr('y', -d.hWorld / 2)
          .attr('width', d.wWorld)
          .attr('height', d.hWorld)
          .attr('rx', 3 / k)
          .attr('ry', 3 / k)
          .style('stroke-width', (0.9 / k) + 'px');
        gItem.select('text.edge-label-text')
          .text(d.text)
          .attr('dy', (edgeFontScreen * 0.34) / k)
          .style('font-size', edgeFontWorld + 'px');
      });

      items.exit().remove();
    }

    function refreshGraphHighlights() {
      if (!nodeElements || !linkElements) return;

      const hoverIdStr = hoveredNodeId !== null ? String(hoveredNodeId) : null;
      const selectIdStr = selectedNodeId !== null ? String(selectedNodeId) : null;
      const spotlightId = hoverIdStr;
      const spotlightNeighbors = spotlightId ? getNeighborIdSet(spotlightId) : null;

      nodeElements
        .classed('active', d => selectIdStr !== null && String(d.id) === selectIdStr)
        .classed('hovered', d => hoverIdStr !== null && String(d.id) === hoverIdStr)
        .classed('dimmed', d => {
          const idStr = String(d.id);
          if (spotlightId) {
            return idStr !== spotlightId && !spotlightNeighbors.has(idStr);
          }
          if (activeMatrixPair) {
            return d.cluster_id !== activeMatrixPair.src && d.cluster_id !== activeMatrixPair.tgt;
          }
          if (activeClusterFilter !== 'all' && d.cluster_id !== activeClusterFilter) {
            return true;
          }
          if (activeSearchQuery) {
            const match = (d.name || '').toLowerCase().includes(activeSearchQuery) ||
              (d.description || '').toLowerCase().includes(activeSearchQuery) ||
              (d.primary_language || '').toLowerCase().includes(activeSearchQuery) ||
              (d.topics || []).some(t => t.toLowerCase().includes(activeSearchQuery)) ||
              (d.tech_stack || []).some(t => t.toLowerCase().includes(activeSearchQuery));
            if (!match) return true;
          }
          return false;
        });

      const activeFocusId = hoverIdStr || selectIdStr;
      linkElements.each(function(l) {
        const sId = String(l.source.id !== undefined ? l.source.id : l.source);
        const tId = String(l.target.id !== undefined ? l.target.id : l.target);
        const srcCluster = l.source.cluster_id || l.source_cluster;
        const tgtCluster = l.target.cluster_id || l.target_cluster;

        const connectedToFocus = activeFocusId !== null && (sId === activeFocusId || tId === activeFocusId);
        let dimmed = false;

        if (spotlightId) {
          dimmed = !connectedToFocus;
        } else if (activeMatrixPair) {
          const match = (srcCluster === activeMatrixPair.src && tgtCluster === activeMatrixPair.tgt) ||
                        (srcCluster === activeMatrixPair.tgt && tgtCluster === activeMatrixPair.src);
          dimmed = !match;
        } else {
          if (activeClusterFilter !== 'all' && srcCluster !== activeClusterFilter && tgtCluster !== activeClusterFilter) {
            dimmed = true;
          }
          if (activeSearchQuery) {
            const srcElDimmed = nodeElements.filter(n => String(n.id) === sId).classed('dimmed');
            const tgtElDimmed = nodeElements.filter(n => String(n.id) === tId).classed('dimmed');
            if (srcElDimmed && tgtElDimmed) dimmed = true;
          }
        }

        if (activeEdgeFilter === 'depends_on' && l.type !== 'depends_on') dimmed = true;
        if (activeEdgeFilter === 'cross_cluster' && !l.is_cross_cluster) dimmed = true;
        if (activeEdgeFilter === 'shares_tech' && l.type !== 'shares_tech') dimmed = true;

        const isHighlighted = connectedToFocus && !dimmed;
        d3.select(this)
          .classed('dimmed', dimmed)
          .classed('highlighted', isHighlighted)
          .attr('marker-end', getLinkMarkerUrl(l, isHighlighted));
      });

      if (gClusters) {
        let spotlightClusters = null;
        if (spotlightId) {
          spotlightClusters = new Set();
          (rawNodes || []).forEach(n => {
            const idStr = String(n.id);
            if (idStr === spotlightId || (spotlightNeighbors && spotlightNeighbors.has(idStr))) {
              spotlightClusters.add(n.cluster_id);
            }
          });
        }
        gClusters.selectAll('g.cluster-zone').classed('dimmed', d => {
          if (spotlightClusters) return !spotlightClusters.has(d.id);
          if (activeMatrixPair) return d.id !== activeMatrixPair.src && d.id !== activeMatrixPair.tgt;
          return activeClusterFilter !== 'all' && d.id !== activeClusterFilter;
        });
      }

      updateSemanticZoom();
    }

    /* Shared framing helper with asymmetric top padding to clear the floating controls bar */
    function frameNodes(nodesList, options = {}) {
      if (!nodesList || nodesList.length === 0 || !svg || !d3Zoom) return;
      const container = document.getElementById('graph-container');
      if (!container) return;
      const width = container.clientWidth || 900;
      const height = container.clientHeight || 660;
      const controlsEl = container.querySelector('.graph-controls');
      const controlsHeight = controlsEl ? controlsEl.offsetHeight : 42;

      const padTop = Math.max(options.padTop || 82, controlsHeight + 44);
      const padBottom = options.padBottom || 66;
      const padLeft = options.padLeft || 108;
      const padRight = options.padRight || 108;
      const margin = options.nodeMargin !== undefined ? options.nodeMargin : 76;
      const minScale = options.minScale || 0.16;
      const maxScale = options.maxScale || 1.25;
      const animate = options.animate !== undefined ? options.animate : true;
      const duration = options.duration || 650;

      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      nodesList.forEach(d => {
        if (d.x !== undefined && d.y !== undefined) {
          if (d.x - margin < minX) minX = d.x - margin;
          if (d.x + margin > maxX) maxX = d.x + margin;
          if (d.y - margin < minY) minY = d.y - margin;
          if (d.y + margin > maxY) maxY = d.y + margin;
        }
      });

      if (minX === Infinity) return;

      const boxW = Math.max(maxX - minX, 160);
      const boxH = Math.max(maxY - minY, 160);
      const midX = (minX + maxX) / 2;
      const midY = (minY + maxY) / 2;

      const availW = Math.max(width - padLeft - padRight, 200);
      const availH = Math.max(height - padTop - padBottom, 200);
      const scale = clampVal(Math.min(availW / boxW, availH / boxH), minScale, maxScale);

      const centerX = padLeft + availW / 2;
      const centerY = padTop + availH / 2;
      const transform = d3.zoomIdentity
        .translate(centerX, centerY)
        .scale(scale)
        .translate(-midX, -midY);

      if (animate) {
        svg.transition().duration(duration).call(d3Zoom.transform, transform);
      } else {
        svg.call(d3Zoom.transform, transform);
      }
    }

    /* Auto-fit and frame all clusters and nodes into the main view */
    function zoomToFitAll(animate = true, duration = 650) {
      frameNodes(rawNodes, { animate, duration, minScale: 0.14, maxScale: 1.05, nodeMargin: 82 });
    }

    /* Smoothly zoom and center on a specific thematic cluster */
    function zoomToCluster(clusterId, animate = true, duration = 650) {
      const clusterNodes = (rawNodes || []).filter(d => d.cluster_id === clusterId);
      if (clusterNodes.length === 0) {
        zoomToFitAll(true);
        return;
      }
      frameNodes(clusterNodes, { animate, duration, minScale: 0.45, maxScale: 1.75, nodeMargin: 85 });
    }

    /* Zoom to frame a specific list of nodes */
    function zoomToNodes(nodesList, animate = true, duration = 650) {
      frameNodes(nodesList, { animate, duration, minScale: 0.25, maxScale: 1.55, nodeMargin: 75 });
    }

    /* Zoom in / out smoothly from the bottom-right controls */
    function zoomGraphBy(factor) {
      if (!svg || !d3Zoom) return;
      svg.transition().duration(260).call(d3Zoom.scaleBy, factor);
    }

    function positionTooltip(event) {
      const tooltip = document.getElementById('graph-tooltip');
      const container = document.getElementById('graph-container');
      if (!tooltip || !container) return;
      const rect = container.getBoundingClientRect();
      const tipW = tooltip.offsetWidth || 240;
      const tipH = tooltip.offsetHeight || 100;
      let left = event.clientX - rect.left + 16;
      let top = event.clientY - rect.top - 12;
      if (left + tipW > rect.width - 12) left = Math.max(12, event.clientX - rect.left - tipW - 16);
      if (top + tipH > rect.height - 12) top = Math.max(12, rect.height - tipH - 12);
      if (top < 12) top = 12;
      tooltip.style.left = left + 'px';
      tooltip.style.top = top + 'px';
    }

    function handleNodeMouseOver(event, d) {
      hoveredNodeId = d.id;
      refreshGraphHighlights();

      const tooltip = document.getElementById('graph-tooltip');
      if (!tooltip) return;
      tooltip.style.display = 'block';
      tooltip.innerHTML = `
        <div style="font-weight: 700; color: #38bdf8; margin-bottom: 2px;">${d.name}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">${d.cluster_name}</div>
        <div style="font-size: 0.75rem; line-height: 1.35;">${d.description || 'No description'}</div>
        <div style="margin-top: 6px; font-size: 0.7rem; color: var(--text-dim);">Connections: ${d.total_degree || 0} &middot; ${d.primary_language || 'Other'}</div>
      `;
      positionTooltip(event);
    }

    function handleNodeMouseMove(event) {
      positionTooltip(event);
    }

    function handleNodeMouseOut() {
      hoveredNodeId = null;
      refreshGraphHighlights();
      const tooltip = document.getElementById('graph-tooltip');
      if (tooltip) tooltip.style.display = 'none';
    }

    function selectNode(nodeId) {
      selectedNodeId = nodeId;
      const node = (rawNodes || []).find(n => String(n.id) === String(nodeId) || n.name === nodeId);
      if (!node) return;

      const targetActualId = node.id;
      selectedNodeId = targetActualId;
      refreshGraphHighlights();

      const sidebar = document.getElementById('graph-sidebar');
      if (!sidebar) return;

      const incoming = (rawLinks || []).filter(l => String(l.target.id || l.target) === String(targetActualId));
      const outgoing = (rawLinks || []).filter(l => String(l.source.id || l.source) === String(targetActualId));

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
      const node = (rawNodes || []).find(n => String(n.id) === String(nodeId) || n.name === nodeId);
      if (node && node.x !== undefined && node.y !== undefined && svg && d3Zoom) {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth || 900;
        const height = container.clientHeight || 700;
        const transform = d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(1.45)
          .translate(-node.x, -node.y);
        svg.transition().duration(700).call(d3Zoom.transform, transform);
      }
    }

    /* Filter Graph by Cross-Cluster Matrix Cell and Zoom */
    function filterMatrixCell(srcClusterId, tgtClusterId) {
      switchTab('tab-graph');
      const clusterEl = document.getElementById('graph-cluster-filter');
      const edgeEl = document.getElementById('graph-edge-filter');
      if (clusterEl) clusterEl.value = 'all';
      if (edgeEl) edgeEl.value = 'all';
      activeClusterFilter = 'all';
      activeEdgeFilter = 'all';
      activeMatrixPair = { src: srcClusterId, tgt: tgtClusterId };
      refreshGraphHighlights();

      const cellNodes = rawNodes.filter(d => d.cluster_id === srcClusterId || d.cluster_id === tgtClusterId);
      zoomToNodes(cellNodes, true);
      showToast(`Filtered and focused on ${srcClusterId} -> ${tgtClusterId}`);
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
      activeMatrixPair = null;
      refreshGraphHighlights();
      if (clusterId === 'all') {
        zoomToFitAll(true);
      } else {
        zoomToCluster(clusterId, true);
      }
    }

    function onEdgeFilterChange(edgeType) {
      activeEdgeFilter = edgeType;
      refreshGraphHighlights();
    }

    function onLabelModeChange(mode) {
      activeLabelMode = mode || 'smart';
      updateSemanticZoom();
    }

    function onSpacingModeChange(mode) {
      activeSpacingMode = mode || 'balanced';
      recomputeGraphSpacing();
    }

    function onGraphSearch(query) {
      activeSearchQuery = (query || '').trim().toLowerCase();
      refreshGraphHighlights();
    }

    function applyGraphFilters() {
      refreshGraphHighlights();
    }

    function togglePhysics() {
      isPhysicsPaused = !isPhysicsPaused;
      const btn = document.getElementById('btn-toggle-physics');
      if (isPhysicsPaused) {
        if (simulation) simulation.stop();
        if (btn) btn.textContent = 'Resume Physics';
      } else {
        if (simulation) simulation.alpha(0.25).restart();
        if (btn) btn.textContent = 'Pause Physics';
      }
    }

    function resetGraphView() {
      resetSidebarDrawer();
      const clusterSelect = document.getElementById('graph-cluster-filter');
      if (clusterSelect) clusterSelect.value = 'all';
      const edgeSelect = document.getElementById('graph-edge-filter');
      if (edgeSelect) edgeSelect.value = 'all';
      const searchInput = document.getElementById('graph-search');
      if (searchInput) searchInput.value = '';
      activeClusterFilter = 'all';
      activeEdgeFilter = 'all';
      activeSearchQuery = '';
      activeMatrixPair = null;
      hoveredNodeId = null;
      refreshGraphHighlights();
      zoomToFitAll(true);
      showToast('Graph view reset to show all clusters.');
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
        return (template
                .replace("__TITLE_NAME__", title_name)
                .replace("__TARGET_DISPLAY__", target_display)
                .replace("__INPUT_VALUE__", input_value)
                .replace("__EMBEDDED_JSON__", json_data_str))
