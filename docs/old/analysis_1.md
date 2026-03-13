# TTT Expert System — Project Analysis

> **Date**: 2026-03-11
> **Branch**: dev7
> **Scope**: Project structure, governing documents (CLAUDE+.md, MISSION_DIRECTIVE.md), infrastructure readiness
> **Note**: CLAUDE+.md will be renamed to CLAUDE.md before Phase A start

---

## 1. Project Structure Overview

```
/home/v/Dev/ttt-expert-v1/
├── CLAUDE+.md                    (517 lines) — Master expert system prompt
├── MISSION_DIRECTIVE.md          (117 lines) — Goals, sources, project context
├── .gitignore
│
├── .claude/
│   ├── .mcp.json                 — 5 MCP servers (gitlab, confluence, swagger, postgres, figma)
│   ├── settings.local.json       — Local settings
│   ├── context/                  — Credentials (gitignored)
│   ├── mcp-tools/                — Swagger MCP wrapper + cache
│   └── skills/                   — 10 skills (fully documented)
│
├── expert-system/
│   ├── config.yaml               — Session/phase configuration
│   ├── analytics.db              — SQLite DB (EMPTY — not initialized)
│   └── vault/                    — Obsidian vault (MINIMAL — only skeleton)
│       ├── test-note.md
│       ├── exploration/          (empty)
│       └── external/             (empty)
│
├── config/ttt/                   — TTT environment configs
│   ├── ttt.yml                   — App-wide settings
│   └── envs/                     — Per-environment: qa-1, timemachine, stage
│
├── docs/                         — Documentation (3 existing files)
└── artifacts/                    — Empty, not referenced anywhere
```

### Structure vs CLAUDE+.md Expectations

| Expected (CLAUDE+.md §3)  | Actual | Status |
|---|---|---|
| `expert-system/MISSION_DIRECTIVE.md` | Root: `MISSION_DIRECTIVE.md` | **WRONG LOCATION** |
| `expert-system/repos/` | Does not exist | **MISSING** |
| `expert-system/scripts/` | Does not exist | **MISSING** |
| `expert-system/output/` | Does not exist | **MISSING** |
| `vault/_SESSION_BRIEFING.md` | Does not exist | Missing (bootstrap) |
| `vault/_INVESTIGATION_AGENDA.md` | Does not exist | Missing (bootstrap) |
| `vault/_INDEX.md` | Does not exist | Missing (bootstrap) |
| `vault/_KNOWLEDGE_COVERAGE.md` | Does not exist | Missing (bootstrap) |
| `vault/architecture/` | Does not exist | Missing (bootstrap) |
| `vault/modules/` | Does not exist | Missing (bootstrap) |
| `vault/patterns/` | Does not exist | Missing (bootstrap) |
| `vault/debt/` | Does not exist | Missing (bootstrap) |
| `vault/decisions/` | Does not exist | Missing (bootstrap) |
| `vault/external/requirements/` | Does not exist | Missing (bootstrap) |
| `vault/external/designs/` | Does not exist | Missing (bootstrap) |
| `vault/external/tickets/` | Does not exist | Missing (bootstrap) |
| `vault/external/existing-tests/` | Does not exist | Missing (bootstrap) |
| `vault/exploration/ui-flows/` | Does not exist | Missing (bootstrap) |
| `vault/exploration/api-findings/` | Does not exist | Missing (bootstrap) |
| `vault/exploration/data-findings/` | Does not exist | Missing (bootstrap) |
| `vault/investigations/` | Does not exist | Missing (bootstrap) |
| `vault/analysis/` | Does not exist | Missing (bootstrap) |
| `vault/branches/` | Does not exist | Missing (bootstrap) |

**Verdict**: Vault and supporting directories are almost entirely uninitialized. This is expected — CLAUDE+.md §16 defines a "First Session Bootstrap" that creates these. The bootstrap has not been executed yet.

---

## 2. CLAUDE+.md Analysis

### 2.1 Internal Consistency Issues

