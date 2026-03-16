---
type: investigation
tags:
  - ci
  - build-number
  - footer
  - actuator
  - sprint-15
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[architecture/frontend-architecture]]'
  - '[[modules/admin-panel-deep-dive]]'
---
# CI Build Number in App Footer (#3036)

## Overview

Sprint 15 feature: ensure the build number displayed in the app footer correctly reflects the CI pipeline that produced the deployed build. Previously, the build number could be stale (not updated when only non-TTT services changed).

**Status:** Ready to Test (Sprint 15). Passed on qa-1, qa-2, timemachine. Waiting for stage/preprod/prod verification.

## Problem

The footer shows `Build #: X | Build date: Y` where X = `app.version` from ttt-backend's `/actuator/info`. Two issues:
1. **Stale number**: If a CI pipeline only rebuilt vacation/calendar/email services (no changes to ttt-backend), the ttt-backend's actuator still reported the OLD pipeline ID
2. **No pipeline traceability**: Could not reliably match a deployed version to a specific CI pipeline

## Solution

### Approach 1 (Frontend — REVERTED)
MR !5258 by ishumchenko: Call all 4 actuator endpoints (ttt, vacation, calendar, email), compare build numbers, display highest. **Reverted** in MR !5287 because:
- Complex frontend logic
- Still didn't guarantee accuracy for rollbacks
- Backend-only solution was simpler

### Approach 2 (CI — KEPT)
MR !5275 by qnguyen: Modify `.gitlab-ci-ttt-module.yml` to **always rebuild the TTT service** on key branches, even if no TTT code changed. This ensures `actuator/info` always reflects the current pipeline ID.

**CI Rules** (`gitlab/modules/.gitlab-ci-ttt-module.yml`):
- Always build on: `master`, `release/*`, `hotfix/*`, `pre-release/v*`, `hotfix-pre-release/v*`, `development-ttt`
- Skip on other branches from non-push sources

### Limitation
Only works for **forward deployments**. Rollbacks will show the old version's pipeline ID, not the rollback pipeline. Follow-up: #3396.

## Technical Details

### Backend (Spring Actuator)
`ttt/app/src/main/resources/application.yml`:
```yaml
info:
  app:
    name: "TTT backend REST API"
    version: ${project.version}.${env.CI_PIPELINE_ID}
  maven:
    buildtime: ${maven.build.timestamp}
    commit: ${git.commit.id}
  ci:
    commit: ${env.CI_COMMIT_SHA}
    build-number: ${env.CI_PIPELINE_ID}
```

Version format: `<maven-version>.<CI_PIPELINE_ID>` → e.g., `2.1.26-SNAPSHOT.290485`

### Frontend (React)

**API** (`ducks/info/api.js`):
```js
export const getBuildDetails = () => tttApiRequest.get('/actuator/info');
export const getLoginDetails = () => baseApiRequest.get('/actuator/info');
```
- `getBuildDetails`: `/api/ttt/actuator/info` (ttt-backend, port 9583)
- `getLoginDetails`: `/actuator/info` (frontend-app, port 9584) — used only for demo auth detection

**Selectors** (`ducks/info/selectors.js`):
```js
export const selectBuildVersion = state => state.info.build.app ? state.info.build.app.version : 0;
export const selectBuildDate = state => state.info?.build?.maven?.buildtime ? MomentPlugin.formatDate(...) : '';
```

**Footer** (`components/Footer/index.js`):
Renders `Build #: ${build} | Build date: ${date}`. Default: `build: '0'`, `date: '0'`.

### Gateway Routing
- `/api/ttt/**` → ttt-backend (StripPrefix=2)
- `/**` → ttt-frontend (catch-all)

### Nginx Access
`/actuator/info` is explicitly allowed without access restrictions (lines 55-58 in `docker/nginx/conf.d/ttt.conf`). Broader `/actuator` paths are restricted.

## QA Verification Status
| Environment | Status | Notes |
|---|---|---|
| qa-1 | PASS | Verified by vulyanov |
| qa-2 | PASS | Verified by vulyanov |
| timemachine | PASS | Verified by vulyanov |
| stage | UNKNOWN | Needs verification after next deployment |
| preprod | UNKNOWN | Needs verification |
| prod | UNKNOWN | Needs verification |

## Related
- [[architecture/frontend-architecture]]
- [[modules/admin-panel-deep-dive]]
- #3396 — follow-up for rollback version tracking
- MRs: !5258 (reverted frontend), !5275 (CI fix, kept), !5287 (revert of !5258)
