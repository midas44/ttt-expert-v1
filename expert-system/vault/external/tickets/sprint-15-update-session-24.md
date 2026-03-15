---
type: external
tags:
  - gitlab
  - tickets
  - sprint-15
  - pm-tool
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[external/tickets/sprint-14-15-overview]]'
  - '[[branches/pm-tool-stage-comparison]]'
branch: release/2.1
---
# Sprint 15 Tickets — Session 24 Update

60 total Sprint 15 issues (58 open, 2 closed). 7 updated since 2026-03-12.

## New Tickets (since session 23)

### #3402 — [QA Automation] AI-Driven Expert System
- **Created**: 2026-03-13
- **Labels**: Auto QA, To Do
- **Note**: This ticket tracks the expert system project itself

### #3401 — [Admin] [Projects] Create Ratelimit for PM tool client
- **Created**: 2026-03-10
- **Status**: Production Ready
- **Code**: Already merged to release/2.1 — configurable `RateLimiter` in `PmToolEntitySyncLauncher`

### #3400 — [Statistics] Export norm by individual calendar
- **Created**: 2026-03-10
- **Status**: Production Ready

### #3399 — [Admin] [Projects] Ratelimit on PM tool side
- **Created**: 2026-03-06
- **Status**: Production Ready

## Key Status Changes

- **#2724** — CRITICAL planner auto-close by labels: now "Ready to Test" (2026-03-13). Code merged (session 24 analyzed new permission system)
- **#3389** — Skip employee with sales type: updated 2026-03-12 (relates to PM Tool sync `removeSalesFromProject`)
- **#3384** — Unable to locate employee by ID: updated 2026-03-12 (relates to `validateEmployeesExist` in sync)
- **#3383** — PM Tool API error with id parameter: updated 2026-03-12

## PM Tool Integration Cluster

Tickets #3382-3389, #3397, #3399, #3401 form a cluster addressing PM Tool sync reliability. Most are "Production Ready". Code changes include: rate limiting, sales filtering, employee validation, failed entity retry, per-entity transactions.

See also: [[branches/pm-tool-stage-comparison]], [[external/tickets/sprint-14-15-overview]]
