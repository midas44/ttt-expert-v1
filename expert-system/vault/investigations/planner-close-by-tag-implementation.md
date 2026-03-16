---
type: investigation
tags:
  - planner
  - close-by-tag
  - sprint-15
  - '2724'
  - backend
  - frontend
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[modules/planner-assignment-backend]]'
  - '[[modules/frontend-planner-module]]'
  - '[[modules/pm-tool-integration-deep-dive]]'
---
# Planner Close-by-Tag Implementation (#2724)

## Overview
Sprint 15 CRITICAL feature. Solves planner performance degradation caused by uncontrollable growth of task assignments (e.g., DirectEnergie-ODC project: ~10 new assignments/employee/day, never cleaned up). Allows managers to configure per-project labels that automatically close matching assignments during Refresh/Load-from-tracker.

**Tickets:** #2724 (main), related #2408, #3375
**Status:** Ready to Test (4 MRs merged to release/2.1: !5293, !5299, !5301, !5303)
**Migration:** V2.1.27 — `V2_1_27_20260301000000__create_planner_close_tag_table.sql`

## Database Schema

```sql
CREATE TABLE ttt_backend.planner_close_tag (
    id          BIGSERIAL PRIMARY KEY,
    project_id  BIGINT NOT NULL,
    tag         VARCHAR(255) NOT NULL,
    CONSTRAINT fk_planner_close_tag_project
        FOREIGN KEY (project_id) REFERENCES ttt_backend.project(id) ON DELETE CASCADE,
    CONSTRAINT uq_planner_close_tag_project_tag UNIQUE (project_id, tag)
);
CREATE INDEX idx_planner_close_tag_project_id ON ttt_backend.planner_close_tag(project_id);
```

Key constraints:
- CASCADE DELETE: removing project removes all its close tags
- UNIQUE(project_id, tag): no duplicate tags per project
- tag VARCHAR(255) NOT NULL

## REST API — Close Tag CRUD

**Base path:** `/v1/projects/{projectId}/close-tags`
**Controller:** `PlannerCloseTagController` (129 lines)
**Security:** All endpoints require `AUTHENTICATED_USER` or `PROJECTS_ALL`

| Method | Path | Handler | Response | Permission |
|--------|------|---------|----------|------------|
| GET | `/v1/projects/{projectId}/close-tags` | `list()` | `List<PlannerCloseTagDTO>` | Any authenticated user |
| POST | `/v1/projects/{projectId}/close-tags` | `create()` | `PlannerCloseTagDTO` (HTTP 200, not 201) | CREATE |
| PATCH | `/v1/projects/{projectId}/close-tags/{tagId}` | `update()` | `PlannerCloseTagDTO` | EDIT |
| DELETE | `/v1/projects/{projectId}/close-tags/{tagId}` | `delete()` | void | DELETE |

**Note:** POST returns HTTP 200, not 201 — unconventional for create endpoint.

### Controller Validation
- `@PathVariable("projectId") @NotNull @ProjectIdExists` — custom annotation validates project exists
- `@Valid @RequestBody` on create/update (enforces `@NotBlank tag`)

## Permission Model

**Service:** `PlannerCloseTagPermissionService` (64 lines)
**Permission types:** CREATE, EDIT, DELETE (enum `PlannerCloseTagPermissionType`)
**Model:** Binary all-or-nothing — either all three permissions or none.

**Who can manage tags (create/edit/delete):**
- Admin (`isAdmin()`)
- Project manager (`current.getId().equals(project.getManagerId())`)
- Senior manager (`current.getId().equals(project.getSeniorManagerId())`)
- Project owner (`current.getId().equals(project.getOwnerId())`)

**Who cannot:**
- Read-only users — NO permissions (empty set)
- Plain employees — can LIST tags (200 OK on GET) but get 403 on POST/PATCH/DELETE

## Service Layer — PlannerCloseTagServiceImpl (139 lines)

### create(projectId, tag)
1. Validates projectId not null, tag not blank
2. Permission check: CREATE
3. Loads Project entity (NotFoundException if missing)
4. Calls `doSaveTagInNewTransaction()` — **REQUIRES_NEW** transaction for isolation
5. On `DataIntegrityViolationException` (duplicate key): catches, returns existing tag → **idempotent create**
6. Uses `@Lazy self` injection to invoke `doSaveTagInNewTransaction()` through Spring proxy (required for nested transaction)

