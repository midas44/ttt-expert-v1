---
type: external
tags:
  - tickets
  - sprint-14
  - sprint-15
  - gitlab
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-vacations-master]]'
  - '[[REQ-advance-vacation]]'
  - '[[REQ-statistics]]'
  - '[[vacation-service-implementation]]'
---
# Sprint 14-15 GitLab Tickets Overview

Sprint 14: 42 tickets (all closed). Sprint 15: 59 tickets (55 open). Hotfix Sprint 14: 6 (all closed).

## Key Themes

1. **Vacations dominate** — 14 S14 + 15 S15 + 3 Hotfix tickets. AV=true (advance, Cyprus/Germany) vs AV=false (Russia) is the central complexity driver.
2. **Statistics optimization** — Sprint 15 focus: Caffeine caching (#3337), `statistic_report` sync table (#3345, #3346), individual norm refinements (#3353, #3356, #3381).
3. **PM Tool integration** — 10 Sprint 15 tickets: API rate limiting, data sync, admin UI changes.
4. **Planner ordering bugs** — drag-and-drop persistence failures across both sprints (#3308, #3332, #3314, #3375).

## Priority Vacation Tickets

| # | Title | Sprint | State | Notes |
|---|-------|--------|-------|-------|
| #3092 | Advance vacation option per CS setting | S14 | closed | Major feature — two logic branches |
| #3283 | Vacation day correction (AV=true/false) | S14 | closed | Depends on #3092 |
| #3347 | AV=true corner cases next-year vacation | S15 | open | Complex allocation logic |
| #3361 | AV=True incorrect multi-year balance | S15 | open | Production ready |
| #3369 | Backend allows past vacations without deduction | S15 | open | Low priority bug |
| #3370 | Maternity leave users can't edit vacation | S15 | open | Frontend fix needed |
| #3380 | Vacations don't affect monthly norm | S15 | open | My Tasks impact |
| #3322 | Block vacation creation for next year until Dec-01 | S15 | open | New restriction |
| #2789 | Double accrual for SO-transfer employees | S15 | open | Production: 42 days instead of 18 |

## Priority Statistics Tickets

| # | Title | Sprint | State |
|---|-------|--------|-------|
| #3337 | Performance: Caffeine caching for Statistic Report | S15 | open |
| #3345 | Sync to populate statistic_report table | S15 | open |
| #3346 | Execute initial sync once via java_migration | S15 | open |
| #3353 | Individual norm: exclude pre/post employment | S15 | open |
| #3356 | Individual norm for part-month employees | S15 | open |
| #3381 | Additional norm with admin vacation hours | HF-S14 | closed |

## Figma References Found
- #3318 (chevrons, node-id=43297-298160), #3309 (employee reports, node-id=43297-298158)
- #3353 (individual norm, node-id=44763-311340), #3381 (budget norm, node-id=44744-117220)
- #3093 (PM Tool UI, node-id=38435-3910899), #2931 (notification badge)

## Google Docs References
- #3281: Email notifications spreadsheet
- #3383, #3387, #3083: PM Tool API docs

## Team
- Olga Maksimova: heaviest load (~25+ tickets)
- Irina Malakhovskaia: analytical/requirements (~15 tickets)
- Vladimir Ulyanov: backend/critical fixes (~10)
- Ilya Shumchenko: newer assignee (4)
- Sergey Navrockiy: infrastructure (3)

See also: [[REQ-vacations-master]], [[REQ-advance-vacation]], [[REQ-statistics]], [[vacation-service-implementation]], [[vacation-service-debt]]


## Session 26 Update

Sprint 15 now has **60 tickets** (58 open, 2 closed). Key changes since session 24:

### New/Updated Tickets
| # | Title | State | Labels | Notes |
|---|-------|-------|--------|-------|
| #3402 | AI-Driven Expert System (Auto QA) | open | Auto QA, To Do | Meta-ticket for this expert system |
| #3400 | Statistics: Individual norm CSV export | open | Production Ready | **Not yet in codebase** — see [[external/tickets/ticket-3400-statistics-individual-norm-export]] |
| #3392 | InnovationLab banner feature | closed | Hotfix Sprint 14 | **Deployed to both stage and release/2.1** — see [[external/tickets/ticket-3392-innovationlab-banner]] |
| #3389 | PM Tool: Skip sales-type employees | open | Production Ready | Breaking API schema change |
| #3384 | PM Tool: Employee ID 642 not found | open | Production Ready | Data mapping gap |
| #3383 | PM Tool: `id` param returns 422 | open | Production Ready | External API bug |
| #3382 | PM Tool: Batch fetch needed (422) | open | Production Ready | Query string overflow |
| #3399 | PM Tool: Rate limit 429 | open | Production Ready | Needs throttling |
| #3387 | PM Tool: Add pmtId for deep links | open | Production Ready | Feature enhancement |

### Ticket #2724 Status Change
Moved to **"Ready to Test"** — planner close-by-tag permissions feature progressing.