| Issue | Section | Description | Severity |
|---|---|---|---|
| **Mission Directive path** | §7, §9.1, §16 | References `expert-system/MISSION_DIRECTIVE.md` but file is at project root | **CRITICAL** |
| **config.yaml template mismatch** | §2 | Template shows `testing_envs.primary.url/api_base/db_host` — actual config uses `testing_dev_envs.primary.name` and `testing_prod_envs.primary.name` | **CRITICAL** |
| **config.yaml template default_branch** | §2 | Template shows `default_branch: "develop"` — actual is `"release/2.1"`. Misleading template. | **MODERATE** |
| **QMD tool names wrong** | §13 | Lists `qmd_search`, `qmd_vsearch`, `qmd_query`, `qmd_get` — actual tools: `search`, `vector_search`, `deep_search`, `get`, `multi_get` | **MODERATE** |
| **SQLite MCP reference vague** | §13 | Says "SQLite MCP" — actual server: `sqlite-analytics` via `@bytebase/dbhub`, tools: `execute_sql`, `search_objects` | **MODERATE** |
| **Google Docs access undefined** | §4, §12 | Architecture diagram shows Google Docs as source; §12 says "no MCP needed" but no access method defined | **MINOR** |

### 2.2 Missing or Incorrect References

| Reference | Issue |
|---|---|
| `qmd embed` (§9.3, §16) | Command exists but `qmd embed` requires an embedding model — configuration not documented |
| `qmd collection add` (§16) | Collection `expert-vault` already exists in QMD — step should be idempotent |
| `qmd context add` (§16) | Context already configured in QMD |
| `sqlite3` usage implied (§6) | `sqlite3` CLI is NOT installed on this machine |

### 2.3 MCP Server Coverage

CLAUDE+.md §13 references these MCP servers:

| MCP in doc | Configured? | Where? |
|---|---|---|
| mcp-obsidian | Yes | `~/.claude.json` (project scope) |
| QMD | Yes | `~/.claude.json` (project scope) |
| SQLite MCP | Yes | `~/.claude.json` as `sqlite-analytics` |
| Playwright | Yes | Plugin (`playwright@claude-plugins-official`) |
| Swagger/API | Yes | `.mcp.json` as `ttt-swagger-test` |
| PostgreSQL | Yes | `.mcp.json` as `postgres` |
| GitLab | Yes | `.mcp.json` as `gitlab` |
| Confluence | Yes | `.mcp.json` as `confluence` |
| Figma | Yes | `.mcp.json` as `figma` |
| Qase | Yes | `~/.claude.json` (project scope) |

**All 10 referenced MCP servers are configured.** However, the doc doesn't mention that servers are split between `.mcp.json` (5) and `~/.claude.json` (5). This split works but could cause confusion.

### 2.4 Swagger API Coverage Gap

Only `test-api` group is configured as MCP server. MISSION_DIRECTIVE.md and MEMORY.md reference two Swagger groups (`test-api` and `api`). The `api` group is not available via MCP — would need a second server or curl.

---

## 3. MISSION_DIRECTIVE.md Analysis

### 3.1 Typos and Grammar

| Line | Text | Fix |
|---|---|---|
| 44 | "syncronization" | "synchronization" |
| 47 | "may not mentioned" | "may not be mentioned" |
| 93 | "descretion" | "discretion" |
| 102 | `**Google Sheet]**:` | `**Google Sheets**:` (stray bracket) |

### 3.2 Completeness Assessment

| Area | Status | Notes |
|---|---|---|
| Global goal | Complete | Clear two-phase objective |
| Project context | Good | Covers all major areas |
| Functionality list | Good | Comprehensive but notes "some features may not be mentioned" |
| Priority areas | Complete | 4 areas prioritized |
| Codebase sources | Complete | GitLab repo, branches identified |
| Documentation | Good | Confluence pages with examples |
| Designs | Adequate | References figma-access skill |
| Test management | Adequate | References qase-access skill with quality caveat |
| Tickets | Good | Sprint labels defined (11-15) |
| Additional docs | Adequate | Google Docs/Sheets by links |
| Testing environments | Complete | 3 envs with roles defined |
| Output requirements | Good | Clear XLSX format, Google Sheets compatibility, autotest input noted |

### 3.3 Missing Information