### update(projectId, tagId, tag)
1. Validates projectId, tag
2. Permission check: EDIT
3. Loads tag by tagId (NotFoundException if missing)
4. **Ownership check:** tag.project.id must equal projectId → `ValidationException("Planner close tag does not belong to project")`
5. **No-op optimization:** if new tag equals existing tag, returns without saving
6. Uses `saveAndFlush()` for immediate constraint check
7. On duplicate: throws `ValidationException("Planner close tag already exists for project")`

### delete(projectId, tagId)
1. Validates projectId
2. Permission check: DELETE
3. Loads tag (NotFoundException if missing)
4. **Ownership check:** same as update
5. Deletes from repository

### Error Messages
- `"Project id is required"` — null projectId
- `"Tag must not be blank"` — blank tag
- `"Planner close tag does not belong to project {projectId}"` — cross-project access
- `"Planner close tag already exists for project {projectId}"` — duplicate on update
- `NotFoundException(Project.class)` — project not found
- `NotFoundException(PlannerCloseTag.class)` — tag not found

## Core Logic — CloseByTagServiceImpl (267 lines)

**Entry point:** `apply(PlannerSectionBO section)` — called during Refresh and Load-from-tracker flows.

### Flow
1. **Guard checks:** null section → return; `hasApplicableContext` checks for projectId or employeeLogin
2. **Resolve date:** priority: section.date → section.startDate → section.endDate
3. **Load assignments:** search for date with `strict=false`
4. **Load tasks:** by assignment task IDs into a map
5. **Group by project:** assignments grouped by projectId
6. **Tag matching:** per project, loads close tags, checks each assignment's task `ticket_info`

### Tag Matching Logic
```java
// Case-insensitive substring matching
StringUtils.containsIgnoreCase(ticketInfo, tag)
```
- A tag "closed" matches "closed", "CLOSED", "[closed]", "already-closed", etc.
- Blank tags are filtered out
- Blank ticket_info is skipped
- Projects without close tags are skipped entirely

### Assignment Closing — Two Paths

**Path 1: Existing assignment (has DB id)**
- `closeByTagSetClosedAndReturnHasReportOnDate(assignmentId)` — marks closed in DB, returns whether date has report
- If HAS report: stop (no WebSocket event — row stays visible because user reported hours)
- If NO report: publish `TaskAssignmentPatchEvent` with `closed=true` (row disappears from UI)

**Path 2: Generated assignment (no DB record yet)**
- Creates real assignment with `closed=true` via `createForCloseByTag(createRequest)`
- On creation failure: **silently swallowed** with debug log only
- Checks for report on task/assignee/date
- If HAS report: stop
- If NO report: publish `TaskAssignmentGenerateEvent` with nested `AddEvent` (row disappears)

### Key Behavioral Rules
1. Closed assignments don't propagate to future dates (excluded from "last actual" logic)
2. Assignment with report stays visible even when closed — report data preserved
3. Close-by-tag runs AFTER tracker sync / refresh, not during
4. WebSocket events enable real-time UI updates without page reload

## Frontend Implementation (!5301)

### UI Changes
- "Project employees" tooltip/popup renamed to **"Project settings"** (RU: "Настройки проекта")
- Modal redesigned with two tabs:
  - **"Project members"** (existing employee management)
  - **"Tasks closing"** (new tag management) (RU: "Закрытие задач")

### New Components
- `PlannerTagsAdd.js` — form with text field + add button (Formik)
- `PlannerTagsList.js` — tag list table with new-item highlighting + scroll-to-new
- `PlannerTag.js` — inline-editable tag cell (click to edit, Enter to save, Escape to cancel)
- `PlannerModalDelete.js` — generalized delete button (renamed from PlannerEmployeeDelete)

### Tags Tab Content
1. Explanatory text about auto-closing behavior
2. Add tag form (text input + "Add" button)
3. Tag list table with inline editing and delete buttons

### New-Item Highlighting
- Green left border (5px) on new items via `.new-item::before` CSS
- Auto-scroll to newly added item
- Highlight auto-clears after rendering

