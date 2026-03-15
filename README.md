# AI-Driven Expert System for TTT Legacy Application Investigation and Test Documentation Generation

## Purpose

An autonomous expert system built on top of Claude Code (Opus) that systematically investigates the TTT (Time Tracking Tool) — a complex corporate web application for time reporting and absence management — and produces comprehensive test documentation (plans and cases) as XLSX artifacts. The system addresses the problem of insufficient test coverage and undocumented business logic in a large legacy codebase.

## Architecture

The system operates as a prompt-engineered autonomous agent with a two-phase workflow:

- **Phase A — Knowledge Acquisition.** The agent conducts multi-session investigation of the target application: static analysis of the codebase (Java/Spring Boot backend, React/Redux frontend), exploratory testing of live environments via browser automation and REST API calls, database inspection, and ingestion of external documentation (Confluence, Figma, GitLab, Qase). Findings are persisted into an Obsidian vault (Markdown notes with YAML frontmatter and wikilink cross-references) and a SQLite analytics database. Phase A targets 80% knowledge coverage before transitioning.

- **Phase B — Test Documentation Generation.** Using the accumulated knowledge base, the agent generates per-module XLSX files containing structured test plans and test cases, traceable to requirements and non-duplicative of existing Qase entries.

Sessions are orchestrated by a shell-based runner that enforces inter-session delays, manages vault git history, and limits consecutive runs. Each session follows a protocol: read briefing → select investigation targets → execute investigation cycles → persist findings → update coverage metrics → write next-session briefing.

## Technology Stack

**Agent infrastructure:**
- Claude Code CLI with Claude Opus model, full autonomy mode
- Master system prompt (`CLAUDE+.md`, ~620 lines) defining identity, protocols, and quality standards
- YAML-based runtime configuration (phase, timing, autonomy parameters)
- Bash session runner with preflight checks and failure tracking

**Knowledge storage:**
- Obsidian vault with typed notes (architecture, module, analysis, exploration, external) and semantic search via QMD
- SQLite database (6 tables: analysis runs, module health, design issues, external refs, exploration findings, test case tracking)

**Integration layer — MCP servers:**

| MCP Server | Package / Method | Purpose |
|---|---|---|
| **mcp-obsidian** | `@mauricio.wolff/mcp-obsidian` | Vault CRUD, search, frontmatter and tag management |
| **qmd-search** | `qmd mcp` | Semantic and keyword search over the vault |
| **sqlite-analytics** | `@bytebase/dbhub` | Structured data queries against the analytics database |
| **playwright-vpn** | `@playwright/mcp` (standalone, proxy bypass) | Browser automation for VPN-only TTT environments |
| **Swagger/API** | 21 instances: 3 envs × 7 service/group combinations | REST API exploration and exploratory testing |
| **PostgreSQL** | `crystaldba/postgres-mcp` — 3 instances (qa-1, timemachine, stage) | Database inspection (read-only) |
| **Confluence** | `@anthropic/confluence-mcp` | Requirements and wiki documentation |
| **Figma** | `@anthropic/figma-mcp` | Design specifications and mockups |
| **Qase** | `@anthropic/qase-mcp` | Existing test suites and test cases |
| **GitLab** | curl + PAT (MCP server connected but non-functional on self-hosted CE) | Issues, MRs, pipelines, code via REST API |

**Reusable skills (10):** Encapsulated domain-specific interaction patterns for GitLab, Confluence, Figma, Qase, Swagger API, PostgreSQL, Playwright, and infrastructure management (MCP setup, package install, skill creator).

## Target Application (TTT)

A microservices-based corporate system for time tracking and absence management:
- 4 backend services (Java 17, Spring Boot): TTT core, Vacation, Calendar, Email — 366 REST endpoints total
- React 18 / TypeScript / Redux frontend with 12 modules
- PostgreSQL database: 86 tables across 4 schemas
- 20+ salary offices across 7 countries, 11 global user roles
- Business-critical domains: vacation workflows (multi-approver, dual calculation modes), sick leaves, days-off, time reporting with approval chains, accounting period management
- 3 testing environments (timemachine, qa-1, stage) with full API and database access

## XLSX Output and Downstream Usage

Generated test documentation (test plans and test cases as XLSX workbooks) serves as structured input for an existing AI-driven test automation framework that generates executable autotests from these artifacts. The XLSX format is also compatible with Google Sheets import, enabling export to collaborative environments for review, manual editing, or integration with other systems. Each test case includes: ID, title, preconditions, steps, expected results, priority, type, requirement reference, and notes on test data generation (database mining with criteria, random generation, static values, etc.) — providing sufficient detail for both human execution and automated code generation.

## Operating Modes

The expert system is designed to operate in four modes, selectable via `config.yaml` and session context:

1. **Data Acquisition** (implemented, completed). Autonomous multi-session investigation from scratch. The agent systematically builds a knowledge base by exploring the codebase (static analysis of local clone), live testing environments (Playwright UI, Swagger API, PostgreSQL), and external documentation (Confluence, Figma, GitLab, Qase). Sessions are orchestrated by `run-sessions.sh` with configurable delays and limits. Completed in 47 sessions with 100% knowledge coverage.

2. **Data Update** (planned). Triggered after application changes (new sprints, releases, hotfixes). The agent compares branches (e.g. `release/2.1` vs `stage`), identifies changed areas via GitLab diffs and tickets, and selectively updates affected vault notes, SQLite records, and coverage metrics. Avoids full re-investigation by scoping updates to deltas — changed endpoints, modified business logic, new UI flows, altered database schema. Marks stale notes for review and re-runs targeted exploratory testing on affected areas.

