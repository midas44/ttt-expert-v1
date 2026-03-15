---
type: pattern
tags:
  - feature-toggles
  - unleash
  - infrastructure
  - configuration
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[architecture/system-overview]]'
  - '[[modules/ttt-service]]'
  - '[[modules/vacation-service]]'
  - '[[modules/calendar-service]]'
  - '[[external/tickets/pm-tool-integration]]'
  - '[[patterns/frontend-cross-module-patterns]]'
branch: release/2.1
---
# Feature Toggles (Unleash)

TTT uses Unleash for feature flag management across all 4 services. Toggles control infrastructure behavior (async processing, external sync), not UI features.

## Toggle Inventory (6 unique)

| Toggle Code | Services | Purpose |
|---|---|---|
| `email-async` | TTT, Vacation | Route email sending through async (RabbitMQ) vs synchronous path |
| `ttt-vacation-async` | TTT | Async vacation operations from TTT service (period changes, recalculation) |
| `calendar-vacation-async` | Calendar | Async vacation operations from calendar service |
| `cs-sync` | TTT, Vacation, Calendar | Enable CompanyStaff synchronization |
| `pmtool-sync` | TTT | Enable PM Tool project synchronization |
| `employee-project-initial-sync` | Vacation | Initial employee-project data sync |

## Environment-Specific Naming

Sync toggles use **environment-qualified names**: `{code}-{env}` (e.g., `pmtool-sync-timemachine`). This allows per-environment control of sync features:
```java
String pmToolSyncFlag = String.format("%s-%s", FeatureToggleType.PM_TOOL_SYNC.getCode(), env);
featureToggleService.isEnabled(pmToolSyncFlag);
```

## Architecture

- **Configuration**: `UnleashConfiguration` bean in each service (TTT, Vacation, Calendar, Frontend)
- **Service layer**: `FeatureToggleService` interface + impl in each service, delegates to `Unleash.isEnabled()`
- **REST API**: `GET /v1/feature-toggles` (list all), `GET /v1/feature-toggles/{name}` (single) — exposed by TTT backend
- **Frontend**: Redux duck at `common/ducks/featureFlags/` — subscribe/fetch pattern, stores flags as `{name: boolean}` map
- **Config**: `unleash.url`, `unleash.key`, `unleash.env` from application properties

## Usage Patterns

1. **Email**: `InternalEmailService` checks `EMAIL_ASYNC` before sending — if enabled, publishes to message queue; if disabled, sends synchronously
2. **Period operations**: `InternalOfficePeriodService` checks `TTT_VACATION_ASYNC` — if enabled, vacation recalculation happens asynchronously
3. **CS Sync**: `CSSyncLauncherImpl` in each service gates the sync scheduler
4. **PM Tool**: `PmToolSyncLauncherImpl` uses environment-qualified flag, has dedicated thread pool (`pmToolSyncPool`)

## Test Impact

- Tests need to account for toggle states — behavior differs significantly
- Integration tests (`PmToolSyncIntegrationTest`, `CloseByTagIntegrationTest`) mock Unleash toggle states
- No UI feature flags — all toggles are backend infrastructure, so frontend tests are unaffected by toggle state
- Frontend fetches toggle list at auth time but doesn't conditionally render based on flags currently