- **No URLs for testing environments**: Env configs only have DB credentials and API tokens. Full URLs must be derived from `ttt.yml` pattern `https://ttt-***.noveogroup.com`
- **No Confluence space key explicitly stated**: Delegated to skill — acceptable but fragile
- **No Figma file key explicitly stated**: Delegated to skill — acceptable
- **No explicit list of all Confluence requirement pages**: Only examples given with "All pages in Requirements/*"
- **Sprint range may need updating**: "X>=11 and X<=15" — if sprints advance, this becomes stale

---

## 4. config.yaml Analysis

### Actual vs CLAUDE+.md Template

```yaml
# ACTUAL config.yaml structure:
testing_dev_envs:
  primary:
    name: "timemachine"
  secondary:
    name: "qa-1"
testing_prod_envs:
  primary:
    name: "stage"

# CLAUDE+.md §2 template structure:
testing_envs:
  primary:
    url: ""
    api_base: ""
    db_host: ""
  secondary:
    url: ""
    api_base: ""
    db_host: ""
```

**Issues**:
1. Different key names (`testing_dev_envs`/`testing_prod_envs` vs `testing_envs`)
2. Different value structure (`name` only vs `url`/`api_base`/`db_host`)
3. Actual config splits dev/prod into separate keys — template doesn't
4. Actual config relies on separate env YAML files for connection details — template embeds them

**Recommendation**: Either update config.yaml to match the template or update the CLAUDE+.md template to match reality. The actual structure is cleaner (name + separate env files) but the template is more self-contained.

---

## 5. Infrastructure Readiness

### 5.1 MCP Servers

| Server | Status | Notes |
|---|---|---|
| gitlab | Available | Registered, PAT configured |
| confluence | Available | Registered, PAT configured |
| ttt-swagger-test | Available | Custom wrapper with caching |
| postgres | Available | Connection string configured |
| figma | Available | HTTP MCP endpoint |
| obsidian | Available | Points to vault directory |
| qmd-search | Available | 0 documents indexed |
| sqlite-analytics | Available | Points to empty DB |
| qase | Available | Read-only token |
| playwright | Available | Plugin enabled |

**All 10 MCP servers registered and available.**

### 5.2 QMD Search

- Collection `expert-vault` exists
- Context configured: "Expert system knowledge base"
- **0 documents indexed** — needs `qmd sync` after vault has content
- Vector embeddings: 0 — `qmd embed` not yet run
- Keyword search (`search`) will work once synced
- Vector search requires embedding model configuration (not documented)

### 5.3 SQLite Analytics DB

- File exists at `expert-system/analytics.db` but is **EMPTY** (0 bytes)
- `sqlite3` CLI **NOT INSTALLED** — cannot initialize via bash
- `sqlite-analytics` MCP (dbhub) can execute SQL — can be used to initialize schema
- Schema defined in CLAUDE+.md §6 (6 tables) — ready to apply

### 5.4 Vault (Obsidian)

- Base directory exists
- `.obsidian/` config present (basic Obsidian setup)
- Only `test-note.md`, `exploration/`, `external/` exist
- 20+ required directories/files missing (see §1 table)
- mcp-obsidian can create directories and files — bootstrap via MCP

### 5.5 Tools

| Tool | Available | Notes |
|---|---|---|
| `qmd` | Yes | `/usr/local/bin/qmd` |
| `sqlite3` | **NO** | Not installed — use MCP or install |
| Python `openpyxl` | Yes | Required for XLSX generation (Phase B) |
| `npx` | Yes | For frontend analysis tools |
| `git` | Yes | For repo cloning and history |
| `python3` | Yes | For scripts |
| `curl` | Yes | Swagger API fallback |

---

## 6. All Identified Issues — Priority Ranking

### CRITICAL (must fix before Phase A start)

| # | Issue | Fix |
|---|---|---|
| C1 | MISSION_DIRECTIVE.md is at project root but CLAUDE+.md references `expert-system/MISSION_DIRECTIVE.md` | Move file or update all references in CLAUDE+.md |
| C2 | config.yaml schema doesn't match CLAUDE+.md §2 template | Align one to the other |
| C3 | analytics.db is empty; `sqlite3` not installed | Install `sqlite3` OR initialize via sqlite-analytics MCP |
| C4 | QMD has 0 indexed documents | Will resolve naturally after bootstrap (vault population + `qmd sync`) |
| C5 | Missing directories: `repos/`, `scripts/`, `output/` | Create during bootstrap |