### Localization Keys
- `project_settings`, `add_tag`, `tag_for_closing`, `tags_for_closing`
- `tags_text` (explanatory text about auto-closing)
- `tabs.project_members`, `tabs.task_closing`

## Integration Tests

### PlannerCloseTagControllerIntegrationTest (282 lines)
8 test methods covering CRUD + permissions:
1. `createAndListTagsForProject` — create via POST, verify in GET
2. `updateTagForProjectWithPatch` — create, update via PATCH, verify
3. `updateTagConflictDuplicateTag` — create two tags, update second to match first → 400
4. `createTagTwiceWithSameNameReturnsExistingTag` — idempotent create verified
5. `deleteTagForProject` — create, delete, verify empty list
6. `createTagAsOwner` — owner permission verified
7. `createTagAsSeniorManager` — senior manager permission verified
8. `whenCurrentUserIsPlainEmployee_canListTagsButCannotCreateUpdateDelete` — 200 on GET, 403 on POST/PATCH/DELETE

### CloseByTagIntegrationTest (761 lines)
End-to-end test with WireMock (GitLab tracker) and mocked PM Tool:
1. Sync projects from PM Tool (WireMock)
2. Set up tracker, create task with closed ticket
3. Add project member, create time report
4. Generate assignments, verify visibility
5. Add close tag `[closed]`
6. Refresh for next day → verify: assignment `closed=true` in DB, WebSocket GENERATE event, not visible in filtered search

## Design Issues / Test Gaps Identified
1. **Silent failure on generated assignment creation** — creation errors swallowed with debug log
2. **POST returns 200 instead of 201** — unconventional REST
3. **No max tag count per project** — could create unlimited tags
4. **No tag length validation** beyond VARCHAR(255) DB constraint
5. **Substring matching false positives** — tag "fix" matches "prefix", "fixed", "fixture"
6. **No audit trail** — no logging of who created/modified/deleted tags
7. **Manager role only via project role** — department manager not checked in permissions
8. **No bulk operations** — no endpoint to delete all tags or create multiple at once
9. **No pagination on tag list** — GET returns all tags, could be large for projects with many tags
10. **Race condition on update** — `saveAndFlush` catches duplicate but no optimistic locking


## Live Testing Results (S74 — Timemachine)

**Environment:** timemachine, build 2.1.26-SNAPSHOT.290209 (March 11, 2026)
**Test project:** Administration (id=145), DirectEnergie-ODC (id=1225)

### API CRUD Testing (16 tests)

| # | Test | Method | Expected | Actual | Status |
|---|------|--------|----------|--------|--------|
| 1 | Create tag `[closed]` | POST | 201, tag created | **200**, tag created `{"id":1,"projectId":145,"tag":"[closed]"}` | PASS (HTTP code issue noted) |
| 2 | List tags | GET | Array with 1 tag | `[{"id":1,"projectId":145,"tag":"[closed]"}]` | PASS |
| 3 | Create second tag `done` | POST | Tag created | `{"id":2,"projectId":145,"tag":"done"}` | PASS |
| 4 | Idempotent create (duplicate `[closed]`) | POST | Returns existing | `{"id":1,...}`, HTTP 200 | PASS — idempotent confirmed |
| 5 | Update tag via PATCH | PATCH | Tag updated | **500 HttpRequestMethodNotSupportedException** | **FAIL — CRITICAL BUG** |
| 6 | Verify list after update attempt | GET | 2 tags unchanged | `[{id:1, "[closed]"}, {id:2, "done"}]` | PASS |
| 7 | Update tag via PUT | PUT | Tag updated | **500 HttpRequestMethodNotSupportedException** | FAIL — same bug |
| 8 | Delete tag id=2 | DELETE | 200, tag removed | 200, empty response | PASS |
| 9 | Create blank tag `""` | POST | 400 validation | 400, `"Tag must not be blank"` | PASS |
| 10 | Create whitespace tag `"   "` | POST | 400 validation | 400, `@NotBlank` triggered | PASS |
| 11 | Create on non-existent project 999999 | POST | 400 not found | 400, `"Project id not found"` | PASS |
| 12 | Delete non-existent tag id=999 | DELETE | 404 | 404, `"exception.plannerclosetag.not.found"` | PASS |
| 13 | Cross-project delete (tag from project 145, via project 3146) | DELETE | 400 ownership | 400, `"does not belong to project 3146"` | PASS |
| 14 | Special chars `won't fix / закрыто <script>` | POST | Created (but sanitized?) | 200, stored raw — **no HTML sanitization** | CONCERN |
| 15 | Cleanup: delete all test tags | DELETE | 200 | 200 | PASS |
| 16 | Verify empty after cleanup | GET | `[]` | `[]` | PASS |

