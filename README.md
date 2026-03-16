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
- Master system prompt (`CLAUDE+.md`, ~630 lines) defining identity, protocols, and quality standards
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

Generated test documentation (test plans and test cases as XLSX workbooks) serves as structured input for an existing AI-driven test automation framework that generates executable autotests from these artifacts. The XLSX format is also compatible with Google Sheets import, enabling export to collaborative environments for review, manual editing, or integration with other systems.

### Output directory structure

```
output/
├── vacation/vacation.xlsx           # 201 cases, 18 tabs
├── statistics/statistics.xlsx       # 156 cases, 12 tabs
├── sick-leave/sick-leave.xlsx       # 132 cases, 10 tabs
├── planner/planner.xlsx             # 130 cases, 15 tabs
├── day-off/day-off.xlsx             # 120 cases, 10 tabs
├── reports/reports.xlsx             # 110 cases, 11 tabs
├── admin/admin.xlsx                 # 108 cases, 12 tabs
├── security/security.xlsx           # 108 cases, 12 tabs
├── accounting/accounting.xlsx       # 104 cases, 10 tabs
└── cross-service/cross-service.xlsx #  64 cases, 10 tabs
```

### Workbook tab structure

Each XLSX workbook is a self-contained document with these tab types:

| Tab | Purpose |
|-----|---------|
| **Plan Overview** | Scope, objectives, approach, environment requirements. Contains hyperlinks to all TS-* tabs. |
| **Feature Matrix** | Features × test types grid with case counts. Each feature hyperlinks to its TS-* tab. |
| **Risk Assessment** | Feature, risk description, likelihood, impact, severity, mitigation/test focus. |
| **TS-\*** | Test suite tabs — one per logical group (e.g., TS-Vac-Create, TS-SL-Lifecycle). Each tab has a back-link to Plan Overview. |
| **Test Data** | SQL queries and data generation notes for test execution. |

### Test case columns (all TS-* tabs)

| Column | Description |
|--------|-------------|
| Test ID | Unique identifier (e.g., TC-VAC-001) |
| Title | What is being tested |
| Preconditions | Required state before test execution |
| Steps | Numbered execution steps |
| Expected Result | What should happen |
| Priority | P1 (critical) through P4 (low) |
| Type | Functional, Negative, Boundary, Security, API, etc. |
| Requirement Ref | Link to requirement, Confluence page, or GitLab ticket |
| Module/Component | Backend service, frontend module, or API endpoint |
| Notes | Test data hints, known bugs, edge case context |

### Test suites by area

**Vacation** (201 cases): Create, Update, StatusFlow, Approval, DayCalc, Payment, Permissions, APIErrors, Supplement, Maternity, CSSettings, CalendarMigr, AVMultiYear, PastDateVal

**Statistics** (156 cases): GeneralUI, EmpReports, API, NormCalc, Access, DataCache, Export, EffBounds, CacheArch

**Sick Leave** (132 cases): Lifecycle, DualStatus, Accounting, Permissions, Validation, APIErrors

**Planner** (130 cases): Search, CRUD, Generate, Ordering, CloseTag, Locks, History, WebSocket, Bugs, UI, ClosedFilter

**Day-Off** (120 cases): CRUD, Approval, Calendar, OptApprover, Permissions, Validation

**Reports** (110 cases): CRUD, Periods, Locks, Statistics, Permissions, APIErrors, Confirmation

**Admin** (108 cases): Projects, Employees, Calendars, Settings, Trackers, APIErrors, PMTool-Edge, PMTool-S15

**Security** (108 cases): JWTAuth, APIToken, RoleAccess, EndpointPerm, SoDuties, InfoLeak, ObjPerm, InputVal

**Accounting** (104 cases): Periods, Payment, DayCorrection, Views, SickLeave, APIErrors

**Cross-Service** (64 cases): Office, RabbitMQ, CSSync, WebSocket, Banner, BuildInfo

### Google Sheets import

Each workbook is designed for single-file import: File > Import > Upload > select the `.xlsx` file. All tabs, formatting, and hyperlinks are preserved. The Plan Overview tab serves as the navigation hub — click any feature to jump to its test suite.

## Operating Modes

The expert system is designed to operate in four modes, selectable via `config.yaml` and session context:

1. **Data Acquisition** (implemented, completed). Autonomous multi-session investigation from scratch. The agent systematically builds a knowledge base by exploring the codebase (static analysis of local clone), live testing environments (Playwright UI, Swagger API, PostgreSQL), and external documentation (Confluence, Figma, GitLab, Qase). Sessions are orchestrated by `run-sessions.sh` with configurable delays and limits. Completed across two runs: initial run (47 sessions, breadth-first) followed by a deep re-investigation run (51 sessions with relaxed note size limits and code snippet inclusion) that enriched the knowledge base from ~150K to ~222K tokens before auto-transitioning to Phase B.

2. **Data Update** (planned). Triggered after application changes (new sprints, releases, hotfixes). The agent compares branches (e.g. `release/2.1` vs `stage`), identifies changed areas via GitLab diffs and tickets, and selectively updates affected vault notes, SQLite records, and coverage metrics. Avoids full re-investigation by scoping updates to deltas — changed endpoints, modified business logic, new UI flows, altered database schema. Marks stale notes for review and re-runs targeted exploratory testing on affected areas.

