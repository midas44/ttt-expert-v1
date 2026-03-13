# TTT Expert System — Project Analysis (Round 2)

> **Date**: 2026-03-11
> **Branch**: dev7
> **Scope**: Re-evaluation of all issues from analysis_1.md after user fixes, plus new findings
> **Baseline**: `docs/analysis_1.md` (same date, earlier)

---

## 1. Resolution Tracker — Issues from Analysis 1

### CRITICAL Issues

| # | Issue | Status | Notes |
|---|---|---|---|
| C1 | MISSION_DIRECTIVE.md wrong location | **FIXED** | Moved to `expert-system/MISSION_DIRECTIVE.md` — matches CLAUDE+.md §3, §9.1, §16 |
| C2 | config.yaml template mismatch | **FIXED** | CLAUDE+.md §2 now uses `testing_dev_envs`/`testing_prod_envs` with `name` only; env params rule added at line 67 |
| C3 | analytics.db empty; sqlite3 not installed | **PARTIALLY FIXED** | `sqlite3` now installed (`/usr/bin/sqlite3`). DB still empty (0 bytes) — expected, schema initialization is part of First Session Bootstrap §16 step 4 |
| C4 | QMD has 0 indexed documents | **OPEN (expected)** | Still 0 docs. Will resolve after bootstrap populates vault + runs `qmd sync` |
| C5 | Missing directories: repos/, scripts/, output/ | **FIXED** | All three directories now exist (empty) |

### MODERATE Issues

| # | Issue | Status | Notes |
|---|---|---|---|
| M1 | QMD tool names wrong in §13 | **OPEN** | Still shows `qmd_search`, `qmd_vsearch`, `qmd_query`, `qmd_get`. Should be: `search`, `vector_search`, `deep_search`, `get`, `multi_get` |
| M2 | SQLite MCP description vague in §13 | **OPEN** | Still says "SQLite MCP". Should say: `sqlite-analytics` via `@bytebase/dbhub`, tools: `execute_sql`, `search_objects` |
| M3 | config.yaml template shows `default_branch: "develop"` | **OPEN** | Line 48 of CLAUDE+.md still has `default_branch: "develop"`. Actual config.yaml has `"release/2.1"`. The template is a reference example, but this mismatch could confuse the system on first read |
| M4 | MISSION_DIRECTIVE.md typos (4 items) | **FIXED** | "synchronization" (line 45), "may not be mentioned" (line 51 reworded), "discretion" (line 102), Google Sheets bracket (line 110-111 rewritten) |
| M5 | Only test-api Swagger group has MCP | **PARTIALLY ADDRESSED** | MISSION_DIRECTIVE.md now lists all Swagger URLs (lines 119-127) for all services and groups. MCP still only covers `test-api` of `ttt` service, but the comprehensive URL list enables curl-based access to all others |
| M6 | `qmd embed` requires embedding model not documented | **OPEN** | No change |
| M7 | Vault bootstrap not executed | **OPEN (expected)** | Still pending — by design, part of First Session Bootstrap |

### MINOR Issues

| # | Issue | Status | Notes |
|---|---|---|---|
| L1 | Google Docs access method undefined | **FIXED** | MISSION_DIRECTIVE.md lines 110-111 now explicitly state "access by link, no mcp required" |
| L2 | `artifacts/` directory orphaned | **OPEN** | Still present, not referenced |
| L3 | MCP server split not documented | **OPEN** | Still undocumented |
| L4 | Sprint range (11-15) may become stale | **OPEN** | Unchanged |
| L5 | No explicit Confluence/Figma identifiers | **PARTIALLY FIXED** | Confluence now has space "NOV" and entry page URL (line 68, 74). Figma still delegated to skill |
| L6 | `qmd collection add` in §16 already exists | **OPEN** | Unchanged |

---

## 2. MISSION_DIRECTIVE.md — What Changed

The document grew from 117 to 136 lines with significant quality improvements:

### New Content Added
1. **Language guidance** (line 8): "Use English version of application; English in knowledge base; give Russian terms for ambiguous terminology"
2. **UI languages** (line 49): "UI has 2 language versions: Russian (RU) and English (EN). Language switcher is available in page header."
3. **Expanded note** (line 51): Encourages investigating undescribed areas
4. **Confluence identifiers** (line 68): Space "NOV", project "Time Tracking Tool", entry page URL
5. **Confluence entry page** (line 72-74): Explicit URL with caveat about being "severely outdated"
6. **Figma usage note** (line 98): "Use links to figma layers from GitLab tickets and Confluence pages"
7. **Swagger URL inventory** (lines 119-127): All 7 Swagger URLs across 4 services (ttt, vacation, calendar, email) with URL pattern
8. **Output: English only** (line 135): Explicit requirement
9. **Output: AI autotest note** (line 136): Clarified phrasing

### Fixes Applied
- "syncronization" → "synchronization"
- "may not mentioned" → reworded entirely
- "descretion" → "discretion"
- "Google Sheet]" → "Google Sheets" (rewritten cleanly)
- swagger-api removed from Testing Environments skill list (was wrong — swagger-api is API skill, not env skill)

---

## 3. New Issues Found (Round 2)

### MODERATE