### CRITICAL BUG: PATCH Endpoint Not Routed

**Swagger spec confirms PATCH is missing:** Only GET, POST (collection) and DELETE (item) are registered in `/v2/api-docs?group=api`. The `@PatchMapping("/{tagId}")` on `PlannerCloseTagController.update()` is not exposed through the API gateway.

**Impact:** Tag editing is completely impossible via API. The frontend "Tasks closing" tab's inline edit feature will also fail once deployed, as it calls PATCH.

**Probable cause:** API gateway route predicates may not include PATCH method for the `/v1/projects/{projectId}/close-tags/**` path pattern. This is a gateway configuration issue, not a controller code issue (the controller has the mapping, but requests never reach it).

### XSS Concern

Tags containing `<script>` content are stored without sanitization. If the frontend renders tag text via `innerHTML` or without React's default escaping, this is exploitable. React's JSX escaping should protect by default, but worth verifying once frontend is deployed.

### Frontend Deployment Status

Build 2.1.26-SNAPSHOT.290209 (March 11, 2026) does **not** include !5301 frontend changes. The "Project settings" modal with "Tasks closing" tab is not yet available in the UI. Backend API is deployed and functional. Frontend verification deferred until new build deployed.

### Database Verification

- `planner_close_tag` table exists on timemachine (V2.1.27 migration applied)
- Table was empty before testing (no close tags configured on any project)
- Schema confirmed: `id BIGINT PK, project_id BIGINT FK, tag VARCHAR(255)`, UNIQUE(project_id, tag)


## S74 Root Cause Update — PATCH 500 Explained

**Root cause: PATCH endpoint not deployed, NOT a gateway routing bug.**

### Timeline
1. **2026-03-10 23:34 UTC** — Commit `7b764c0a7b` ("Feature/2724 snavrockiy v2") merged to `release/2.1`. This version had **only GET, POST, DELETE**. No `@PatchMapping` existed.
2. **2026-03-11 03:08 UTC** — Build `2.1.26-SNAPSHOT.290209` created from a commit that includes `7b764c0a7b` but NOT the PATCH commit.
3. **2026-03-12 08:44 UTC** — Commit `dbdb6c9663` ("Feature/2724 snavrockiy v3") added the PATCH endpoint: `update()` method, `@PatchMapping("/{tagId}")`, `PlannerCloseTagUpdateRequestDTO`. This landed ~29 hours AFTER the deployed build.

### Evidence
- OPTIONS response: `Allow: DELETE,OPTIONS` — no PATCH registered at runtime
- `git merge-base --is-ancestor dbdb6c9663 2e4c42723b` → false (PATCH commit not in deployed build)
- Deployed controller: 107 lines (GET/POST/DELETE only). Current release/2.1: 129 lines (includes PATCH).

### Bonus Design Issue: RestErrorHandler Catch-All
`RestErrorHandler` (`@RestControllerAdvice`) has `@ExceptionHandler(Exception.class)` that maps ALL unhandled exceptions to `HttpStatus.INTERNAL_SERVER_ERROR` (500). No specific handler for `HttpRequestMethodNotSupportedException` → returns 500 instead of correct 405.

### Resolution
Deploy a new build from current `release/2.1` HEAD (includes commits `dbdb6c9663` v3 and `215f325186` v4). PATCH will work. No code changes needed.

### TC-PLN-101 Reclassification
TC-PLN-101 should be reclassified from "Bug Verification" to "Deployment Verification" — the PATCH endpoint exists in code but wasn't in the deployed build. After next deployment, re-test to verify PATCH works correctly.
