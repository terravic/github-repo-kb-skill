> **DRAFT — REQUIRES LEGAL REVIEW**
> Replace bracketed placeholders (`[LEGAL ENTITY NAME]`, `[JURISDICTION]`, `[PRIMARY HOSTING REGION]`, `[BACKUP STORAGE REGION]`, `[LLM API REGION]`, `[CONTACT EMAIL]`, `[EFFECTIVE DATE]`, `[RETENTION PERIOD]`) and review with your Data Protection Officer / legal counsel before operationalizing.

# Record of Processing Activities (ROPA) & AI/Data Governance

**Effective Date:** `[EFFECTIVE DATE]`
**Controller / Operator:** `[LEGAL ENTITY NAME]`
**Jurisdiction:** `[JURISDICTION]`
**DPO / Governance Contact:** `[CONTACT EMAIL]`

---

## 1. Record of Processing Activities (GDPR Article 30)

| Field | Value |
|---|---|
| **Processing Activity Name** | GitHub Repository Metadata Analysis & Knowledge Base Generation (`github-repo-kb-skill`) |
| **Purpose of Processing** | Inventorying software repositories, thematic domain classification, architectural dependency mapping, and capability search |
| **Categories of Data Subjects** | Public/private GitHub individual account owners (only when scanning a personal GitHub user account rather than an organization) and users initiating live API requests |
| **Categories of Personal Data** | GitHub username/handle (`owner`, `full_name`), public repository URL (`html_url`), repository timestamps (`created_at`, `updated_at`), and client IP address transmitted to `api.github.com` during explicit live scans (*Breyer*, C-582/14). No emails, phone numbers, physical addresses, commit author emails, or special-category data are ingested. |
| **Special Categories (GDPR Art. 9) / PHI (HIPAA)** | **None / Prohibited.** Do not feed PHI or clinical patient data into this tool. |
| **Jurisdictional Hosting & Backups** | Compute & primary storage: `[PRIMARY HOSTING REGION]`; Backup storage: `[BACKUP STORAGE REGION]` (must match primary residency); Agent LLM API endpoint (if used): `[LLM API REGION, e.g., EEA-pinned endpoint]`. |
| **Recipients / External Endpoints** | `https://api.github.com` (GitHub, Inc., United States) — **only** during explicit live scans (`--url` or user-triggered **Scan Address**). Zero external hosts on offline runs or dashboard load. |
| **International Data Transfers** | EEA/UK/Swiss live-scan requests to `api.github.com` rely on EU-U.S. Data Privacy Framework certification and/or executed Standard Contractual Clauses (SCCs) under operator's GitHub Data Protection Agreement (requires legal counsel verification). |
| **Retention & Erasure Workflow** | `[RETENTION PERIOD, e.g., 90 days or deleted upon project completion]` for `output/` artifacts; verified hard-erasure (`--erase-user` / `deleteUserData`) and JSON/CSV portability (`--export-user`) fulfilled within **30 calendar days** (GDPR Art. 12(3), 17, 20). `GITHUB_TOKEN` held in volatile memory only. |
| **Technical & Organizational Measures (TOMs)** | TLS >= 1.2 + certificate validation, SSRF/IP allowlisting, strict CSP (`sha256` script hashes), XSS/URL/Markdown sanitization, `O_NOFOLLOW` path/symlink confinement, strict config schema validation, secret log redaction, vendored SHA-256 verified D3.js, WCAG 2.2 AA accessibility. |

---

## 2. AI Governance & Transparency (EU AI Act Art. 50 / NIST AI RMF Posture)
- **Skill Classification**: Low-risk developer productivity and architectural documentation tool. Core clustering (`scripts/clusterer.py`), graph centrality (`scripts/graph_builder.py`), and search scoring (`scripts/query_engine.py`) are deterministic rule/keyword algorithms.
- **Agent Harness Disclosure**: When invoked through an LLM agent harness (`SKILL.md`), the host agent should inform end users that conversational summaries are AI-assisted and link directly to the underlying source repositories on GitHub for verification.
- **Prompt Injection Defense**: Generated `KNOWLEDGE_BASE.md` includes an explicit Data Provenance Notice instructing agents and reviewers to treat external GitHub metadata strictly as passive untrusted data, never as executable instructions.

---

## 3. Sub-Processor & External Service Register

| Service | Host | Primary Region | Purpose | Trigger Condition | Credentials Sent |
|---|---|---|---|---|---|
| GitHub REST API (GitHub, Inc.) | `https://api.github.com` | United States | Fetch repository metadata | Explicit CLI `--url` or Dashboard **Scan Address** / live preset | Optional `GITHUB_TOKEN` (CLI only; browser scan is unauthenticated `credentials: omit`) |

*(No other external services, CDNs, font hosts, payment gateways, or telemetry endpoints are bundled.)*