3. **Documentation Generation** (implemented, completed). Activated after Phase A reached coverage target with sufficient depth. Produces per-functional-area unified XLSX workbooks (test plan + test suites in one file with cross-linked tabs) using Python openpyxl. Each area goes through: focused deep investigation → knowledge sufficiency check → Qase deduplication check → XLSX generation → tracking in SQLite. Output directory: `output/<area>/`. Generator scripts in `expert-system/generators/<area>/`. Designed for single-file import into Google Sheets with multi-tab navigation. Completed: 1,233 test cases across 81 suites in 10 workbooks.

4. **Interactive** (implicit, always available). A human launches Claude Code in the project directory and gives specific tasks in a conversational session. The agent leverages the full knowledge base (vault, SQLite, QMD search) and all MCP integrations to accomplish narrow tasks: answer questions about the application, investigate specific bugs, trace a particular business workflow, generate test cases for a single feature, update documentation after a known change, or run targeted exploratory tests. The governing documents (`CLAUDE+.md`, Mission Directive) and accumulated knowledge provide context; the human provides direction.

## Current State

Both phases complete. The system ran 80 sessions over 4 days (March 12-16, 2026):

**Run statistics:**
- **80 sessions** total (51 Phase A + 29 Phase B), 22.1 hours of compute, zero failures
- **4.5M output tokens**, 689M cache read tokens across 4,170 tool turns
- Models used: Claude Opus 4.6 (primary), Claude Haiku 4.5 (subagent tasks), Claude Sonnet 4.6 (occasional)

**Knowledge base:** 191 notes, ~222K tokens
- Exploration findings (48 notes), external references (37), module deep-dives (35), bug investigations (28), architecture (12), cross-cutting analysis (17), patterns (6)
- Average note: ~1,163 tokens with code snippets, validation rules, and concrete testable details

**Test documentation output:** 1,233 test cases across 81 suites in 10 unified XLSX workbooks

| Area | Suites | Cases |
|------|--------|-------|
| Vacation | 14 | 201 |
| Statistics | 9 | 156 |
| Sick Leave | 6 | 132 |
| Planner | 11 | 130 |
| Day-Off | 6 | 120 |
| Reports | 7 | 110 |
| Admin | 8 | 108 |
| Security | 8 | 108 |
| Accounting | 6 | 104 |
| Cross-Service | 6 | 64 |

Each workbook contains: Plan Overview, Feature Matrix, Risk Assessment, and TS-* test suite tabs with cross-navigation hyperlinks. Ready for Google Sheets import.

## Repository Structure

**Remote:** `https://github.com/midas44/ttt-expert-v1.git` (branch: `main`; public, requires foreign VPN to access from RF)

**What is in the repo:**

```
CLAUDE+.md                              # Master system prompt (~630 lines)
start.sh                               # Start runner in tmux session
stop.sh                                # Graceful stop (sets autonomy.stop: true)
dashboard.sh                           # Open HTML dashboard in Chromium
expert-system/
  config.yaml                           # Runtime configuration
  MISSION_DIRECTIVE.md                  # Project goals and source inventory
  analytics.db                          # SQLite analytics database
  vault/                                # Obsidian knowledge base (191 notes, ~222K tokens)
  repos/project/                        # Local clone of TTT codebase (empty on clone — populated at runtime)
  scripts/
    run-sessions.sh                     # Autonomous session orchestrator
    coverage-report.sh                  # Phase A coverage metrics tool
    proxy-watchdog.sh                   # Cron watchdog — restarts VPN proxy if down
    generate-dashboard.py               # HTML dashboard generator (runs after each session)
  artefacts/                            # Screenshots, PDFs, downloads (gitignored)
  generators/                           # Python scripts that produce XLSX workbooks
output/                                 # Generated XLSX workbooks (10 areas, 1233 cases) — root level
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
| `expert-system/repos/` | Cloned TTT codebase (~772MB) | Populated at runtime, too large for remote |
| `__pycache__/` | Python bytecode cache | Build artifact |
| `.claude/context/secrets/` | Secret files for skills and integrations | Sensitive credentials |
| `.claude/context/gitlab-credentials.md` | GitLab PAT and connection details | Sensitive credentials |
| `.playwright-mcp/` | Auto-generated Playwright MCP screenshots and logs | Transient browser automation artifacts |
| `expert-system/artefacts/` | Screenshots, PDFs, downloaded attachments, exported data | Binary artifacts, not part of knowledge base |

Note: `output/` (generated XLSX files, root level) is not gitignored — Phase B output is tracked in the repo.

## Host Environment

- **OS:** Ubuntu Server LTS (XFCE desktop with access via XRDP)
- **Runtime:** Claude Code CLI with Claude Opus model (works via adguardvpn-cli in SOCKS proxy mode and Throne proxy manager)
- **Network:** Corporate VPN (Noveo OpenVPN) required for all TTT environments; MCP servers configured with proxy bypass for VPN hostnames
- **Prerequisites:** Node.js (MCP servers), Python 3 + openpyxl (XLSX generation), QMD daemon (semantic search), Obsidian vault configuration, PostgreSQL client libraries

- **Hardware:** i5-12600K CPU, 32Gb RAM, Nvidia GPU (GTX 1070) with CUDA drivers to facilitate QMD processing, 1Tb SSD