---
type: external
tags:
  - google-docs
  - specifications
  - external-sources
  - inventory
created: '2026-03-13'
updated: '2026-03-14'
status: active
related:
  - '[[architecture/roles-permissions]]'
  - '[[modules/email-service]]'
  - '[[external/existing-tests/confluence-automation-plans]]'
---

# Google Docs/Sheets Inventory

Complete catalog of external documents referenced from Confluence entry page (18940713).

## Google Drive Folder
- **Master folder**: drive.google.com/drive/folders/0Bx0bD6P61smedlllM1lFMlFVTnc

## Specifications — Fetched (8 documents)

| # | Document | Type | Vault Note | Key Content |
|---|----------|------|------------|-------------|
| 1 | Statistics spec | Sheet | (in google-docs-inventory) | Role-based access matrix, 4 view types, 5 roles |
| 2 | Email notifications | Sheet | (in google-docs-inventory) | All notification types: budget, reporting, vacation, sick leave, day-off |
| 3 | Error handling agreement | Doc | [[patterns/error-handling-agreement]] | 4 error categories, localized errorCode, field validation display |
| 4 | Roles & permissions | Sheet | (updated [[architecture/roles-permissions]]) | 14 roles, scope-based restrictions, action permissions |
| 5 | Vacations spec | Doc | [[external/requirements/REQ-vacations-google-spec]] | Complete spec v1.0: 2 counters, 14 events, accrual formula, all workflows |
| 6 | Tracker integration | Doc | [[external/requirements/REQ-tracker-integration]] | 5 trackers, two-stage search, zero-trust scripting |
| 7 | Timesheet rendering | Sheet | [[external/requirements/REQ-timesheet-rendering]] | Color-coding priorities, sorting logic, permission buttons |
| 8 | Dismissal process | Doc | [[external/requirements/REQ-dismissal-process]] | 8-step cross-system workflow (TTT+CS+STT) |

## Specifications — Not Yet Fetched

| Document | Type | Access | Notes |
|----------|------|--------|-------|
| Planner spec | Doc | **401** | Not publicly shared |
| Functional spec (outdated) | Doc | Available | General overview, not maintained — low priority |
| Old vacation spec | Doc | Available | Predecessor to current — superseded by fetched spec |
| Task rename spec | Doc | Available | Single feature — low priority |
| Vacation digest notifications | Doc | Available | Specific notification feature — low priority |
| Technical notes | Doc | Available | Developer notes — low priority |

## Testing Documents — Fetched (3 of 6)

| # | Document | Type | Vault Note | Key Content |
|---|----------|------|------------|-------------|
| 1 | Test plan | Doc | [[EXT-test-plan]] | pytest+requests stack, 11 test sections, role parametrization, swagger-coverage, manual testing in Qase |
| 2 | Vacation testing notes | Doc | [[EXT-vacation-testing-notes]] | 14 critical regression cases (1-8 auto, 9-14 manual), cross-system CS workflows, test users |
| 3 | Knowledge transfer (nshevtsova) | Doc | [[EXT-knowledge-transfer]] | Automation gaps (admin/accounting/planner not started), technical quirks, role parametrization issues |

## Testing Documents — Inaccessible (3 of 6)

| Document | Type | URL | Access Issue |
|----------|------|-----|-------------|
| Auto tests follow-up | Sheet | docs.google.com/spreadsheets/d/1s8IqbZnlW1y28DatpjPLkcbogdEpb8j96h8NxoCcmiU | Dynamic rendering — WebFetch gets JS shell only |
| Testers meetings MoM | Doc | docs.google.com/document/d/1WpkoqBZpKJ4vSdg0HMWPOKwbEJUNDKs8SmrYKIy_U20 | **401** — not publicly shared |
| Test Automation plan (old) | Doc | docs.google.com/document/d/1P-rq3d7dIMC6BY5Tc9tsXJUBUKBNrtmWTRIQyzlnjb4 | Dynamic rendering — WebFetch gets JS shell only |

**Note**: These 3 documents are from 2021 (end of API test team's work). The most important testing context has already been captured through the 3 fetched docs. The Confluence automation pages ([[confluence-automation-plans]]) provide substantial additional context about both test frameworks.

## Confluence Automation Test Pages (Session 16)

Two rich Confluence pages discovered and synthesized:
- **Automation test plan (API)** (page 110298204): Python/pytest stack, CI config, test structure, links to all Google Docs
- **Automation test plan (Front-end, grey-box)** (page 75923811): Java/JUnit5/Selenide stack, architecture, milestones, methodology

See: [[external/existing-tests/confluence-automation-plans]]

## Related
- [[architecture/roles-permissions]]
- [[modules/email-service]]
- [[modules/statistics-service-implementation]]
- [[architecture/security-patterns]]
- [[external/requirements/confluence-overview]]
- [[patterns/error-handling-agreement]]
- [[external/existing-tests/confluence-automation-plans]]
