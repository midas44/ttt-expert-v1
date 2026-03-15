---
type: module
tags:
  - companystaff
  - integration
  - sync
  - feign
  - cron
  - roles
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[modules/vacation-service]]'
  - '[[modules/calendar-service]]'
  - '[[architecture/roles-permissions]]'
  - '[[external/requirements/REQ-dismissal-process]]'
branch: release/2.1
---

# CompanyStaff (CS) Integration

Comprehensive analysis of CS sync across all 3 TTT services. Session 11.

## Architecture
- Shared Feign client: `CompanyStaffV2Client` (common-client module)
- V1 → V2 evolution (V1 is dead code, no V3 exists)
- Auth: V2 uses HTTP header `"token"`, V1 used query param

| Service | Syncs | Frequency |
|---------|-------|-----------|
| TTT | Employees + Contractors + Offices | Every 15 min (ShedLock) |
| Vacation | Employees + Offices | Every 15 min |
| Calendar | Offices only | Every 15 min |

## Feature Toggle Gate
All sync gated by Unleash flag `cs-sync-{env}`. If disabled, silently returns null.

## Sync Flow
1. Check `cs_sync_status` for last success timestamp → set `updatedAfter` (incremental)
2. Fetch pages (50 per page) from CS API
3. Submit each entity to 4-thread pool, 10s timeout per entity
4. On failure → add to `cs_sync_failed_entity` for retry next cycle
5. After main sync, retry all previously failed entities
6. Run post-processors if any entity succeeded
7. Record success in `cs_sync_status`

**Full sync scheduler is COMMENTED OUT** — no automatic full re-sync exists.

## Data Mapping (Key Fields)
CS username → employee.login (lowercased), CS active → enabled, CS beingDismissed → being_dismissed, CS accountingData.department (300/310) → PRODUCTION/ADMINISTRATION, CS position → cs_manager flag, specializations, city, timezone.

## Role Assignment via Post-Processors (9 total)

### Employee post-processors (6):
1. DepartmentManagerRolePostProcessor
2. **ProjectManagerRolePostProcessor** — ⚠️ BUG: removes ROLE_DEPARTMENT_MANAGER instead of ROLE_PROJECT_MANAGER
3. TechLeadRolePostProcessor
4. EmployeeNameDuplicatesPostProcessor
5. EmployeeCachePostProcessor
6. TokenPostProcessor

### Office post-processors (3):
1. AccountantRolePostProcessor
2. OfficeDirectorRolePostProcessor
3. **OfficeHRRolePostProcessor** — ⚠️ Only adds, never removes ROLE_OFFICE_HR

## Bugs Discovered (7)

| # | Severity | Description |
|---|----------|-------------|
| 1 | **CRITICAL** | ProjectManagerRolePostProcessor removes ROLE_DEPARTMENT_MANAGER instead of ROLE_PROJECT_MANAGER (wrong enum) |
| 2 | HIGH | NPE risk: CSEmployeeSynchronizer.sync() line 198 calls accountingData.getDepartment() when accountingData can be null |
| 3 | MEDIUM | OfficeHRRolePostProcessor only adds ROLE_OFFICE_HR, never removes (former HR keep role forever) |
| 4 | MEDIUM | Full sync scheduler commented out — no recovery from missed incremental updates |
| 5 | LOW | Contractor name order reversed: lastName+firstName vs firstName+lastName for employees |
| 6 | LOW | SalaryOfficeFactory redundant double existsById check |
| 7 | INFO | V1 dead code package (models, config, date deserializer) |

## Vacation Service Differences
- Publishes domain events: EmployeeHiredEvent, EmployeeFiredEvent, EmployeeMaternityBeginEvent/EndEvent, EmployeeOfficeChangedEvent
- Does NOT sync contractors
- Tracks isWorking/isMaternity flags, firstDate

## Related
- [[modules/ttt-service]] — TTT service
- [[modules/vacation-service]] — vacation service
- [[modules/calendar-service]] — calendar service
- [[external/requirements/REQ-dismissal-process]] — dismissal workflow
- [[architecture/roles-permissions]] — role assignment
