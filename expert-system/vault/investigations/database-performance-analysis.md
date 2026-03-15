---
type: investigation
tags:
  - performance
  - database
  - postgresql
  - infrastructure
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/system-overview]]'
  - '[[ttt-report-service]]'
branch: release/2.1
---
# Database Performance Analysis

Investigation of PostgreSQL performance characteristics on timemachine environment (PostgreSQL 12.2, Alpine).

## Database Overview
- **Total size**: 2,626 MB (~2.6 GB)
- **Schemas**: ttt_backend, ttt_vacation, ttt_email, ttt_calendar
- **Top 3 tables** account for 94.5% of database: task_report (1,526 MB), task_assignment (594 MB), task (361 MB)

## Critical Performance Issues

### 1. Stale Statistics (CRITICAL)
The 3 largest tables have **NEVER been ANALYZED**. pg_stat shows 0-1 live tuples while actual counts are 3.5M, 2.5M, and 666K. The query planner makes decisions with wildly wrong cardinality estimates, likely producing catastrophically suboptimal query plans.

### 2. Low Cache Hit Ratio (CRITICAL)
- **Table cache hit**: 52.34% (target: >99%)
- **shared_buffers**: only 128 MB for a 2.6 GB database (should be ~25% of RAM)
- Index cache hit: 98.92% (acceptable)

### 3. Massive Sequential Scans
- task_report: 824M rows seq-scanned (688 scans)
- employee_office: 215M rows seq-scanned, **zero index scans** (33,835 scans)
- employee_dayoff_request: 95M rows seq-scanned, only 349 idx scans
- employee_dayoff: 80M rows seq-scanned, only 18 idx scans
- office_calendar: 30,604 seq scans, **zero index scans**

### 4. Temp File Spills
3,264 temp files totaling **9 GB** in 3 days, caused by 4 MB work_mem being too low.

### 5. Unused Indexes (~526 MB wasted)
| Table | Index | Size | Scans |
|-------|-------|------|-------|
| task_report | idx_task_report_actual_efforts | 88 MB | 0 |
| task_report | idx_52238_fk770ccd2ec078b221 | 92 MB | 6 |
| task_report | idx_52238_fk770ccd2ef8cb35bd | 88 MB | 2 |
| task_assignment | idx_task_assignment_show_in_history | 55 MB | 0 |
| task | tbl_task_name_gin_trgm_idx | 90 MB | 1 |
| task | name_upper_index | 70 MB | 5 |
| task | idx_task_bound_employee | 14 MB | 0 |
| task | idx_task_created_time | 14 MB | 0 |
| tracker_work_log | 3 non-PK indexes | 14.7 MB | 0 |

### 6. Missing FK Indexes (24 total)
Critical missing indexes include:
- **employee_office.employee** (33,835 seq scans, zero idx scans!)
- employee_dayoff.employee, employee_dayoff_request.employee/approver
- task.creator, task_assignment.assigner/next_assignment
- Multiple vacation FK columns

### 7. Connection Pooling
57 idle connections out of 58 total (1 active). Suggests connection pooling misconfiguration or excessive pool sizes across services (4 services × 15-20 max = 60-80 potential connections).

## PostgreSQL Configuration Issues
| Parameter | Value | Recommended |
|-----------|-------|-------------|
| shared_buffers | 128 MB | ~1 GB (25% RAM) |
| work_mem | 4 MB | 16-64 MB |
| maintenance_work_mem | 64 MB | 256 MB |
| random_page_cost | 4 (HDD default) | 1.1-1.5 (if SSD) |
| effective_io_concurrency | 1 | 200 (if SSD) |

## Related
- [[architecture/system-overview]] — database is shared PostgreSQL with schema isolation
- [[database-performance-analysis]] — design issues from this analysis
- [[ttt-report-service]] — largest table, most performance concerns
- [[external/EXT-cron-jobs]] — scheduled jobs that query these tables
