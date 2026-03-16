---
type: investigation
tags:
  - pm-tool
  - ratelimit
  - sprint-15
  - '3401'
  - '3399'
  - sync
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[modules/pm-tool-integration-deep-dive]]'
  - '[[modules/planner-assignment-backend]]'
---
# PM Tool Rate Limiter Implementation (#3401)

## Overview
Sprint 15 feature. Adds client-side rate limiting to PM Tool sync to prevent HTTP 429 errors from the PM Tool API. The PM Tool backend (Laravel/PHP) enforces 60 requests per minute; TTT now self-throttles to 50 RPM (safety margin).

**Tickets:** #3401 (implementation), #3399 (problem report — 429 errors during sync)
**Status:** Production Ready (2 MRs merged: !5295, !5297)
**Companion:** #3399 documents the original `Illuminate\Http\Exceptions\ThrottleRequestsException` from PM Tool

## Problem Context
During PM Tool project sync, TTT pages through `GET /api/v2/projects?limit=50&page=N` to fetch all projects. Without rate limiting, TTT exceeded PM Tool's 60 RPM limit, triggering:
```
feign.RetryableException: 429 Too Many Requests
Illuminate\Http\Exceptions\ThrottleRequestsException
```
The error was observed on `pm-dev2.noveogroup.com` during sync operations.

## Implementation

### Rate Limiter — Guava RateLimiter
**File:** `PmToolEntitySyncLauncher.java` (181 lines)
**Mechanism:** `com.google.common.util.concurrent.RateLimiter` — token-bucket / smooth-bursty algorithm

```java
@Value("${pmTool.sync.fetch-rate-per-minute:50}") final int fetchRatePerMinute
this.fetchRateLimiter = RateLimiter.create(fetchRatePerMinute / 60.0);
// 50 RPM = 0.833 permits/sec = ~1.2 seconds between requests
```

**Where applied:** Inside `syncInternal()` pagination loop, before each `entitySynchronizer.fetch(request)`:
```java
fetchRateLimiter.acquire(); // Blocking — sleeps until permit available
PmToolPageResponse<T> response = entitySynchronizer.fetch(request);
```

### Configuration
- **Spring property:** `pmTool.sync.fetch-rate-per-minute`
- **Default:** 50 RPM (changed from 60 in !5297 for safety margin)
- **Not overridden** in any config file — uses default value everywhere
- **Retry batch size:** `pmTool.sync.retry-batch-size` defaults to 10

### Thread Safety
- `RateLimiter` is thread-safe (internal synchronization)
- Single instance shared across all concurrent sync operations (singleton Spring bean)
- Multiple entity type syncs compete for the same rate budget — by design
- Worker thread pool: configurable via `ttt.threading.pmToolSyncPool.size`

### Sync Flow with Rate Limiting
```
sync() → syncInternal() [main pages]
  └─ for each page:
       fetchRateLimiter.acquire()  ← BLOCKS here if rate exceeded
       entitySynchronizer.fetch(request)
       for each entity:
         threadPool.submit(entitySynchronizer.sync(entity))
  └─ collect futures (10s timeout each)
→ retry failed entities in batches of retryBatchSize
  └─ each batch goes through syncInternal() (same rate limiter)
→ if any success: entitySynchronizer.postProcess()
→ if main sync success: record PmToolSyncStatus
```

### Edge Cases
1. **No timeout on acquire()** — if rate limiter has large debt, could block indefinitely
2. **Null currentPage response** — marks sync as failed but pagination continues via nextPage
3. **Incremental sync date truncation** — `LocalDateTime.toLocalDate()` truncates time, may re-process same-day entities
4. **Unbounded future map** — all pages fetched and submitted before any result collected; large datasets may hold many futures
5. **No idempotency** — same entity on multiple pages will be synced twice
6. **No 429 retry logic** — rate limiter is purely preventive; if 429 still occurs, existing retry mechanism handles it

## Dependency Added
- `com.google.guava:guava` added to `ttt/service/service-impl/pom.xml`

## Unit Tests
**File:** `PmToolEntitySyncLauncherTest.java` (157 lines)

| Test | What it verifies |
|------|-----------------|
| `syncRespectsRateLimit_threeFetchCallsTakeAtLeastTwoSeconds` | 3 fetches at 60 RPM take ≥1900ms (first free, 2 intervals) |
| `syncRespectsRateLimitWhenCalledFromMultipleThreads` | 4 fetches across 2 threads at 60 RPM take ≥2900ms (shared limiter) |

**Note:** Tests use 60 RPM (not 50), timing-based assertions with generous bounds.

## Verification Criteria (from #3399)
After deployment:
1. `ttt_backend.pm_tool_sync_failed_entity` table should have no records
2. `ttt_backend.pm_sync_status` last successful sync time should match deployment time

## Connections
- [[modules/pm-tool-integration-deep-dive]] — full PM Tool architecture
- [[modules/planner-assignment-backend]] — planner that uses synced projects
- [[investigations/planner-close-by-tag-implementation]] — also Sprint 15, uses same project sync