3. **Documentation Generation** (implemented, current mode). Activated after Phase A reached 100% coverage. Produces per-functional-area unified XLSX workbooks (test plan + test suites in one file with cross-linked tabs) using Python openpyxl. Each area goes through: focused deep investigation → knowledge sufficiency check → Qase deduplication check → XLSX generation → tracking in SQLite. Output directory: `expert-system/output/<area>/`. Designed for single-file import into Google Sheets with multi-tab navigation.

4. **Interactive** (implicit, always available). A human launches Claude Code in the project directory and gives specific tasks in a conversational session. The agent leverages the full knowledge base (vault, SQLite, QMD search) and all MCP integrations to accomplish narrow tasks: answer questions about the application, investigate specific bugs, trace a particular business workflow, generate test cases for a single feature, update documentation after a known change, or run targeted exploratory tests. The governing documents (`CLAUDE+.md`, Mission Directive) and accumulated knowledge provide context; the human provides direction.

## Current State

Phase A restarted for deeper knowledge acquisition:
- **48 sessions** completed in previous run (47 Phase A + 1 Phase B)
- **163 knowledge base notes** covering architecture, all modules, database schema (86 tables), roles/permissions, business logic, UI flows, API surface (233 endpoints), exploration findings, external documentation (Confluence, Figma, GitLab, Qase, Google Docs)
- **12 bugs discovered** during exploratory testing, documented in vault
- Phase A is being re-run with relaxed note size limits (no word cap, code snippets allowed) to build deeper, more detailed knowledge before generating test documentation. Previous run reached 100% coverage but with overly compressed notes that lacked concrete testable details.
- Auto-transition to Phase B enabled — system will automatically switch to test documentation generation when coverage target is met with sufficient depth

## Repository Structure

**Remote:** `https://github.com/midas44/ttt-expert-v1.git` (branch: `main`; public, requires foreign VPN to access from RF)

**What is in the repo:**

```
CLAUDE+.md                              # Master system prompt (~620 lines)
start.sh                               # Start runner in tmux session
stop.sh                                # Graceful stop (sets autonomy.stop: true)
dashboard.sh                           # Open HTML dashboard in Chromium
expert-system/
  config.yaml                           # Runtime configuration
  MISSION_DIRECTIVE.md                  # Project goals and source inventory
  analytics.db                          # SQLite analytics database
  vault/                                # Obsidian knowledge base (163 notes)
  repos/project/                        # Local clone of TTT codebase (empty on clone — populated at runtime)
  scripts/
    run-sessions.sh                     # Autonomous session orchestrator
    coverage-report.sh                  # Phase A coverage metrics tool
    proxy-watchdog.sh                   # Cron watchdog — restarts VPN proxy if down
    generate-dashboard.py               # HTML dashboard generator (runs after each session)
  output/                               # Generated XLSX test documentation (subdirs per area)
config/ttt/
  ttt.yml                              # App URL/name configuration template
  envs/timemachine.yml                 # Timemachine environment credentials
  envs/stage.yml                       # Stage environment credentials
docs/                                   # Setup guides (human-guide, autonomy-guide), troubleshooting
.claude/
  settings.local.json                   # MCP server enablement
  scripts/sync-postgres-mcp.js          # Dynamic PostgreSQL MCP config generator
  skills/                               # 10 reusable skills (GitLab, Confluence, Figma, etc.)
  mcp-tools/                            # MCP server dependencies and cached Swagger specs
```

**What is excluded via `.gitignore` (present only on the working machine):**

| Path | Contents | Reason |
|---|---|---|
| `.mcp.json` | MCP server configuration with connection URIs, API tokens, PATs | Contains secrets (tokens, credentials) |
| `CLAUDE.md` | Symlink to `CLAUDE+.md`, auto-created by `run-sessions.sh` | Runtime artifact |
| `expert-system/logs/` | Session runner output, state files, runner log | Transient session artifacts |
| `expert-system/vault/.git` | Inner git repo for vault history, managed by `run-sessions.sh` | Auto-managed, per-session commits |
| `.claude/context/secrets/` | Secret files for skills and integrations | Sensitive credentials |
| `.claude/context/gitlab-credentials.md` | GitLab PAT and connection details | Sensitive credentials |
| `config/ttt/envs/qa-1.yml` | QA-1 environment credentials (DB host, port, password, API token) | Sensitive credentials |
| `.playwright-mcp/` | Auto-generated Playwright MCP screenshots and logs | Transient browser automation artifacts |
| `expert-system/artefacts/` | UI screenshots from Playwright exploration sessions | Binary artifacts, not part of knowledge base |

Note: `expert-system/output/` (generated XLSX files) is not gitignored — Phase B output is tracked in the repo.

## Host Environment

- **OS:** Ubuntu Server LTS (XFCE desktop with access via XRDP)
- **Runtime:** Claude Code CLI with Claude Opus model (works via adguardvpn-cli in SOCKS proxy mode and Throne proxy manager)
- **Network:** Corporate VPN (Noveo OpenVPN) required for all TTT environments; MCP servers configured with proxy bypass for VPN hostnames
- **Prerequisites:** Node.js (MCP servers), Python 3 + openpyxl (XLSX generation), QMD daemon (semantic search), Obsidian vault configuration, PostgreSQL client libraries

- **Hardware:** i5-12600K CPU, 32Gb RAM, Nvidia GPU (GTX 1070) with CUDA drivers to facilitate QMD processing, 1Tb SSD