---
type: architecture
tags:
  - frontend
  - quality
  - dead-code
  - duplication
  - circular-deps
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/frontend-approve-module]]'
  - '[[modules/frontend-planner-module]]'
  - '[[modules/frontend-vacation-module]]'
branch: release/2.1
---
# Frontend Structural Quality

Analysis of frontend codebase structural health using static analysis tools (madge, ts-prune, jscpd).

## Codebase Statistics
- **Total files**: 1,924 source files (670 TS/TSX + 1,254 JS/JSX)
- **Lines of code**: 137,424 total; 57,995 analyzed by jscpd
- **JS/TS split**: 65% JavaScript, 35% TypeScript — migration incomplete
- **Modules**: 10 application modules + common

## Circular Dependencies: 2 Chains (LOW severity)
Both confined to planner module type definitions:

1. `modules/planner/ducks/types.ts` ↔ `modules/planner/ducks/focus/types.ts`
2. `modules/planner/ducks/locks/types.ts` ↔ `modules/planner/ducks/types.ts`

Root cause: Redux duck anti-pattern where root types barrel re-exports sub-duck types while sub-ducks reference root state types. Not systemic.

## Unused Exports (Dead Code): 488 Exports (POOR)
Out of 662 ts-prune results, 488 are genuinely unused.

### Top Offenders
| Unused | Location | Pattern |
|--------|----------|---------|
| 126 | modules/approve/ducks | Redux selectors/actions never consumed |
| 31 | modules/vacation/ducks | Over-engineered state |
| 26 | common/components/tables | Speculative types |
| 20 | modules/statistics/ducks | Abandoned features |
| 19 | common/components/inputs | Unused component props |
| 17 | modules/vacation/components | Orphaned exports |
| 14 | modules/planner/ducks | Dead Redux slice code |
| 13 | modules/admin/context | Context values never read |
| 11 | modules/report/ducks | Unused selectors |

### Notable Patterns
- **modules/approve** accounts for 26% of all dead code (126/488)
- Debug hooks left in production: `useCallbackDebugger`, `useEffectDebugger`, `useHookStateLog`
- Module default exports flagged (false positives from dynamic imports/React.lazy)
- Type barrel files with speculative exports never consumed

## Code Duplication: 1.74% (ACCEPTABLE)

| Format | Files | Lines | Clones | Dup Lines | % |
|--------|-------|-------|--------|-----------|---|
| TypeScript | 415 | 34,796 | 38 | 502 | 1.44% |
| TSX | 220 | 19,277 | 30 | 506 | 2.62% |
| JavaScript | 183 | 3,922 | 0 | 0 | 0% |
| **Total** | **818** | **57,995** | **68** | **1,008** | **1.74%** |

### Top Modules by Clone Count
| Clones | Location | Pattern |
|--------|----------|---------|
| 33 | modules/planner/ducks | Redux boilerplate |
| 19 | modules/vacation/ducks | Saga patterns |
| 14 | modules/vacation/components | UI duplication |
| 14 | modules/approve/ducks | Action patterns |
| 12 | modules/vacation/containers | Container duplication |
| 8 | common/ducks/productionCalendar | Copy-paste sagas (4 near-identical functions) |

## Combined Risk Assessment
1. **modules/approve** — 126 dead exports + 14 clones → highest cleanup priority
2. **modules/planner** — 2 circular deps + 27 dead exports + 33 clones → most structurally complex
3. **modules/vacation** — 59 dead exports + 45 clones → largest but manageable
4. **common/ducks/productionCalendar** — 8 internal clones from copy-paste saga patterns

## Related
- [[modules/frontend-report-module]] — report module (11 unused exports, 8 clones)
- [[modules/frontend-approve-module]] — approve module (worst dead code: 126 exports)
- [[modules/frontend-planner-module]] — planner module (circular deps + highest clones)
- [[modules/frontend-vacation-module]] — vacation module (second most problematic)
- [[patterns/frontend-cross-module-patterns]] — shared patterns
