---
type: exploration
tags:
  - database
  - sick-leave
  - day-off
  - data-patterns
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[absence-data-model]]'
  - '[[vacation-schema-deep-dive]]'
  - '[[sick-leave-service-implementation]]'
  - '[[day-off-service-implementation]]'
branch: release/2.1
---
# Sick Leave & Day-Off Data Patterns (Timemachine)

Data exploration of ttt_vacation schema on timemachine env.

## Sick Leave Data (348 records)

### Status × Accounting Status Distribution
| Status | Accounting | Count | % |
|--------|-----------|-------|---|
| CLOSED | NEW | 215 | 62% |
| CLOSED | PAID | 96 | 28% |
| DELETED | NEW | 16 | 5% |
| REJECTED | REJECTED | 13 | 4% |
| OPEN | NEW | 8 | 2% |

**Key insight**: Majority (215/348) are CLOSED but accounting_status still NEW — large backlog of unprocessed sick leaves for accounting. Only 28% fully processed (CLOSED/PAID).

### Volume by Year
~104-114 sick leaves per year (2023-2025). Average duration 9-11 calendar days. **Extreme outliers**: max 140-141 days (long-term illness). 2026 partial: 9 records, avg 5.7 days.

### File Attachments
184 of ~332 non-deleted sick leaves (55%) have files attached. 231 total files — some have multiple documents.

### Notify-Also
99 sick leaves (30%) have additional notification recipients.

### Office Notification Receivers
67 configured entries across all offices.

### Schema Note
FK columns named `sick_leave` (not `sick_leave_id`) — inconsistent naming convention.

## Day-Off Data

### Request Status Distribution (3,238 records)
| Status | Count | % |
|--------|-------|---|
| APPROVED | 2,902 | 89.6% |
| DELETED | 223 | 6.9% |
| DELETED_FROM_CALENDAR | 82 | 2.5% |
| NEW | 18 | 0.6% |
| REJECTED | 13 | 0.4% |

High approval rate (89.6%). DELETED_FROM_CALENDAR (82, all from 2025) — bulk calendar sync event(s) in 2025.

### Ledger Duration Patterns (5,334 entries)
| Duration | Count | Meaning |
|----------|-------|---------|
| 8 (hours) | 2,853 | Full working day credit (worked holiday) |
| 0 (hours) | 2,454 | Day-off taken (debit) |
| 7 (hours) | 27 | Half-day / short day |

Credit (2,853) > debit (2,454) — ~399 earned but unused day-off credits exist in the system.

### Approval Stats (5,447 records)
ASKED 3,390 (62%), APPROVED 2,056 (38%), REJECTED 1. High ratio of ASKED suggests optional approvers are configured but rarely act, or ASKED state retained after main approval.

### Year Distribution
Data starts 2024 (timemachine env). 2024: 2,354; 2025: 2,134; 2026: 846 (partial).

### DELETED_FROM_CALENDAR
All 82 records from 2025 only — likely a specific calendar sync event or feature introduction.

Links: [[absence-data-model]], [[vacation-schema-deep-dive]], [[sick-leave-service-implementation]], [[day-off-service-implementation]]