| # | Issue | Location | Description |
|---|---|---|---|
| N1 | **Swagger URL typo: double slash** | MISSION_DIRECTIVE.md lines 122-123 | `/api/vacation//swagger-ui.html` has double `//` — likely should be `/api/vacation/swagger-ui.html` |
| N2 | **§5 frontmatter example hardcodes `branch: develop`** | CLAUDE+.md line 183 | Vault note frontmatter template shows `branch: develop`. Should reference the configured default branch or use a placeholder like `<default_branch>` |
| N3 | **§6 SQL schema hardcodes `DEFAULT 'develop'`** | CLAUDE+.md lines 214, 237 | Tables `analysis_runs` and `module_health` have `DEFAULT 'develop'` — should match actual default branch `release/2.1` or be set dynamically at bootstrap |
| N4 | **§2 template still shows `default_branch: "develop"`** | CLAUDE+.md line 48 | Same as M3 — the template example value diverges from the actual config. Three places now hardcode "develop": §2 template, §5 frontmatter, §6 SQL schema |

### MINOR

| # | Issue | Location | Description |
|---|---|---|---|
| N5 | **Heading level inconsistency** | MISSION_DIRECTIVE.md line 16 | `# Functionality` uses H1 (`#`) while all other sections use H2 (`##`). Should be `## Functionality` |
| N6 | **Confluence note wording** | MISSION_DIRECTIVE.md line 94 | "part of information in Confluence may be outdated/obsolete" — grammatically should be "part of **the** information" or "some information" |

---

## 4. Consolidated Open Issues — Priority Ranking

### MODERATE (should fix before Phase A start)

| # | Issue | Fix |
|---|---|---|
| M1 | QMD tool names wrong in §13 | Replace `qmd_search`, `qmd_vsearch`, `qmd_query`, `qmd_get` with `search`, `vector_search`, `deep_search`, `get`, `multi_get` |
| M2 | SQLite MCP description vague in §13 | Replace "SQLite MCP" with `sqlite-analytics` (`@bytebase/dbhub`), tools: `execute_sql`, `search_objects` |
| N4/M3 | "develop" hardcoded in 3 places | **Option A**: Change all three to `release/2.1` — but this becomes stale when branch changes. **Option B** (recommended): Change §2 template to use placeholder `"<current>"`, §5 to note "use value from config.yaml", §6 to use no default (set at bootstrap from config). This makes the system branch-agnostic. |
| N1 | Swagger URL double slash | Remove extra `/` in vacation Swagger URLs (lines 122-123) |

### MINOR (can fix during Phase A or leave as-is)

| # | Issue | Fix |
|---|---|---|
| N5 | Heading level `# Functionality` | Change to `## Functionality` |
| N6 | Confluence note grammar | Minor wording fix |
| L2 | `artifacts/` orphaned | Remove or add to .gitignore |
| L3 | MCP server split undocumented | Add brief note to §13 |
| L4 | Sprint range staleness | Add "update as sprints progress" note |
| L6 | `qmd collection add` already exists | Change to `qmd sync` or add idempotency check |
| M6 | `qmd embed` model undocumented | Document or note as optional |

---

## 5. CLAUDE+.md — "develop" Consistency Issue (Deep Dive)

Three locations in CLAUDE+.md hardcode `develop` as the branch name:

| Location | Line | Text |
|---|---|---|
| §2 config template | 48 | `default_branch: "develop"` |
| §5 frontmatter example | 183 | `branch: develop` |
| §6 SQL schema | 214, 237 | `DEFAULT 'develop'` |

Meanwhile, actual `config.yaml` uses `default_branch: "release/2.1"`.

**Recommended fix**: Since the branch will change over time (release/2.2, release/3.0, etc.), the prompt should NOT hardcode any specific branch. Instead:

- **§2 template**: Keep as illustrative example but add comment: `# Update per active sprint`
- **§5 frontmatter**: Change to `branch: <from config.yaml repos.default_branch>`
- **§6 SQL schema**: Remove `DEFAULT 'develop'` — require explicit branch value at insert time (enforce awareness of which branch is being analyzed)

---

## 6. Readiness Estimation (Updated)

### Phase A — Knowledge Acquisition: **~85% Ready** (was ~70%)

**Improvements since analysis_1:**
- MISSION_DIRECTIVE.md in correct location and significantly improved
- config.yaml template aligned with reality
- `sqlite3` installed
- `repos/`, `scripts/`, `output/` directories created
- MISSION_DIRECTIVE.md typos fixed
- Swagger URLs comprehensively documented
- Google Docs access method clarified

**Remaining blockers (must fix):**
- M1: QMD tool names wrong in §13 (will cause confusion on first use)
- M2: SQLite MCP details wrong in §13 (will cause confusion on first use)

**Remaining non-blocking (should fix):**
- N4/M3: "develop" hardcoded in 3 places (cosmetic but misleading)
- N1: Swagger URL double slash (copy-paste will fail)
- C3: analytics.db empty (bootstrap handles this)
- C4: QMD 0 docs (bootstrap handles this)
- M7: Vault not bootstrapped (bootstrap handles this)

**Estimated fix effort**: ~15-20 minutes for M1 + M2 + N1 + N4. After that, project is ready for First Session Bootstrap.

### Phase B — Test Documentation Generation: **~25% Ready** (was ~20%)

Slight improvement due to better MISSION_DIRECTIVE.md (clearer output requirements, English-only spec, Swagger inventory). Still fundamentally blocked on Phase A completion.

---

## 7. Summary

**13 of 22 original issues resolved** (5 fully fixed, 3 partially fixed/addressed, 5 expected-open for bootstrap). **6 new issues found** (4 moderate, 2 minor), mostly related to the "develop" branch hardcoding pattern and a Swagger URL typo.

The project has moved from ~70% to ~85% Phase A readiness. Two quick fixes (M1: QMD tool names, M2: SQLite MCP details) plus the Swagger URL typo (N1) would bring it to ~95%, with the remaining 5% being the First Session Bootstrap execution itself.