### MODERATE (should fix before Phase A start or during Session 1)

| # | Issue | Fix |
|---|---|---|
| M1 | QMD tool names in CLAUDE+.md §13 are wrong | Update to: `search`, `vector_search`, `deep_search`, `get`, `multi_get` |
| M2 | SQLite MCP description in §13 is vague | Update with actual server name and tool names |
| M3 | config.yaml template shows `default_branch: "develop"` | Update template to show actual or use placeholder |
| M4 | MISSION_DIRECTIVE.md has 4 typos | Fix typos |
| M5 | Only `test-api` Swagger group has MCP server | Consider adding `api` group as second MCP server |
| M6 | `qmd embed` requires embedding model not documented | Document model configuration or note limitation |
| M7 | Vault bootstrap not executed (20+ missing dirs/files) | Part of First Session Bootstrap (§16) |

### MINOR (can fix during Phase A)

| # | Issue | Fix |
|---|---|---|
| L1 | Google Docs access method undefined | Document direct URL access or screenshot workflow |
| L2 | `artifacts/` directory orphaned | Remove or document purpose |
| L3 | MCP server split (.mcp.json vs ~/.claude.json) not documented | Add note to CLAUDE+.md or consolidate |
| L4 | Sprint range (11-15) may become stale | Add note about updating |
| L5 | No explicit Confluence/Figma identifiers in MISSION_DIRECTIVE.md | Acceptable — delegated to skills |
| L6 | `qmd collection add` in §16 — collection already exists | Make step idempotent (use `qmd sync`) |

---

## 7. Readiness Estimation

### Phase A — Knowledge Acquisition: **~70% Ready**

**What's ready:**
- All 10 MCP servers configured and available
- Obsidian vault directory exists with MCP access
- QMD search engine installed and collection registered
- 10 skills fully documented and functional
- config.yaml present with correct phase settings
- Env configs available for all 3 environments
- Git repo functional, branches available
- `qmd`, `python3`, `npx`, `git`, `curl` all installed

**What's NOT ready (blocks first session):**
- MISSION_DIRECTIVE.md in wrong location (or CLAUDE+.md references wrong)
- config.yaml schema mismatches with CLAUDE+.md
- analytics.db empty + sqlite3 not installed
- Vault structure not bootstrapped (20+ missing dirs/files)
- `repos/`, `scripts/`, `output/` directories don't exist
- QMD tool names in CLAUDE+.md are wrong
- No repo clone yet

**Estimated fix effort**: 1-2 hours to resolve all critical and moderate issues. Most can be fixed during the First Session Bootstrap procedure (CLAUDE+.md §16) with minor doc corrections beforehand.

### Phase B — Test Documentation Generation: **~20% Ready**

**What's ready:**
- Python `openpyxl` installed (XLSX generation)
- XLSX format and workflow defined in CLAUDE+.md §11
- Output requirements clear in MISSION_DIRECTIVE.md
- test_case_tracking table schema defined
- Qase MCP available for checking existing tests

**What's NOT ready:**
- Phase A not started (knowledge base empty)
- config.yaml has `generation_allowed: false`
- `output/` directory doesn't exist
- No knowledge base content to generate from
- No vault notes, no SQLite analytics data
- No codebase clone analyzed

**Phase B cannot begin** until Phase A reaches sufficient coverage (~80% per config threshold). Estimated: 25+ sessions of Phase A work.

---

## 8. Recommended Pre-Launch Fixes

Before renaming CLAUDE+.md → CLAUDE.md and starting Phase A:

1. **Decide MISSION_DIRECTIVE.md location**: Move to `expert-system/` or update CLAUDE+.md references
2. **Align config.yaml with CLAUDE+.md template** (or vice versa)
3. **Fix CLAUDE+.md §13**: Correct QMD tool names, SQLite MCP details
4. **Fix MISSION_DIRECTIVE.md typos** (4 items)
5. **Install sqlite3**: `sudo apt install sqlite3`
6. **Create missing directories**: `repos/`, `scripts/`, `output/`
7. **Optionally**: Add second Swagger MCP for `api` group

Items 1-4 are document fixes. Items 5-7 are infra setup. All are straightforward.
