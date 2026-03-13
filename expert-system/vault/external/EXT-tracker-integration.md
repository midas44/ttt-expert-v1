---
type: external
tags:
  - trackers
  - integration
  - jira
  - gitlab
  - redmine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[ttt-service]]'
---
# Tracker Integration

**Source**: Confluence 110298524

## Supported Trackers
- **JIRA Cloud** — full (import + export hours)
- **JIRA Server** (#3161) — corporate jira.noveogroup.com
- **GitLab Server** — import only (time via /spend comments); no cloud support
- **Redmine** (#2522) — corporate redmine.noveogroup.com
- **Presales** (#1964-19) — presales-preprod.noveogroup.com; no hour import/export
- **ClickUp** (#3148) — limited, no test access from Russia, sole user abandoning
- **Asana** (#2462) — NOT supported (listed but not implemented)

## Integration Pattern
8 tracker-client implementations in TTT service. Setup: tracker account → API token → TTT project link (Admin > Projects) → user connection (Settings) → employee assignment (Planner).

## 9 Integration Test Cases
Add linked tasks, rename sync, delete error handling, invalid connection errors, export hours (JIRA/ClickUp), import hours, batch operations (Project/Personal Planner).

## Related
- [[ttt-service]]
- [[system-overview]]
