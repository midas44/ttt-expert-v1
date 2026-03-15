---
type: module
tags:
  - planner
  - permissions
  - close-by-tag
  - sprint-15
  - code-change
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[analysis/role-permission-matrix]]'
  - '[[frontend-planner-module]]'
branch: release/2.1
---
# Planner Close-by-Tag Permission System

Sprint 15 addition (#2724) — adds object-level permission enforcement to the close-by-tag feature, replacing the previously unguarded mutation endpoints.

## Permission Model

New `PlannerCloseTagPermissionType` enum with three values: `CREATE`, `EDIT`, `DELETE` — implementing the `ObjectPermission` marker interface pattern used elsewhere in TTT.

`PlannerCloseTagPermissionService` extends `BaseObjectPermissionService` and calculates permissions per project+user:

**Authorized roles (all-or-nothing — all 3 permissions granted together):**
- Admin (`employee.isAdmin()`)
- Project Manager (`employee.id == project.managerId`)
- Senior Manager (`employee.id == project.seniorManagerId`, OR admin — redundant but harmless)
- Project Owner (`employee.id == project.ownerId`)

**Denied:** read-only users get empty set; plain employees get empty set.

**Note:** There is no partial permission grant — if authorized, user gets CREATE+EDIT+DELETE together.

## Service Changes (PlannerCloseTagServiceImpl)

1. **Permission checks added** to `create()`, `update()`, `delete()` — each calls `permissionService.validate(context, requiredPermission)` before proceeding.

2. **Race condition fix in `create()`** — old check-then-act (`existsByProjectIdAndTag` → save) replaced with try-save-first pattern using `REQUIRES_NEW` transaction isolation via `@Lazy` self-injection. On `DataIntegrityViolationException`, catches and returns existing tag. Create is now **idempotent** (get-or-create semantics).

3. **Race condition fix in `update()`** — old pre-check replaced with try/catch on `saveAndFlush`. On duplicate, throws `ValidationException` (not idempotent — update to existing name fails).

4. **Cross-project validation** in delete/update — verifies tag belongs to specified project.

5. **No-op optimization** in update — if new tag equals current, returns immediately.

## New Repository Method

`Optional<PlannerCloseTag> findByProjectIdAndTag(Long projectId, String tag)` — used in create's fallback path.

## Integration Tests (8 test cases)

Using `@SpringBootTest`, MockMvc, Testcontainers PostgreSQL, mocked `InternalEmployeeService`:
1. Create + list as manager
2. Update via PATCH
3. Update conflict (duplicate → 400)
4. Idempotent create (same tag twice → same ID)
5. Delete
6. Create as owner
7. Create as senior manager
8. **Permission denial** — plain employee can list (200) but not create/update/delete (403)

### Test gaps identified:
- No admin user test
- No `readOnly=true` user test
- No cross-project manipulation test
- TestSecurityConfig bypasses `@PreAuthorize` — tests service-layer permissions only

## Relation to Existing Knowledge

This addresses a gap noted in [[analysis/role-permission-matrix]] — the planner close-tag endpoints previously had no object-level permission checks. The pattern follows TTT's `BaseObjectPermissionService` architecture used by other modules.

The `ObjectPermission` pattern (enum + context BO + permission service) is consistent with [[roles-permissions]] if it exists.

See also: [[frontend-planner-module]], [[planner-close-tag-permissions]]


## Development Evolution (Session 27 Analysis)

The feature went through 4 iterations revealing the development strategy:

### CRITICAL-2 (578e75249f, 2026-03-12)
Initial full-stack implementation: 34 files, 821 insertions. Frontend components (PlannerTagsAdd, PlannerTagsList), table enhancements with auto-scroll, new SVG icons, backend CRUD endpoints. **No permission checks** — any authenticated user could manage tags.

### v3 (dbdb6c9663, 2026-03-12)
Strategic reversion — all 821 lines of frontend code removed. Focus shifted to backend robustness: added 181 integration tests, REST controller refinements, update() method with validation, tag uniqueness enforcement per project. Backend-first solidification.

### v4 (215f325186, 2026-03-13)
Final iteration: 41 files, 1782 insertions. Added the critical permission layer (PlannerCloseTagPermissionService, PlannerCloseTagPermissionType enum, PlannerCloseTagContextBO), 101+ integration test assertions including 403 enforcement. Frontend restored with proper authorization context. Also added 687-line `auth-and-authorization.md` developer doc covering JWT + API token dual auth.

### Key Insight
Without v4's permission layer, the CRITICAL-2 implementation had a **serious authorization gap** — any authenticated employee could modify project close-tags regardless of role. The multi-iteration approach (implement → strip frontend → harden backend → restore with permissions) indicates this was caught during code review.
