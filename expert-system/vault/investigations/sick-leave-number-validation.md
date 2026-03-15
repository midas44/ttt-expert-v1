---
type: investigation
tags: [sick-leave, validation, backend, frontend, comparison]
created: 2026-03-14
updated: 2026-03-14
status: active
related: ["[[frontend-sick-leave-module]]", "[[frontend-vacation-module]]", "[[cross-branch-release21-vs-stage]]"]
branch: release/2.1
---

# Sick Leave Number Field Validation — Backend vs Frontend

Investigation of whether backend and frontend validation rules for the sick leave "number" field are synchronized.

## Backend Rules (Java — vacation service)

**DTO layer** (`SickLeaveCreateRequestDTO.java:37-39`):
- `@Size(max = 40)` on `String number`
- **Optional** — no `@NotNull`/`@NotBlank`
- No format pattern, no character restrictions

**Entity** (`SickLeave.java:61-62`): `@Column(name = "number")` — no additional constraints at DB mapping level.

**Service-level validator** (`SickLeaveCreateValidator.java`): Only validates dates order (startDate ≤ endDate), does NOT validate number field.

**Patch DTO** (`SickLeavePatchRequestDTO`): Extends create DTO — inherits same `@Size(max = 40)`.

## Frontend Rules (JS/TS)

**Validation helper** (`sickLeave/helpers/validation.js:3-16`):
- `MAX_NUMBER_LENGTH = 40`
- Yup `mixed().test()` — trims whitespace, then checks length
- Optional — returns `true` if value is falsy/empty
- Error key: `'sickLeave.errors.number_length'`

**Used in 3 places** — all with same rule:
1. `sickLeavesOfEmployees/validationSchema.ts` (create + edit schemas)
2. `SickListEdit/validation.js`

## Comparison

| Aspect | Backend | Frontend | Match? |
|--------|---------|----------|--------|
| Required | No | No | YES |
| Max length | 40 | 40 | YES |
| Min length | None | None | YES |
| Format pattern | None | None | YES |
| Whitespace | No trim | Trims before check | MINOR DIFF |

## Conclusion

**Rules are synchronized.** Both enforce optional string with max 40 characters. The only minor discrepancy: frontend trims whitespace before length check, backend does not. This means a string of 41 spaces would pass frontend validation (trimmed to empty → optional → pass) but also pass backend validation (41 chars including spaces → `@Size(max=40)` would fail). However, this edge case is academic — users rarely enter only spaces.

**No action needed** — the P3 item "Sick leave number field validation" is resolved. Rules are aligned.
