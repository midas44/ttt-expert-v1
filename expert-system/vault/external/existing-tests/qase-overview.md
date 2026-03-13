---
type: external
tags:
  - qase
  - existing-tests
  - coverage
  - assessment
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[system-overview]]'
---
# Qase Test Repository Overview

**Project**: TIMEREPORT | **Total Cases**: 1,116 | **Total Suites**: 258 | **All Manual, Zero Automation**

## Suite Structure (11 Root Suites)
1. **My Tasks** (Suite 1) — task creation, renaming, comments, time entry, color indication
2. **Employee Tasks** (Suite 22) — reporting on behalf, color coding
3. **Vacations** (Suite 36) — LARGEST: vacation CRUD, days-off, sick leaves, calendar recalculation, day calculations
4. **Approval** (Suite 131) — by employees (81+ cases) and by projects (55+ cases)
5. **Planner** (Suite 157) — task assignment, tracker sync, overlaps
6. **Statistics** (Suite 182) — EMPTY, 0 cases
7. **Admin** (Suite 183) — projects (66), employees (12), parameters (10), calendars (23), API keys (10)
8. **Accounting** (Suite 207) — salary (18), periods (14), vacation payments (41), corrections (22), sick leave accounting (27)
9. **Notifications** (Suite 235) — in-app (14 cases)
10. **User Settings** (Suite 239) — general, trackers, export (19 cases)
11. **Email Notifications** (Suite 244) — vacation (9), general (13), day-off (7), sick leave (14), digest (11)

## Quality Assessment
**Weaknesses**: No test steps (title+description only), no preconditions, severity/priority unset, all draft status, zero automation, sparse descriptions. One-time bulk import (2025-02-13).

## Coverage Gaps
- Statistics page: 0 cases
- Admin Export: 0 cases
- My Sick Leaves, Availability Schedule, Employee Vacation Days, Employee Sick Leaves, Days Off: all placeholder (0 cases)
- Login/Authentication: missing entirely
- RBAC/Permissions: no dedicated suite
- API testing: only 10 API key cases
- Cross-browser/responsive/performance: absent

## Implication for Phase B
Our generated test docs will be significantly more detailed and executable than existing Qase content. Low risk of duplication since Qase cases lack steps.

## Related
- [[system-overview]]
- [[vacation-service]]
- [[confluence-overview]]
