# TTT Expert System — Interactive Mode

This project contains an expert knowledge base for the TTT (Time Tracking Tool) application. Use it to answer questions, investigate issues, and generate test documentation.

## Knowledge Base

- **Obsidian vault** (`expert-system/vault/`, 191 notes, ~222K tokens) — search via `mcp__qmd-search__` tools or read directly via `mcp__obsidian__` tools
- **SQLite analytics** (`expert-system/analytics.db`) — query via `mcp__sqlite-analytics__execute_sql`
- **Generated test docs** (`output/` — 10 XLSX workbooks, 1,233 test cases)

## Available MCPs

| MCP | Use for |
|-----|---------|
| **qmd-search** | Semantic/keyword search over vault notes — start here for any question |
| **obsidian** | Read, write, search vault notes directly |
| **sqlite-analytics** | Query module_health, exploration_findings, design_issues, test_case_tracking |
| **playwright-vpn** | UI testing on TTT environments (use this, not the built-in plugin) |
| **swagger-\*** | REST API calls to qa-1, timemachine, stage environments |
| **postgres-\*** | Database queries on qa-1, timemachine, stage (read-only) |
| **confluence** | TTT documentation wiki |
| **figma** | Design mockups |
| **qase** | Existing test suites (project: TIMEREPORT) |
| **gitlab** | Use curl + PAT (MCP server non-functional on this CE instance) |

## How to answer questions

1. Search the vault first (`mcp__qmd-search__search` or `mcp__qmd-search__vector_search`)
2. Read relevant notes (`mcp__obsidian__read_note`)
3. If vault lacks detail, investigate live: code (`expert-system/repos/project/`), API, DB, or UI
4. Reference vault note names when citing findings

## Key references

- `CLAUDE+.md` — full autonomous system prompt (for reference, not loaded in interactive mode)
- `expert-system/config.yaml` — environment configuration
- `expert-system/MISSION_DIRECTIVE.md` — priority areas and information sources
- `expert-system/vault/_KNOWLEDGE_COVERAGE.md` — what's been investigated
- `expert-system/vault/_INDEX.md` — vault note index
