"""
Interactive HTML Dashboard Generator.

Generates a standalone, offline-first, security-hardened, WCAG 2.2 AA accessible
HTML5 application with vendored D3.js v7 force-directed knowledge graphs,
expandable cluster cards, searchable repository data tables, inspection drawers,
a hardened client-side scanner, and a local Repository Matcher and Search tool.
"""

import base64
import hashlib
import html
import json
import os
import re
from typing import Any, Dict

from scripts.security_utils import assert_not_symlink_file, validate_path_safe


class DashboardGenerator:
    """Generates a self-contained interactive HTML5 dashboard."""

    VENDOR_D3_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vendor", "d3.v7.min.js"
    )
    VENDOR_D3_SHA256 = (
        "f2094bbf6141b359722c4fe454eb6c4b0f0e42cc10cc7af921fc158fceb86539"
    )

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir

    @classmethod
    def _load_vendored_d3(cls) -> str:
        """Load vendored D3.js v7 bundle and verify its pinned SHA-256 integrity hash."""
        if not os.path.isfile(cls.VENDOR_D3_PATH):
            raise RuntimeError(
                f"Vendored D3 bundle not found at '{cls.VENDOR_D3_PATH}'."
            )
        with open(cls.VENDOR_D3_PATH, "rb") as f:
            raw_bytes = f.read()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        if actual_sha != cls.VENDOR_D3_SHA256:
            raise RuntimeError(
                f"Vendored D3 SHA-256 integrity mismatch: expected {cls.VENDOR_D3_SHA256}, "
                f"got {actual_sha}."
            )
        script_text = raw_bytes.decode("utf-8")
        if "</script" in script_text.lower():
            raise RuntimeError("Vendored D3 bundle contains unexpected closing script tag.")
        return script_text

    @staticmethod
    def _safe_json_for_script(data: Any) -> str:
        """Serialize JSON safely for embedding inside <script type='application/json'>."""
        raw = json.dumps(data, ensure_ascii=False)
        return (
            raw.replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )

    @staticmethod
    def _csp_sha256(script_body: str) -> str:
        """Compute exact CSP sha256-<base64> token for an inline script block."""
        digest = hashlib.sha256(script_body.encode("utf-8")).digest()
        return f"'sha256-{base64.b64encode(digest).decode('ascii')}'"

    def generate(
        self,
        metadata: Dict[str, Any],
        clusters_data: Dict[str, Any],
        graph_data: Dict[str, Any],
    ) -> str:
        """
        Produce standalone dashboard.html for embedded webview and browser rendering.
        """
        safe_output_dir = validate_path_safe(self.output_dir, for_write=True)
        os.makedirs(safe_output_dir, exist_ok=True)
        dashboard_path = os.path.join(safe_output_dir, "dashboard.html")
        assert_not_symlink_file(dashboard_path)

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
        json_data_str = self._safe_json_for_script(data)
        d3_script_body = self._load_vendored_d3()
        app_script_body = self._get_app_script()

        d3_hash = self._csp_sha256(d3_script_body)
        app_hash = self._csp_sha256(app_script_body)
        csp_content = (
            "default-src 'none'; "
            f"script-src {d3_hash} {app_hash}; "
            "style-src 'unsafe-inline'; "
            "connect-src https://api.github.com; "
            "img-src 'self' data:; "
            "font-src 'none'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'none';"
        )

        owner_name = str(data.get("metadata", {}).get("owner", "") or "")
        target_url = str(data.get("metadata", {}).get("input_url", "") or "")

        if not target_url or target_url == "GitHub Target":
            target_display = "Target: None (Enter a GitHub URL above to scan)"
            input_value = ""
        else:
            target_display = f"Target: {target_url}"
            input_value = target_url

        if not owner_name or owner_name == "Repository Organization":
            title_name = "Repository Architecture Dashboard"
        else:
            title_name = f"Repository Architecture Dashboard - {owner_name}"

        template = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Security-Policy" content="__CSP_CONTENT__" />
  <meta name="referrer" content="no-referrer" />
  <title>__TITLE_NAME__</title>
  <style>
    :root {
      --bg-base: #0f172a;
      --bg-surface: #1e293b;
      --bg-surface-elevated: #293548;
      --bg-surface-subtle: rgba(30, 41, 59, 0.90);
      --border-color: #475569;
      --border-control: #7c8ea6;
      --border-hover: #3b4b63;
      --text-main: #f8fafc;
      --text-muted: #cbd5e1;
      --text-dim: #94a3b8;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-text: #60a5fa;
      --accent-text: #22d3ee;
      --tag-text: #93c5fd;
      --tag-tech-text: #6ee7b7;
      --success-text: #34d399;
      --warning-text: #fbbf24;
      --danger-text: #fca5a5;
      --danger-bg: #3b1720;
      --danger-border: #f87171;
      --tooltip-title: #38bdf8;
      --focus-ring: #38bdf8;
      --matrix-active-bg: #1e3a5f;
      --matrix-active-text: #e0f2fe;
      --graph-link-stroke: #7c8ea6;
      --graph-link-cross: #94a3b8;
      --graph-link-weak: #64748b;
      --graph-node-stroke: #0f172a;
      --graph-hub-stroke: #fbbf24;
      --graph-label-halo: rgba(15, 23, 42, 0.94);
      --graph-pill-bg: rgba(15, 23, 42, 0.94);
      --font-sans: system-ui, ui-sans-serif, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, "Liberation Mono", "DejaVu Sans Mono", monospace;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.08);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.16), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.32);
    }

    [data-theme="light"] {
      --bg-base: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #eef2f6;
      --bg-surface-subtle: rgba(255, 255, 255, 0.94);
      --border-color: #cbd5e1;
      --border-control: #64748b;
      --border-hover: #dbe4ef;
      --text-main: #0f172a;
      --text-muted: #334155;
      --text-dim: #475569;
      --primary: #1d4ed8;
      --primary-hover: #1e40af;
      --primary-text: #1d4ed8;
      --accent-text: #0e7490;
      --tag-text: #1e40af;
      --tag-tech-text: #065f46;
      --success-text: #065f46;
      --warning-text: #92400e;
      --danger-text: #b91c1c;
      --danger-bg: #fef2f2;
      --danger-border: #b91c1c;
      --tooltip-title: #0369a1;
      --focus-ring: #1d4ed8;
      --matrix-active-bg: #dbeafe;
      --matrix-active-text: #1e3a8a;
      --graph-link-stroke: #475569;
      --graph-link-cross: #334155;
      --graph-link-weak: #64748b;
      --graph-node-stroke: #ffffff;
      --graph-hub-stroke: #b45309;
      --graph-label-halo: rgba(248, 250, 252, 0.95);
      --graph-pill-bg: rgba(255, 255, 255, 0.96);
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

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    .skip-link {
      position: absolute;
      left: 12px;
      top: -60px;
      z-index: 1000;
      background-color: var(--primary);
      color: #ffffff;
      padding: 8px 14px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.88rem;
      text-decoration: none;
      border: 2px solid #ffffff;
    }

    .skip-link:focus {
      top: 12px;
    }

    a:focus-visible,
    button:focus-visible,
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    [tabindex]:focus-visible {
      outline: 2px solid var(--focus-ring);
      outline-offset: 2px;
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
      gap: 12px;
      flex-wrap: wrap;
    }

    .topbar-brand {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .topbar-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-main);
      line-height: 1.3;
    }

    .topbar-subtitle {
      font-size: 0.78rem;
      color: var(--text-muted);
      overflow-wrap: anywhere;
    }

    .scan-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      background-color: var(--bg-base);
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-control);
      flex: 1 1 240px;
      max-width: 520px;
      min-width: 0;
    }

    .scan-bar:focus-within {
      border-color: var(--focus-ring);
    }

    .scan-input {
      flex: 1;
      min-width: 0;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 0.85rem;
      font-family: var(--font-mono);
      padding: 4px 6px;
      min-height: 28px;
    }

    .scan-input::placeholder {
      color: var(--text-dim);
    }

    .btn {
      padding: 6px 12px;
      min-height: 30px;
      min-width: 28px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 5px;
      border: 1px solid var(--border-control);
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      cursor: pointer;
      transition: background-color 0.15s ease, border-color 0.15s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
    }

    .btn:hover {
      background-color: var(--border-hover);
      border-color: var(--text-muted);
    }

    .btn:disabled {
      opacity: 0.65;
      cursor: not-allowed;
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
      padding: 4px 10px;
      min-height: 28px;
      font-size: 0.78rem;
    }

    .topbar-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }

    .topbar-actions select {
      max-width: 100%;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 160px), 1fr));
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
      transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .metric-card:hover {
      border-color: var(--primary-text);
      transform: translateY(-2px);
    }

    .metric-label {
      font-size: 0.74rem;
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
      font-size: 0.76rem;
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
      flex-wrap: wrap;
    }

    .tab-btn {
      padding: 8px 14px;
      min-height: 36px;
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      color: var(--text-muted);
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: color 0.15s ease, border-color 0.15s ease;
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: var(--text-main);
    }

    .tab-btn.active {
      color: var(--primary-text);
      border-bottom-color: var(--primary-text);
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
      .graph-sidebar {
        border-left: none;
        border-top: 1px solid var(--border-color);
      }
    }

    .graph-viewport-container {
      position: relative;
      width: 100%;
      height: 100%;
      min-height: 520px;
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
      gap: 6px;
      background-color: var(--bg-surface-subtle);
      padding: 6px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-control);
      z-index: 10;
      backdrop-filter: blur(8px);
    }

    .graph-controls select,
    .graph-controls input {
      padding: 4px 6px;
      min-height: 28px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-control);
      color: var(--text-main);
      border-radius: 4px;
      font-size: 0.76rem;
      max-width: 100%;
    }

    .graph-controls input#graph-search {
      width: 148px;
    }

    .graph-controls .btn-sm {
      padding: 4px 8px;
      font-size: 0.76rem;
    }

    .graph-zoom-bar {
      position: absolute;
      bottom: 14px;
      right: 14px;
      display: flex;
      align-items: center;
      gap: 4px;
      background-color: var(--bg-surface-subtle);
      border: 1px solid var(--border-control);
      border-radius: 6px;
      padding: 4px 6px;
      z-index: 10;
      backdrop-filter: blur(8px);
      box-shadow: var(--shadow-md);
    }

    .zoom-btn {
      min-width: 28px;
      min-height: 28px;
      border: 1px solid var(--border-control);
      border-radius: 4px;
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      font-size: 0.9rem;
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
      font-size: 0.76rem;
      font-weight: 600;
    }

    .zoom-level {
      min-width: 44px;
      text-align: center;
      font-family: var(--font-mono);
      font-size: 0.76rem;
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
      fill-opacity: 0.08;
      stroke-opacity: 0.30;
      stroke-dasharray: 5, 4;
      cursor: pointer;
      transition: fill-opacity 0.2s ease, stroke-opacity 0.2s ease;
    }

    .cluster-hull:hover {
      fill-opacity: 0.14;
      stroke-opacity: 0.50;
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
      stroke-opacity: 0.48;
      stroke-linecap: round;
      transition: stroke-opacity 0.2s ease, opacity 0.2s ease;
    }

    .graph-link.cross-cluster {
      stroke: var(--graph-link-cross);
      stroke-opacity: 0.40;
      stroke-dasharray: 5, 4;
    }

    .graph-link.weak-link {
      stroke: var(--graph-link-weak);
      stroke-opacity: 0.24;
      stroke-dasharray: 2.5, 3.5;
    }

    .graph-link.highlighted {
      stroke: var(--focus-ring) !important;
      stroke-opacity: 0.95 !important;
      stroke-dasharray: none !important;
    }

    .graph-link.dimmed {
      opacity: 0.05;
    }

    .edge-labels-layer {
      pointer-events: none;
    }

    .edge-label-bg {
      fill: var(--graph-pill-bg);
      stroke: var(--border-control);
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

    .graph-node:focus {
      outline: none;
    }

    .graph-node:focus-visible circle.node-circle {
      stroke: var(--focus-ring) !important;
      stroke-width: 4px !important;
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
      stroke: var(--border-control);
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
      line-height: 1.45;
    }

    .sidebar-link-btn {
      width: 100%;
      text-align: left;
      cursor: pointer;
      padding: 8px 10px;
      min-height: 36px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-control);
      border-radius: 5px;
      font-size: 0.8rem;
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      gap: 2px;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .sidebar-link-btn:hover {
      background: var(--border-hover);
      border-color: var(--primary-text);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 8px;
      font-size: 0.74rem;
      font-weight: 600;
      border-radius: 4px;
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
      border: 1px solid var(--border-control);
    }

    .color-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
      border: 1px solid rgba(15, 23, 42, 0.35);
    }

    .badge-hub {
      color: var(--warning-text);
      border-color: var(--warning-text);
    }

    .badge-bridge {
      color: var(--accent-text);
      border-color: var(--accent-text);
    }

    .badge-high {
      color: var(--success-text);
      border-color: var(--success-text);
    }

    .badge-moderate {
      color: var(--warning-text);
      border-color: var(--warning-text);
    }

    .tag {
      display: inline-block;
      padding: 2px 7px;
      font-size: 0.72rem;
      border-radius: 3px;
      background-color: var(--bg-surface-elevated);
      color: var(--tag-text);
      margin: 2px;
      font-family: var(--font-mono);
      border: 1px solid var(--border-control);
    }

    .tag-tech {
      color: var(--tag-tech-text);
    }

    .ext-link {
      color: var(--primary-text);
      text-decoration: underline;
      text-underline-offset: 2px;
    }

    .ext-link:hover {
      color: var(--text-main);
    }

    /* Query Matcher Tab */
    .matcher-container {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: var(--shadow-sm);
    }

    .matcher-search-box {
      display: flex;
      gap: 10px;
      align-items: stretch;
      flex-wrap: wrap;
    }

    .matcher-input {
      flex: 1 1 220px;
      min-width: 0;
      padding: 10px 14px;
      min-height: 40px;
      background-color: var(--bg-base);
      border: 1px solid var(--border-control);
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
      padding: 5px 12px;
      min-height: 30px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-control);
      border-radius: 20px;
      color: var(--text-main);
      font-size: 0.8rem;
      cursor: pointer;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .chip-btn:hover {
      background-color: var(--border-hover);
      border-color: var(--primary-text);
    }

    .matcher-result-card {
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-control);
      border-radius: 8px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .matcher-no-match {
      background: var(--danger-bg);
      border: 1px solid var(--danger-border);
      padding: 18px;
      border-radius: 8px;
    }

    .matcher-alt-btn {
      background: none;
      border: none;
      padding: 2px 4px;
      min-height: 28px;
      color: var(--primary-text);
      font-weight: 700;
      font-size: 0.84rem;
      cursor: pointer;
      text-decoration: underline;
      text-align: left;
    }

    /* Cluster Cards Grid */
    .cluster-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
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
      transition: border-color 0.15s ease, transform 0.15s ease;
      border-left-width: 4px;
      box-shadow: var(--shadow-sm);
    }

    .cluster-card:hover {
      border-color: var(--border-control);
      transform: translateY(-2px);
    }

    .cluster-card-toggle {
      width: 100%;
      background: none;
      border: none;
      padding: 0;
      text-align: left;
      color: inherit;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .cluster-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
      width: 100%;
    }

    .cluster-card-title {
      font-size: 1rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .cluster-card-desc {
      font-size: 0.84rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    .cluster-card-stats {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      font-size: 0.8rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border-color);
      padding-top: 10px;
      width: 100%;
    }

    .cluster-repos-list {
      display: none;
      margin-top: 4px;
      padding-top: 10px;
      border-top: 1px dashed var(--border-control);
    }

    .cluster-card.expanded .cluster-repos-list {
      display: block;
    }

    .cluster-repo-item {
      width: 100%;
      font-size: 0.82rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 10px;
      min-height: 32px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-control);
      border-radius: 4px;
      color: var(--text-main);
      cursor: pointer;
      text-align: left;
      transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .cluster-repo-item:hover {
      background: var(--border-hover);
      border-color: var(--primary-text);
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
      flex: 1 1 200px;
      min-width: 0;
      padding: 6px 10px;
      min-height: 34px;
      background-color: var(--bg-base);
      border: 1px solid var(--border-control);
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
      padding: 8px 12px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      user-select: none;
    }

    .table-sort-btn {
      background: none;
      border: none;
      color: var(--text-main);
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      padding: 4px 2px;
      min-height: 28px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .table-sort-btn:hover {
      color: var(--primary-text);
    }

    table.data-table td {
      padding: 10px 12px;
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

    .matrix-table th,
    .matrix-table td {
      border: 1px solid var(--border-color);
      padding: 6px 8px;
      text-align: center;
    }

    .matrix-table th {
      background-color: var(--bg-surface-elevated);
      color: var(--text-main);
    }

    .matrix-table th[scope="row"] {
      text-align: left;
      font-weight: 600;
    }

    .matrix-cell-active {
      background-color: var(--matrix-active-bg);
      padding: 2px;
    }

    .matrix-cell-btn {
      width: 100%;
      min-width: 28px;
      min-height: 28px;
      background-color: transparent;
      border: 1px solid transparent;
      border-radius: 4px;
      color: var(--matrix-active-text);
      font-weight: 700;
      font-size: 0.84rem;
      cursor: pointer;
    }

    .matrix-cell-btn:hover {
      background-color: var(--primary);
      color: #ffffff;
    }

    .graph-tooltip {
      position: absolute;
      padding: 8px 12px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-control);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 0.8rem;
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
      border: 1px solid var(--border-control);
      box-shadow: var(--shadow-lg);
      z-index: 999;
      font-size: 0.84rem;
      display: none;
      max-width: calc(100vw - 40px);
    }

    .site-footer {
      border-top: 1px solid var(--border-color);
      background-color: var(--bg-surface);
      padding: 12px 20px;
      font-size: 0.78rem;
      color: var(--text-dim);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    @media (max-width: 640px) {
      .topbar {
        padding: 10px 12px;
      }
      .metric-grid {
        padding: 12px;
      }
      .main-container {
        padding: 0 12px 24px;
      }
      .scan-bar {
        flex-basis: 100%;
        max-width: 100%;
      }
      .topbar-actions {
        width: 100%;
      }
      .graph-controls input#graph-search {
        width: 100%;
      }
      .site-footer {
        padding: 12px;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
      .metric-card:hover,
      .cluster-card:hover {
        transform: none;
      }
    }
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- Top Navigation & Scanning Bar -->
  <header class="topbar">
    <div class="topbar-brand">
      <h1 class="topbar-title">Repository Architecture Dashboard</h1>
      <div class="topbar-subtitle" id="active-target-display">__TARGET_DISPLAY__</div>
    </div>

    <!-- Live Address Scan Input -->
    <div class="scan-bar" role="search" aria-label="Scan public GitHub target">
      <label for="scan-target-input" class="sr-only">Public GitHub organization, user, or repository URL</label>
      <input
        type="text"
        id="scan-target-input"
        class="scan-input"
        value="__INPUT_VALUE__"
        placeholder="Public GitHub Org or Repo URL (e.g. github.com/pallets)"
      />
      <button type="button" id="btn-scan-address" class="btn btn-primary btn-sm">Scan Address</button>
    </div>

    <div class="topbar-actions">
      <label for="preset-selector" class="sr-only">Select dataset preset</label>
      <select id="preset-selector" class="btn btn-sm">
        <option value="current">Current Scanned Dataset</option>
        <option value="synthetic">Synthetic Multi-Domain Demo (16 Repos)</option>
        <option value="pallets">Pallets Org (Live GitHub Fetch)</option>
        <option value="fastapi">FastAPI Ecosystem (Live GitHub Fetch)</option>
      </select>
      <button type="button" id="btn-toggle-theme" class="btn btn-sm" aria-pressed="false" aria-label="Switch to light theme">Theme</button>
      <button type="button" id="btn-export-json" class="btn btn-sm">Export JSON</button>
      <button type="button" id="btn-print-view" class="btn btn-primary btn-sm">Print View</button>
    </div>
  </header>

  <!-- Metric Summary Cards -->
  <section class="metric-grid" id="metric-summary-container" aria-label="Repository portfolio metrics">
    <!-- Populated dynamically -->
  </section>

  <!-- Main Container with Tabs -->
  <main id="main-content" class="main-container" tabindex="-1">
    <div class="nav-tabs" role="tablist" aria-label="Dashboard sections">
      <button type="button" class="tab-btn active" role="tab" id="btn-tab-graph" aria-selected="true" aria-controls="tab-graph" tabindex="0" data-tab="tab-graph">Knowledge Graph</button>
      <button type="button" class="tab-btn" role="tab" id="btn-tab-matcher" aria-selected="false" aria-controls="tab-matcher" tabindex="-1" data-tab="tab-matcher">Repository Matcher &amp; Chat</button>
      <button type="button" class="tab-btn" role="tab" id="btn-tab-clusters" aria-selected="false" aria-controls="tab-clusters" tabindex="-1" data-tab="tab-clusters">Cluster Explorer</button>
      <button type="button" class="tab-btn" role="tab" id="btn-tab-repos" aria-selected="false" aria-controls="tab-repos" tabindex="-1" data-tab="tab-repos">Repository Catalog</button>
      <button type="button" class="tab-btn" role="tab" id="btn-tab-matrix" aria-selected="false" aria-controls="tab-matrix" tabindex="-1" data-tab="tab-matrix">Cross-Domain Flow</button>
      <button type="button" class="tab-btn" role="tab" id="btn-tab-raw" aria-selected="false" aria-controls="tab-raw" tabindex="-1" data-tab="tab-raw">Raw JSON &amp; Config</button>
    </div>

    <!-- TAB 1: KNOWLEDGE GRAPH -->
    <div id="tab-graph" class="tab-pane active" role="tabpanel" aria-labelledby="btn-tab-graph">
      <h2 class="sr-only">Interactive Repository Knowledge Graph</h2>
      <div class="graph-layout">
        <div class="graph-viewport-container" id="graph-container">
          <div class="graph-controls" role="toolbar" aria-label="Graph filters and layout controls">
            <label for="graph-search" class="sr-only">Search graph nodes or technologies</label>
            <input type="text" id="graph-search" placeholder="Search node or tech..." />
            <label for="graph-cluster-filter" class="sr-only">Filter graph by domain cluster</label>
            <select id="graph-cluster-filter">
              <option value="all">All Clusters</option>
            </select>
            <label for="graph-edge-filter" class="sr-only">Filter graph by relationship type</label>
            <select id="graph-edge-filter">
              <option value="all">All Relationships</option>
              <option value="depends_on">Dependencies Only</option>
              <option value="cross_cluster">Cross-Cluster Only</option>
              <option value="shares_tech">Shared Tech Stack</option>
            </select>
            <label for="graph-label-mode" class="sr-only">Node label visibility mode</label>
            <select id="graph-label-mode" title="Node label visibility mode">
              <option value="smart" selected>Labels: Smart (Zoom)</option>
              <option value="all">Labels: All</option>
              <option value="hubs">Labels: Hubs &amp; Hover</option>
            </select>
            <label for="graph-spacing-mode" class="sr-only">Node and cluster spacing mode</label>
            <select id="graph-spacing-mode" title="Node &amp; cluster spacing">
              <option value="balanced" selected>Spacing: Balanced</option>
              <option value="wide">Spacing: Wide</option>
              <option value="compact">Spacing: Compact</option>
            </select>
            <button type="button" id="btn-reset-graph" class="btn btn-sm">Reset View</button>
            <button type="button" class="btn btn-sm" id="btn-toggle-physics" aria-pressed="false">Pause Physics</button>
          </div>
          <svg class="graph-svg" id="graph-svg" role="img" aria-labelledby="graph-svg-title graph-svg-desc">
            <title id="graph-svg-title">Repository Architecture Knowledge Graph</title>
            <desc id="graph-svg-desc">Interactive force-directed graph showing repositories grouped by domain clusters and connected by dependencies. Tab through nodes and press Enter or Space to inspect repository details.</desc>
          </svg>
          <div class="graph-zoom-bar" role="group" aria-label="Graph zoom controls">
            <button type="button" id="btn-zoom-in" class="zoom-btn" title="Zoom In" aria-label="Zoom in">+</button>
            <span class="zoom-level" id="graph-zoom-level" aria-live="polite">100%</span>
            <button type="button" id="btn-zoom-out" class="zoom-btn" title="Zoom Out" aria-label="Zoom out">-</button>
            <button type="button" id="btn-zoom-fit" class="zoom-btn zoom-btn-fit" title="Fit All Clusters" aria-label="Fit all clusters in view">Fit</button>
          </div>
          <div class="graph-tooltip" id="graph-tooltip" role="tooltip" style="display: none;"></div>
        </div>

        <aside class="graph-sidebar" id="graph-sidebar" aria-label="Selected repository inspector">
          <div class="drawer-empty">
            Select any node or repository in the graph to inspect architectural dependencies, technology stack, and cluster connections.
          </div>
        </aside>
      </div>
    </div>

    <!-- TAB 2: REPOSITORY MATCHER & CHAT -->
    <div id="tab-matcher" class="tab-pane" role="tabpanel" aria-labelledby="btn-tab-matcher">
      <div class="matcher-container">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px;">Repository Matcher &amp; Capability Search</h2>
          <p style="font-size: 0.86rem; color: var(--text-muted);">
            Describe what program, library, or software functionality you need. The matcher evaluates all repositories in this organization locally to find the best match or report if none fits.
          </p>
        </div>

        <div class="matcher-search-box">
          <label for="matcher-query-input" class="sr-only">Describe the repository capability you need</label>
          <input
            type="text"
            id="matcher-query-input"
            class="matcher-input"
            placeholder="e.g., 'Python SDK for platform API', 'OAuth2 authentication service', 'Video transcoding'..."
          />
          <button type="button" id="btn-run-matcher" class="btn btn-primary">Find Best Repository</button>
        </div>

        <div class="chips-container" role="group" aria-label="Example capability queries">
          <span style="font-size: 0.8rem; color: var(--text-dim);">Suggestions:</span>
          <button type="button" class="chip-btn" data-chip-query="Patient clinical EHR records and FHIR">Patient EHR Records</button>
          <button type="button" class="chip-btn" data-chip-query="DNA and RNA bioinformatics genomics pipeline">Genomics Sequencing</button>
          <button type="button" class="chip-btn" data-chip-query="OAuth2 and user login authentication service">User Authentication</button>
          <button type="button" class="chip-btn" data-chip-query="Subscription billing and payment webhooks">Subscription Billing</button>
          <button type="button" class="chip-btn" data-chip-query="Python client SDK for platform API automation">Python Client SDK</button>
          <button type="button" class="chip-btn" data-chip-query="Terraform and Kubernetes cloud infrastructure">Terraform DevOps</button>
          <button type="button" class="chip-btn" data-chip-query="Blockchain cryptocurrency mining smart contract">Crypto Mining (Non-matching demo)</button>
        </div>

        <div id="matcher-result-area" aria-live="polite">
          <div style="text-align: center; color: var(--text-dim); padding: 30px; font-size: 0.88rem;">
            Type a capability request above or select a suggestion chip to find the best-suited repository.
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: CLUSTERS EXPLORER -->
    <div id="tab-clusters" class="tab-pane" role="tabpanel" aria-labelledby="btn-tab-clusters">
      <h2 class="sr-only">Domain Cluster Explorer</h2>
      <div class="cluster-grid" id="cluster-cards-container">
        <!-- Populated by JS -->
      </div>
    </div>

    <!-- TAB 4: REPOSITORY CATALOG -->
    <div id="tab-repos" class="tab-pane" role="tabpanel" aria-labelledby="btn-tab-repos">
      <h2 class="sr-only">Repository Catalog</h2>
      <div class="table-container">
        <div class="table-controls">
          <label for="repo-table-search" class="sr-only">Filter repositories by name, language, or topic</label>
          <input type="text" class="table-search" id="repo-table-search" placeholder="Filter repositories by name, language, or topic..." />
          <label for="table-cluster-filter" class="sr-only">Filter catalog by domain cluster</label>
          <select id="table-cluster-filter" class="table-search" style="max-width: 220px;">
            <option value="all">All Clusters</option>
          </select>
        </div>
        <table class="data-table" id="repo-data-table">
          <caption class="sr-only">Scanned repositories with domain cluster, primary language, stars, graph connections, and architectural role</caption>
          <thead>
            <tr>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="0">Repository</button></th>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="1">Cluster</button></th>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="2">Language</button></th>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="3">Stars</button></th>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="4">Connections</button></th>
              <th scope="col" aria-sort="none"><button type="button" class="table-sort-btn" data-sort-col="5">Role</button></th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody id="repo-table-body">
            <!-- Populated by JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 5: CROSS-DOMAIN FLOW MATRIX -->
    <div id="tab-matrix" class="tab-pane" role="tabpanel" aria-labelledby="btn-tab-matrix">
      <div style="background-color: var(--bg-surface); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color);">
        <h2 style="margin-bottom: 8px; font-size: 1.15rem;">Inter-Cluster Architecture Connectivity Matrix</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 16px;">
          Rows represent source domain origins; columns represent target domain interfaces. Activate any non-zero cell to filter connections on the graph.
        </p>
        <div id="matrix-container" style="overflow-x: auto;">
          <!-- Populated by JS -->
        </div>
      </div>
    </div>

    <!-- TAB 6: RAW JSON & CONFIG -->
    <div id="tab-raw" class="tab-pane" role="tabpanel" aria-labelledby="btn-tab-raw">
      <div style="background-color: var(--bg-surface); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;">
          <h2 style="font-size: 1.15rem;">Raw Knowledge Base Payload</h2>
          <button type="button" id="btn-copy-json" class="btn btn-sm btn-primary">Copy JSON</button>
        </div>
        <label for="raw-json-viewer" class="sr-only">Raw knowledge base JSON payload</label>
        <textarea id="raw-json-viewer" readonly style="width: 100%; height: 420px; font-family: var(--font-mono); font-size: 0.82rem; background: var(--bg-base); color: var(--text-main); border: 1px solid var(--border-control); border-radius: 6px; padding: 12px;"></textarea>
      </div>
    </div>
  </main>

  <footer class="site-footer" role="contentinfo">
    <span>Offline-first dashboard: zero cookies, zero browser storage, and zero external requests on load.</span>
    <span>Live scanning ("Scan Address" or live presets) sends requests directly to <code>https://api.github.com</code>.</span>
  </footer>

  <div id="toast" class="toast-msg" role="status" aria-live="polite" aria-atomic="true"></div>

  <script id="kb-data" type="application/json">__EMBEDDED_JSON__</script>
  <script>__D3_SCRIPT__</script>
  <script>__APP_SCRIPT__</script>
</body>
</html>
"""
        replacements = {
            "__CSP_CONTENT__": csp_content,
            "__TITLE_NAME__": html.escape(title_name, quote=True),
            "__TARGET_DISPLAY__": html.escape(target_display, quote=True),
            "__INPUT_VALUE__": html.escape(input_value, quote=True),
            "__EMBEDDED_JSON__": json_data_str,
            "__D3_SCRIPT__": d3_script_body,
            "__APP_SCRIPT__": app_script_body,
        }
        return re.sub(
            r"__[A-Z0-9_]+__",
            lambda match: replacements.get(match.group(0), match.group(0)),
            template,
        )

    @staticmethod
    def _get_app_script() -> str:
        return r"""
    const kbDataElement = document.getElementById('kb-data');
    let KB_DATA = kbDataElement ? JSON.parse(kbDataElement.textContent) : {};
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
    let isScanning = false;
    let activeClusterFilter = 'all';
    let activeEdgeFilter = 'all';
    let activeLabelMode = 'smart';
    let activeSpacingMode = 'balanced';
    let activeSearchQuery = '';
    let activeMatrixPair = null;
    let toastTimer = null;

    const HEX_COLOR_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
    const OWNER_RE = /^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,38})$/;
    const REPO_RE = /^[A-Za-z0-9._-]{1,100}$/;

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

    /* Security & Rendering Sanitization Helpers */
    function escapeHtml(value) {
      if (value === null || value === undefined) return '';
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/`/g, '&#96;');
    }

    function sanitizeUrl(url) {
      if (typeof url !== 'string') return '#';
      const trimmed = url.trim();
      if (!trimmed) return '#';
      try {
        const parsed = new URL(trimmed);
        if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
          return parsed.href;
        }
      } catch (e) {
        return '#';
      }
      return '#';
    }

    function sanitizeColor(color, fallback = '#3B82F6') {
      if (typeof color === 'string' && HEX_COLOR_RE.test(color.trim())) {
        return color.trim();
      }
      return fallback;
    }

    function renderClusterBadgeHtml(name, color) {
      const safeColor = sanitizeColor(color, '#3B82F6');
      return `<span class="badge cluster-badge"><span class="color-dot" style="background-color: ${safeColor};" aria-hidden="true"></span><span>${escapeHtml(name || 'General')}</span></span>`;
    }

    function renderSafeLinkHtml(url, labelText, className = 'ext-link') {
      const safeHref = sanitizeUrl(url);
      if (safeHref === '#') {
        return `<span>${escapeHtml(labelText)}</span>`;
      }
      return `<a href="${escapeHtml(safeHref)}" target="_blank" rel="noopener noreferrer" class="${className}">${escapeHtml(labelText)}<span class="sr-only"> (opens in new tab)</span></a>`;
    }

    function prefersReducedMotion() {
      return Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }

    document.addEventListener('DOMContentLoaded', () => {
      bindStaticEvents();
      refreshAllViews();
    });

    function bindStaticEvents() {
      const scanInput = document.getElementById('scan-target-input');
      if (scanInput) {
        scanInput.addEventListener('keydown', (event) => {
          if (event.key === 'Enter') scanAddressInput();
        });
      }

      const btnScan = document.getElementById('btn-scan-address');
      if (btnScan) btnScan.addEventListener('click', () => scanAddressInput());

      const presetSelector = document.getElementById('preset-selector');
      if (presetSelector) {
        presetSelector.addEventListener('change', (event) => onPresetChange(event.target.value));
      }

      const btnTheme = document.getElementById('btn-toggle-theme');
      if (btnTheme) btnTheme.addEventListener('click', () => toggleTheme());

      const btnExport = document.getElementById('btn-export-json');
      if (btnExport) btnExport.addEventListener('click', () => exportDataJson());

      const btnPrint = document.getElementById('btn-print-view');
      if (btnPrint) btnPrint.addEventListener('click', () => window.print());

      // Accessible ARIA tab switching + Arrow/Home/End keyboard navigation
      const tabButtons = Array.from(document.querySelectorAll('.tab-btn[role="tab"]'));
      tabButtons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
          const tabId = btn.getAttribute('data-tab');
          if (tabId) switchTab(tabId);
        });
        btn.addEventListener('keydown', (event) => {
          let nextIdx = null;
          if (event.key === 'ArrowRight') nextIdx = (index + 1) % tabButtons.length;
          else if (event.key === 'ArrowLeft') nextIdx = (index - 1 + tabButtons.length) % tabButtons.length;
          else if (event.key === 'Home') nextIdx = 0;
          else if (event.key === 'End') nextIdx = tabButtons.length - 1;
          if (nextIdx !== null) {
            event.preventDefault();
            const targetBtn = tabButtons[nextIdx];
            const tabId = targetBtn.getAttribute('data-tab');
            if (tabId) switchTab(tabId);
            targetBtn.focus();
          }
        });
      });

      const graphSearch = document.getElementById('graph-search');
      if (graphSearch) graphSearch.addEventListener('input', (e) => onGraphSearch(e.target.value));

      const graphClusterFilter = document.getElementById('graph-cluster-filter');
      if (graphClusterFilter) graphClusterFilter.addEventListener('change', (e) => onClusterFilterChange(e.target.value));

      const graphEdgeFilter = document.getElementById('graph-edge-filter');
      if (graphEdgeFilter) graphEdgeFilter.addEventListener('change', (e) => onEdgeFilterChange(e.target.value));

      const graphLabelMode = document.getElementById('graph-label-mode');
      if (graphLabelMode) graphLabelMode.addEventListener('change', (e) => onLabelModeChange(e.target.value));

      const graphSpacingMode = document.getElementById('graph-spacing-mode');
      if (graphSpacingMode) graphSpacingMode.addEventListener('change', (e) => onSpacingModeChange(e.target.value));

      const btnResetGraph = document.getElementById('btn-reset-graph');
      if (btnResetGraph) btnResetGraph.addEventListener('click', () => resetGraphView());

      const btnTogglePhysics = document.getElementById('btn-toggle-physics');
      if (btnTogglePhysics) btnTogglePhysics.addEventListener('click', () => togglePhysics());

      const btnZoomIn = document.getElementById('btn-zoom-in');
      if (btnZoomIn) btnZoomIn.addEventListener('click', () => zoomGraphBy(1.35));

      const btnZoomOut = document.getElementById('btn-zoom-out');
      if (btnZoomOut) btnZoomOut.addEventListener('click', () => zoomGraphBy(0.74));

      const btnZoomFit = document.getElementById('btn-zoom-fit');
      if (btnZoomFit) btnZoomFit.addEventListener('click', () => zoomToFitAll(true));

      const matcherInput = document.getElementById('matcher-query-input');
      if (matcherInput) {
        matcherInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') executeMatcherQuery();
        });
      }

      const btnRunMatcher = document.getElementById('btn-run-matcher');
      if (btnRunMatcher) btnRunMatcher.addEventListener('click', () => executeMatcherQuery());

      document.querySelectorAll('.chip-btn[data-chip-query]').forEach((chip) => {
        chip.addEventListener('click', () => {
          setQueryChip(chip.getAttribute('data-chip-query') || '');
        });
      });

      const repoTableSearch = document.getElementById('repo-table-search');
      if (repoTableSearch) repoTableSearch.addEventListener('input', () => filterRepoTable());

      const tableClusterFilter = document.getElementById('table-cluster-filter');
      if (tableClusterFilter) tableClusterFilter.addEventListener('change', () => filterRepoTable());

      document.querySelectorAll('.table-sort-btn[data-sort-col]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const col = parseInt(btn.getAttribute('data-sort-col'), 10);
          if (!Number.isNaN(col)) sortTable(col);
        });
      });

      const btnCopyJson = document.getElementById('btn-copy-json');
      if (btnCopyJson) btnCopyJson.addEventListener('click', () => copyRawJson());

      // Delegated handlers for dynamically rendered controls (zero inline onclick)
      document.addEventListener('click', (event) => {
        const focusBtn = event.target.closest('[data-focus-node]');
        if (focusBtn) {
          event.stopPropagation();
          const nodeId = focusBtn.getAttribute('data-focus-node');
          if (nodeId !== null) focusNodeOnGraph(nodeId);
          return;
        }

        const matrixBtn = event.target.closest('[data-matrix-src][data-matrix-tgt]');
        if (matrixBtn) {
          const src = matrixBtn.getAttribute('data-matrix-src');
          const tgt = matrixBtn.getAttribute('data-matrix-tgt');
          if (src && tgt) filterMatrixCell(src, tgt);
          return;
        }

        const clusterToggle = event.target.closest('.cluster-card-toggle');
        if (clusterToggle) {
          const card = clusterToggle.closest('.cluster-card');
          if (card) toggleClusterCard(card, clusterToggle);
        }
      });
    }

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
      document.querySelectorAll('.tab-btn[role="tab"]').forEach(b => {
        const isActive = b.getAttribute('data-tab') === tabId;
        b.classList.toggle('active', isActive);
        b.setAttribute('aria-selected', isActive ? 'true' : 'false');
        b.setAttribute('tabindex', isActive ? '0' : '-1');
      });
      document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.id === tabId);
      });

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
      const btn = document.getElementById('btn-toggle-theme');
      if (btn) {
        btn.setAttribute('aria-pressed', next === 'light' ? 'true' : 'false');
        btn.setAttribute('aria-label', next === 'light' ? 'Switch to dark theme' : 'Switch to light theme');
      }
      updateSemanticZoom();
      showToast('Theme switched to ' + next);
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      if (!t) return;
      t.textContent = String(msg);
      t.style.display = 'block';
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => { t.style.display = 'none'; }, 2800);
    }

    function renderMetricSummary() {
      const summary = KB_DATA.graph || {};
      const repos = KB_DATA.repositories || [];
      const clusters = KB_DATA.clusters || [];

      const totalStars = repos.reduce((sum, r) => sum + (Number(r.stars) || 0), 0);

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
            <div class="metric-label">${escapeHtml(it.label)}</div>
            <div class="metric-value">${escapeHtml(it.val)}</div>
            <div class="metric-subtext">${escapeHtml(it.sub)}</div>
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
          opt1.value = String(c.id || '');
          opt1.textContent = String(c.name || c.id || '');
          clusterSelectGraph.appendChild(opt1);
        });
      }

      if (clusterSelectTable) {
        clusterSelectTable.innerHTML = '<option value="all">All Clusters</option>';
        (KB_DATA.clusters || []).forEach(c => {
          const opt2 = document.createElement('option');
          opt2.value = String(c.id || '');
          opt2.textContent = String(c.name || c.id || '');
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
          color: sanitizeColor(meta.color || (nodes.find(n => n.cluster_id === id) || {}).cluster_color, '#3B82F6'),
          count: nodeCountByCluster[id] || 1
        };
      });

      const centers = {};
      const cCount = activeClusters.length;
      if (cCount === 0) return { centers, baseRadius: 320 * spacingMult, orderedClusters: [] };

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
      // Preserve accessible <title> and <desc> inside SVG
      d3.select('#graph-svg').selectAll('g, defs').remove();

      rawNodes = (KB_DATA.graph && KB_DATA.graph.nodes ? KB_DATA.graph.nodes : []).map(d => Object.assign({}, d));
      rawLinks = (KB_DATA.graph && KB_DATA.graph.links ? KB_DATA.graph.links : []).map(d => Object.assign({}, d));
      currentZoomTransform = d3.zoomIdentity;
      hoveredNodeId = null;

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
        { id: 'arrow-highlight', fill: 'var(--focus-ring)' }
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
        .attr('tabindex', '0')
        .attr('role', 'button')
        .attr('aria-label', d => `${d.name || 'Repository'}, cluster ${d.cluster_name || 'General'}, ${d.total_degree || 0} connections`)
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        )
        .on('click', (event, d) => {
          event.stopPropagation();
          selectNode(d.id);
        })
        .on('keydown', (event, d) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            selectNode(d.id);
          }
        })
        .on('mouseover', handleNodeMouseOver)
        .on('mousemove', handleNodeMouseMove)
        .on('mouseout', handleNodeMouseOut);

      nodeElements.append('circle')
        .attr('class', 'node-circle')
        .attr('r', d => getNodeBaseRadius(d))
        .attr('fill', d => sanitizeColor(d.cluster_color, '#3B82F6'))
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
        .text(d => d.name || '');

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

      zoomToFitAll(false);
      refreshGraphHighlights();

      if (!isPhysicsPaused && !prefersReducedMotion()) {
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
      zoomToFitAll(!prefersReducedMotion(), 550);
      if (!isPhysicsPaused && !prefersReducedMotion()) {
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
            color: sanitizeColor(n.cluster_color, '#3B82F6'),
            nodes: []
          };
        }
        byCluster[cid].nodes.push(n);
      });

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
        .text(d => String(d.name || '').toUpperCase());

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

      const zoomBadge = document.getElementById('graph-zoom-level');
      if (zoomBadge) {
        zoomBadge.textContent = Math.round(k * 100) + '%';
      }

      const strokeScale = 1 / Math.pow(k, 0.55);
      nodeElements.select('circle.node-circle')
        .attr('r', d => getNodeWorldRadius(d, k))
        .style('stroke-width', d => {
          const isFocus = String(d.id) === String(selectedNodeId) || String(d.id) === String(hoveredNodeId);
          return ((isFocus ? 3.2 : (d.is_hub ? 2.2 : 1.6)) * strokeScale) + 'px';
        });

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

      const clusterLabelScreenFont = clampVal(9.2 + (k - 0.5) * 1.4, 8.8, 11.2);
      const clusterLabelWorldFont = clusterLabelScreenFont / k;
      const clusterTitleOpacity = k > 2.35 ? 0.25 : 0.86;
      const clusterTitleBoxes = [];

      if (gClusters) {
        gClusters.selectAll('g.cluster-zone').each(function(d) {
          const isDimmed = d3.select(this).classed('dimmed');
          const offsetWorld = 12 / k;
          const estW = String(d.name || '').length * clusterLabelScreenFont * 0.62 + 8;
          const estH = clusterLabelScreenFont + 6;

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

      const screenFont = clampVal(9.5 + (k - 0.5) * 2.4, 9.5, 13.5);
      const haloWorldWidth = 3.6 / k;

      const focusId = hoveredNodeId !== null ? String(hoveredNodeId) : (selectedNodeId !== null ? String(selectedNodeId) : null);
      const focusNeighbors = focusId ? getNeighborIdSet(focusId) : new Set();

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

        const rawName = String(d.name || '');
        const labelFontScreen = isPrimaryFocus ? Math.min(screenFont + 1.2, 14.5) : screenFont;

        const vx = (d.x || 0) - graphMidX;
        const vy = (d.y || 0) - graphMidY;
        let order;
        if (Math.abs(vx) > Math.abs(vy) * 1.15) {
          order = vx >= 0 ? ['right', 'below', 'above', 'left'] : ['left', 'below', 'above', 'right'];
        } else {
          order = vy >= 0 ? ['below', 'right', 'left', 'above'] : ['above', 'right', 'left', 'below'];
        }

        let finalText = rawName;
        let result = findBestCandidate(meta, rawName, labelFontScreen, order);
        const forceFull = isPrimaryFocus || isSearchHit || k >= 0.95;

        if (!result.chosen && !forceFull && rawName.length > 18) {
          const shortName = rawName.slice(0, 17) + '\u2026';
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
        const rawLabel = String(l.label || l.type || '');
        const text = rawLabel.length > 22 ? rawLabel.slice(0, 21) + '\u2026' : rawLabel;
        const wScreen = text.length * edgeFontScreen * 0.56 + 10;
        const hScreen = edgeFontScreen + 6;
        const screenLen = (l._worldLen || 0) * k;

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
              (d.topics || []).some(t => String(t).toLowerCase().includes(activeSearchQuery)) ||
              (d.tech_stack || []).some(t => String(t).toLowerCase().includes(activeSearchQuery));
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
      const shouldAnimate = (options.animate !== undefined ? options.animate : true) && !prefersReducedMotion();
      const duration = shouldAnimate ? (options.duration || 650) : 0;

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

      if (shouldAnimate && duration > 0) {
        svg.transition().duration(duration).call(d3Zoom.transform, transform);
      } else {
        svg.call(d3Zoom.transform, transform);
      }
    }

    function zoomToFitAll(animate = true, duration = 650) {
      frameNodes(rawNodes, { animate, duration, minScale: 0.14, maxScale: 1.05, nodeMargin: 82 });
    }

    function zoomToCluster(clusterId, animate = true, duration = 650) {
      const clusterNodes = (rawNodes || []).filter(d => d.cluster_id === clusterId);
      if (clusterNodes.length === 0) {
        zoomToFitAll(true);
        return;
      }
      frameNodes(clusterNodes, { animate, duration, minScale: 0.45, maxScale: 1.75, nodeMargin: 85 });
    }

    function zoomToNodes(nodesList, animate = true, duration = 650) {
      frameNodes(nodesList, { animate, duration, minScale: 0.25, maxScale: 1.55, nodeMargin: 75 });
    }

    function zoomGraphBy(factor) {
      if (!svg || !d3Zoom) return;
      if (prefersReducedMotion()) {
        svg.call(d3Zoom.scaleBy, factor);
      } else {
        svg.transition().duration(260).call(d3Zoom.scaleBy, factor);
      }
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
        <div style="font-weight: 700; color: var(--tooltip-title); margin-bottom: 2px;">${escapeHtml(d.name)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">${escapeHtml(d.cluster_name || 'General')}</div>
        <div style="font-size: 0.78rem; line-height: 1.35;">${escapeHtml(d.description || 'No description')}</div>
        <div style="margin-top: 6px; font-size: 0.74rem; color: var(--text-dim);">Connections: ${escapeHtml(d.total_degree || 0)} | ${escapeHtml(d.primary_language || 'Other')}</div>
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

      const incoming = (rawLinks || []).filter(l => String(l.target.id !== undefined ? l.target.id : l.target) === String(targetActualId));
      const outgoing = (rawLinks || []).filter(l => String(l.source.id !== undefined ? l.source.id : l.source) === String(targetActualId));

      const outgoingHtml = outgoing.length === 0
        ? '<div style="font-size: 0.78rem; color: var(--text-dim);">No outgoing dependencies</div>'
        : outgoing.map(l => {
            const targetName = (l.target && l.target.name) ? l.target.name : l.target;
            const targetId = (l.target && l.target.id !== undefined) ? l.target.id : l.target;
            return `<button type="button" class="sidebar-link-btn" data-focus-node="${escapeHtml(String(targetId))}">
              <span style="color: var(--primary-text); font-weight: 600;">-> ${escapeHtml(targetName)}</span>
              <span style="color: var(--text-dim); font-size: 0.74rem;">${escapeHtml(l.label || l.type || '')}</span>
            </button>`;
          }).join('');

      const incomingHtml = incoming.length === 0
        ? '<div style="font-size: 0.78rem; color: var(--text-dim);">No incoming consumers</div>'
        : incoming.map(l => {
            const srcName = (l.source && l.source.name) ? l.source.name : l.source;
            const srcId = (l.source && l.source.id !== undefined) ? l.source.id : l.source;
            return `<button type="button" class="sidebar-link-btn" data-focus-node="${escapeHtml(String(srcId))}">
              <span style="color: var(--accent-text); font-weight: 600;"><- ${escapeHtml(srcName)}</span>
              <span style="color: var(--text-dim); font-size: 0.74rem;">${escapeHtml(l.label || l.type || '')}</span>
            </button>`;
          }).join('');

      const safeUrl = sanitizeUrl(node.html_url);
      const repoLinkHtml = safeUrl !== '#'
        ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer" class="ext-link" style="font-size: 0.82rem;">View on GitHub<span class="sr-only"> (opens in new tab)</span></a>`
        : '<span style="font-size: 0.8rem; color: var(--text-dim);">Repository URL unavailable</span>';

      sidebar.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 6px;">
            ${renderClusterBadgeHtml(node.cluster_name, node.cluster_color)}
            ${node.is_hub ? '<span class="badge badge-hub">Architecture Hub</span>' : ''}
          </div>
          <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 4px; overflow-wrap: anywhere;">${escapeHtml(node.name)}</h3>
          ${repoLinkHtml}
        </div>

        <div style="font-size: 0.84rem; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 10px;">
          ${escapeHtml(node.description || 'No description available.')}
        </div>

        <div>
          <div style="font-size: 0.76rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Tech Stack &amp; Topics</div>
          <div>
            ${(node.topics || []).map(t => `<span class="tag">#${escapeHtml(t)}</span>`).join('')}
            ${(node.tech_stack || []).map(t => `<span class="tag tag-tech">${escapeHtml(t)}</span>`).join('')}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.82rem;">
          <div style="background: var(--bg-surface-elevated); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color);">
            <div style="color: var(--text-dim); font-size: 0.74rem;">Language</div>
            <div style="font-weight: 600;">${escapeHtml(node.primary_language || 'Other')}</div>
          </div>
          <div style="background: var(--bg-surface-elevated); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color);">
            <div style="color: var(--text-dim); font-size: 0.74rem;">Stars / Forks</div>
            <div style="font-weight: 600;">${escapeHtml(node.stars || 0)} / ${escapeHtml(node.forks || 0)}</div>
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
          <div style="font-size: 0.82rem; font-weight: 600; margin-bottom: 6px;">Outgoing Dependencies (${outgoing.length})</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${outgoingHtml}
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
          <div style="font-size: 0.82rem; font-weight: 600; margin-bottom: 6px;">Incoming Consumers (${incoming.length})</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${incomingHtml}
          </div>
        </div>
      `;
    }

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
        if (prefersReducedMotion()) {
          svg.call(d3Zoom.transform, transform);
        } else {
          svg.transition().duration(700).call(d3Zoom.transform, transform);
        }
      }
    }

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
      const queryEl = document.getElementById('matcher-query-input');
      const query = (queryEl ? queryEl.value : '').trim();
      const area = document.getElementById('matcher-result-area');
      if (!area) return;

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
        const topics = (repo.topics || []).map(t => String(t).toLowerCase());
        const tech = (repo.tech_stack || []).map(t => String(t).toLowerCase());
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
          <div class="matcher-no-match">
            <div style="font-weight: 700; color: var(--danger-text); margin-bottom: 6px; font-size: 1rem;">No matching repository found</div>
            <div style="font-size: 0.86rem; color: var(--text-main); line-height: 1.45;">
              No repository in this organization can answer your need for <strong>"${escapeHtml(query)}"</strong>.<br/>
              The scanned organization contains repositories across these domains: <em>${escapeHtml(domainNames || 'None')}</em>.
            </div>
          </div>
        `;
        return;
      }

      const best = finalResults[0];
      const isHigh = best.score >= 6.0;
      const confidence = isHigh ? 'High Confidence' : 'Moderate Confidence';
      const badgeClass = isHigh ? 'badge-high' : 'badge-moderate';
      const alternatives = finalResults.slice(1, 4);

      area.innerHTML = `
        <div class="matcher-result-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
            <div>
              <span class="badge ${badgeClass}" style="margin-bottom: 6px;">${escapeHtml(confidence)} (Score: ${escapeHtml(best.score.toFixed(1))})</span>
              <h3 style="font-size: 1.25rem; font-weight: 700;">
                ${renderSafeLinkHtml(best.repo.html_url, (best.repo.name || 'Repository') + ' \u2192')}
              </h3>
            </div>
            <button type="button" class="btn btn-primary btn-sm" data-focus-node="${escapeHtml(String(best.repo.id))}">Locate on Knowledge Graph</button>
          </div>

          <div style="font-size: 0.9rem; color: var(--text-main);">
            ${escapeHtml(best.repo.description || 'No description available.')}
          </div>

          <div style="display: flex; gap: 12px; flex-wrap: wrap; font-size: 0.84rem; color: var(--text-muted); align-items: center;">
            <div><strong>Domain:</strong> ${renderClusterBadgeHtml(best.repo.cluster_name, best.repo.cluster_color)}</div>
            <div><strong>Language:</strong> ${escapeHtml(best.repo.primary_language || 'Other')}</div>
            <div><strong>Stars:</strong> ${escapeHtml(best.repo.stars || 0)}</div>
          </div>

          <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
            <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Why this repository matches your query:</div>
            <ul style="padding-left: 20px; font-size: 0.85rem; color: var(--text-main); line-height: 1.45;">
              ${best.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
          </div>

          ${alternatives.length > 0 ? `
            <div style="border-top: 1px solid var(--border-color); padding-top: 10px;">
              <div style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Alternative Candidates:</div>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                ${alternatives.map(alt => `
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; padding: 6px 10px; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 4px; font-size: 0.82rem;">
                    <div>
                      <button type="button" class="matcher-alt-btn" data-focus-node="${escapeHtml(String(alt.repo.id))}">${escapeHtml(alt.repo.name)}</button>
                      <span style="color: var(--text-muted); font-size: 0.78rem;"> - ${escapeHtml(alt.repo.description || '')}</span>
                    </div>
                    <span class="badge">${escapeHtml(alt.repo.primary_language || 'Other')}</span>
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
        if (btn) {
          btn.textContent = 'Resume Physics';
          btn.setAttribute('aria-pressed', 'true');
        }
      } else {
        if (simulation) simulation.alpha(0.25).restart();
        if (btn) {
          btn.textContent = 'Pause Physics';
          btn.setAttribute('aria-pressed', 'false');
        }
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

      container.innerHTML = clusters.map((c, idx) => {
        const safeColor = sanitizeColor(c.color, '#3B82F6');
        const listId = `cluster-repos-${idx}`;
        return `
        <article class="cluster-card" style="border-left-color: ${safeColor};">
          <button type="button" class="cluster-card-toggle" aria-expanded="false" aria-controls="${listId}">
            <div class="cluster-card-header">
              <div>
                <h3 class="cluster-card-title">${escapeHtml(c.name)}</h3>
                <p class="cluster-card-desc">${escapeHtml(c.description || '')}</p>
              </div>
              ${renderClusterBadgeHtml(`${c.repo_count || 0} repos`, safeColor)}
            </div>

            <div class="cluster-card-stats">
              <div><strong>Stars:</strong> ${escapeHtml(c.total_stars || 0)}</div>
              <div><strong>Languages:</strong> ${escapeHtml((c.top_languages || []).join(', ') || 'N/A')}</div>
            </div>
          </button>

          <div class="cluster-repos-list" id="${listId}">
            <div style="font-size: 0.76rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Repositories (Select to inspect):</div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              ${(c.repositories || []).map(rid => {
                const r = repoMap.get(rid);
                if (!r) return '';
                return `<button type="button" class="cluster-repo-item" data-focus-node="${escapeHtml(String(r.id))}">
                  <span style="font-family: var(--font-mono);">${escapeHtml(r.name)}</span>
                  <span style="color: var(--text-muted); font-size: 0.76rem;">${escapeHtml(r.primary_language || 'Other')}</span>
                </button>`;
              }).join('')}
            </div>
          </div>
        </article>`;
      }).join('');
    }

    function toggleClusterCard(card, toggleBtn) {
      const expanded = card.classList.toggle('expanded');
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      }
    }

    /* Repository Catalog Table */
    let repoSortCol = 0;
    let repoSortAsc = true;

    function renderRepoTable() {
      const repos = KB_DATA.repositories || [];
      const tbody = document.getElementById('repo-table-body');
      if (!tbody) return;

      tbody.innerHTML = repos.map(r => {
        const connections = r.centrality_score ? ((r.in_degree || 0) + (r.out_degree || 0)) : 0;
        const roleHtml = r.is_hub
          ? '<span class="badge badge-hub">Hub</span>'
          : (r.is_bridge ? '<span class="badge badge-bridge">Bridge</span>' : '<span style="color: var(--text-dim);">-</span>');
        return `
        <tr data-name="${escapeHtml((r.name || '').toLowerCase())}" data-cluster="${escapeHtml(String(r.cluster_id || ''))}" data-lang="${escapeHtml((r.primary_language || '').toLowerCase())}">
          <td>
            <strong>${renderSafeLinkHtml(r.html_url, r.name || 'repository')}</strong>
            <div style="font-size: 0.78rem; color: var(--text-muted); max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(r.description || '')}</div>
          </td>
          <td>${renderClusterBadgeHtml(r.cluster_name, r.cluster_color)}</td>
          <td>${escapeHtml(r.primary_language || 'Other')}</td>
          <td>${escapeHtml(r.stars || 0)}</td>
          <td>${escapeHtml(connections)}</td>
          <td>${roleHtml}</td>
          <td><button type="button" class="btn btn-sm" data-focus-node="${escapeHtml(String(r.id))}" aria-label="Inspect ${escapeHtml(r.name || 'repository')} on knowledge graph">Inspect</button></td>
        </tr>`;
      }).join('');
    }

    function filterRepoTable() {
      const query = (document.getElementById('repo-table-search').value || '').toLowerCase();
      const cluster = document.getElementById('table-cluster-filter').value;
      const rows = document.querySelectorAll('#repo-table-body tr');

      rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        const rCluster = row.getAttribute('data-cluster') || '';
        const lang = row.getAttribute('data-lang') || '';

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

      table.querySelectorAll('thead th[aria-sort]').forEach((th, idx) => {
        th.setAttribute('aria-sort', idx === colIndex ? (repoSortAsc ? 'ascending' : 'descending') : 'none');
      });

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
      const matrix = (KB_DATA.graph && KB_DATA.graph.connectivity_matrix) || {};
      const clusters = KB_DATA.clusters || [];

      let htmlOut = '<table class="matrix-table"><caption class="sr-only">Inter-cluster architecture connectivity matrix</caption><thead><tr><th scope="col">Source \\ Target</th>';
      clusters.forEach(c => {
        htmlOut += `<th scope="col" title="${escapeHtml(c.description || '')}">${escapeHtml(c.name)}</th>`;
      });
      htmlOut += '</tr></thead><tbody>';

      clusters.forEach(src => {
        htmlOut += `<tr><th scope="row">${escapeHtml(src.name)}</th>`;
        clusters.forEach(tgt => {
          const count = (matrix[src.id] && matrix[src.id][tgt.id]) || 0;
          if (count > 0) {
            htmlOut += `<td class="matrix-cell-active"><button type="button" class="matrix-cell-btn" data-matrix-src="${escapeHtml(String(src.id))}" data-matrix-tgt="${escapeHtml(String(tgt.id))}" aria-label="Filter ${escapeHtml(count)} connections from ${escapeHtml(src.name)} to ${escapeHtml(tgt.name)}">${escapeHtml(count)}</button></td>`;
          } else {
            htmlOut += '<td><span aria-label="0 connections">-</span></td>';
          }
        });
        htmlOut += '</tr>';
      });

      htmlOut += '</tbody></table>';
      container.innerHTML = htmlOut;
    }

    /* Hardened Client-Side Live Scanning */
    function parseClientGitHubTarget(rawInput) {
      const cleaned = (rawInput || '').trim();
      if (!cleaned || /\s/.test(cleaned) || cleaned.includes('?') || cleaned.includes('#') || cleaned.includes('..')) {
        return null;
      }

      let pathPart = '';
      if (cleaned.includes('://')) {
        let parsed;
        try {
          parsed = new URL(cleaned);
        } catch (e) {
          return null;
        }
        if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return null;
        const host = parsed.hostname.toLowerCase();
        if (host !== 'github.com' && host !== 'www.github.com') return null;
        if (parsed.search || parsed.hash) return null;
        pathPart = parsed.pathname.replace(/^\/+|\/+$/g, '');
      } else {
        let stripped = cleaned.replace(/^www\./i, '');
        if (/^github\.com\//i.test(stripped)) {
          stripped = stripped.slice('github.com/'.length);
        } else if (stripped.includes(':') || stripped.includes('.')) {
          return null;
        }
        pathPart = stripped.replace(/^\/+|\/+$/g, '');
      }

      const parts = pathPart.split('/').filter(Boolean);
      if (parts.length === 0) return null;
      let owner = parts[0];
      let repoName = null;

      if (owner === 'orgs' || owner === 'users') {
        if (parts.length < 2) return null;
        owner = parts[1];
        repoName = parts.length >= 3 ? parts[2] : null;
      } else if (parts.length >= 2) {
        repoName = parts[1];
      }

      if (!OWNER_RE.test(owner)) return null;
      if (repoName !== null) {
        if (repoName.endsWith('.git')) repoName = repoName.slice(0, -4);
        if (repoName === '.' || repoName === '..' || !REPO_RE.test(repoName)) return null;
      }

      return { owner, repoName };
    }

    async function fetchWithTimeout(url, timeoutMs = 15000) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        return await fetch(url, {
          signal: controller.signal,
          credentials: 'omit',
          referrerPolicy: 'no-referrer',
          headers: { 'Accept': 'application/vnd.github.v3+json' }
        });
      } finally {
        clearTimeout(timer);
      }
    }

    async function scanAddressInput() {
      if (isScanning) {
        showToast('A GitHub scan is already in progress.');
        return;
      }
      const inputEl = document.getElementById('scan-target-input');
      const btnScan = document.getElementById('btn-scan-address');
      const input = (inputEl ? inputEl.value : '').trim();
      if (!input) {
        showToast('Please enter a public GitHub URL or handle.');
        return;
      }

      const parsed = parseClientGitHubTarget(input);
      if (!parsed) {
        showToast('Invalid GitHub target. Enter a valid github.com owner or owner/repo.');
        return;
      }

      const { owner, repoName } = parsed;
      const encOwner = encodeURIComponent(owner);
      const encRepo = repoName ? encodeURIComponent(repoName) : null;

      isScanning = true;
      if (btnScan) btnScan.disabled = true;
      showToast('Scanning ' + owner + (repoName ? '/' + repoName : '') + ' via api.github.com...');

      try {
        if (encRepo) {
          const res = await fetchWithTimeout(`https://api.github.com/repos/${encOwner}/${encRepo}`);
          if (res.status === 200) {
            const rawRepo = await res.json();
            if (rawRepo && typeof rawRepo === 'object' && !Array.isArray(rawRepo)) {
              processClientRepos(owner, input, [rawRepo]);
              showToast(`Successfully loaded repository ${owner}/${repoName}!`);
              return;
            }
          }
        }

        const res = await fetchWithTimeout(`https://api.github.com/orgs/${encOwner}/repos?per_page=100&sort=updated`);
        if (res.status === 200) {
          const rawRepos = await res.json();
          if (!Array.isArray(rawRepos)) throw new Error('Unexpected API payload');
          processClientRepos(owner, input, rawRepos.slice(0, 100));
          showToast(`Successfully loaded ${Math.min(rawRepos.length, 100)} repos from ${owner}!`);
        } else if (res.status === 404) {
          const userRes = await fetchWithTimeout(`https://api.github.com/users/${encOwner}/repos?per_page=100&sort=updated`);
          if (userRes.status === 200) {
            const rawRepos = await userRes.json();
            if (!Array.isArray(rawRepos)) throw new Error('Unexpected API payload');
            processClientRepos(owner, input, rawRepos.slice(0, 100));
            showToast(`Loaded ${Math.min(rawRepos.length, 100)} repos from user ${owner}!`);
          } else {
            showToast('GitHub account not found. Loading synthetic preview.');
            onPresetChange('synthetic');
          }
        } else {
          showToast(`GitHub API rate limit or error (HTTP ${res.status}).`);
        }
      } catch (err) {
        showToast('Network, timeout, or CORS limitation. Use Python CLI or local preset.');
      } finally {
        isScanning = false;
        if (btnScan) btnScan.disabled = false;
      }
    }

    function processClientRepos(owner, inputUrl, rawRepos) {
      const taxonomy = [
        { id: "medical-healthcare", name: "Medical & Healthcare", description: "Clinical systems, electronic health records (EHR/EMR), patient care, FHIR, and telehealth.", color: "#0EA5E9", keywords: ["medical", "healthcare", "clinical", "patient", "health", "ehr", "emr", "fhir", "hl7", "dicom", "hospital", "telehealth", "hipaa", "diagnosis"] },
        { id: "life-sciences-bio", name: "Life Sciences & Bioinformatics", description: "Genomics sequencing pipelines, DNA/RNA molecular biology, and clinical trials research.", color: "#14B8A6", keywords: ["genomics", "bioinformatics", "biology", "dna", "rna", "sequencing", "protein", "crispr", "pharma", "biotech", "molecular", "clinical-trials", "laboratory"] },
        { id: "finance-billing", name: "Finance, Billing & Commerce", description: "Payment processing, subscription billing, invoices, accounting, and e-commerce checkout.", color: "#10B981", keywords: ["billing", "payment", "invoice", "subscription", "checkout", "finance", "banking", "accounting", "ecommerce", "ledger"] },
        { id: "security-identity", name: "Security, Identity & Access", description: "Authentication, OAuth2/OIDC identity providers, token issuance, RBAC, and encryption.", color: "#EC4899", keywords: ["auth", "authentication", "oauth", "oauth2", "oidc", "identity", "security", "rbac", "jwt", "token", "encryption", "sso", "login"] },
        { id: "data-ai-analytics", name: "Data Intelligence & AI/ML", description: "Machine learning models, inference engines, vector search, streaming pipelines, and analytics.", color: "#8B5CF6", keywords: ["ai", "ml", "analytics", "pipeline", "etl", "kafka", "flink", "warehouse", "embeddings", "rag", "llm", "model", "inference"] },
        { id: "developer-tooling", name: "Developer Tooling & SDKs", description: "Client SDKs, CLI tools, API bindings, linters, code generators, and testing harnesses.", color: "#F59E0B", keywords: ["sdk", "cli", "client-library", "tooling", "generator", "plugin", "agent", "linter", "wrapper", "bindings"] },
        { id: "infrastructure-devops", name: "Infrastructure & Cloud Operations", description: "Cloud infrastructure as code, Terraform, Kubernetes, Helm, Docker, and CI/CD.", color: "#EF4444", keywords: ["infra", "infrastructure", "terraform", "k8s", "kubernetes", "docker", "helm", "ci-cd", "cloud", "deploy"] },
        { id: "core-platform", name: "Core Platform & Business Services", description: "Routing gateways, user profiles, tenancy, notification dispatchers, and domain services.", color: "#3B82F6", keywords: ["gateway", "proxy", "user-service", "tenancy", "notification", "dispatch", "engine", "router", "service"] },
        { id: "frontend-applications", name: "User Applications & Web Portals", description: "Web portals, dashboards, customer interfaces, mobile apps, and interactive web apps.", color: "#06B6D4", keywords: ["portal", "app", "ui", "dashboard", "web", "frontend", "mobile", "console", "react", "vue"] },
        { id: "utilities-libraries", name: "Utilities & Shared Libraries", description: "Shared common utilities, protocol buffer contracts, data schemas, and helper libraries.", color: "#64748B", keywords: ["utils", "utilities", "common", "shared", "core-lib", "proto", "contracts", "schemas", "helpers", "types"] },
        { id: "documentation-specs", name: "Documentation & Specifications", description: "Architectural blueprints, technical guides, OpenAPI specs, and RFC standards.", color: "#475569", keywords: ["docs", "documentation", "spec", "specification", "rfc", "guide", "architecture", "standard", "wiki"] }
      ];

      const repos = rawRepos.map((r, i) => {
        const topics = Array.isArray(r.topics) ? r.topics.map(t => String(t)) : [];
        const name = String(r.name || '');
        const desc = String(r.description || '').toLowerCase();

        let assignedCluster = taxonomy[taxonomy.length - 2];
        for (const tax of taxonomy) {
          if (tax.keywords.some(k => name.toLowerCase().includes(k) || topics.includes(k) || desc.includes(k))) {
            assignedCluster = tax;
            break;
          }
        }

        return {
          id: r.id || (i + 1),
          name: name,
          full_name: String(r.full_name || `${owner}/${name}`),
          html_url: sanitizeUrl(r.html_url),
          description: String(r.description || "No description provided."),
          primary_language: String(r.language || "Other"),
          topics: topics,
          tech_stack: [r.language].filter(Boolean).map(String),
          stars: Number(r.stargazers_count) || 0,
          forks: Number(r.forks_count) || 0,
          open_issues: Number(r.open_issues_count) || 0,
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

      const targetDisplay = document.getElementById('active-target-display');
      if (targetDisplay) targetDisplay.textContent = 'Target: ' + inputUrl;
      refreshAllViews();
    }

    function onPresetChange(val) {
      if (val === 'current') {
        KB_DATA = JSON.parse(JSON.stringify(INITIAL_KB_DATA));
      } else if (val === 'synthetic') {
        KB_DATA = JSON.parse(JSON.stringify(INITIAL_KB_DATA));
      } else if (val === 'pallets') {
        const input = document.getElementById('scan-target-input');
        if (input) input.value = 'https://github.com/pallets';
        scanAddressInput();
        return;
      } else if (val === 'fastapi') {
        const input = document.getElementById('scan-target-input');
        if (input) input.value = 'https://github.com/fastapi';
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
          try { document.execCommand('copy'); } catch (_) {}
          showToast('JSON copied to clipboard!');
        }
      }
    }

    function exportDataJson() {
      const blob = new Blob([JSON.stringify(KB_DATA, null, 2)], { type: 'application/json;charset=utf-8' });
      const blobUrl = URL.createObjectURL(blob);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', blobUrl);
      downloadAnchor.setAttribute('download', 'knowledge_base_export.json');
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      showToast('Exporting JSON file...');
    }
"""
