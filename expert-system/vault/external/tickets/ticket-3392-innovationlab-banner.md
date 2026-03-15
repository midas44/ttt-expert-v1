---
type: external
tags:
  - ticket
  - frontend
  - banner
  - innovation-lab
  - hotfix
  - sprint-14
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[frontend-architecture]]'
  - '[[external/tickets/sprint-14-15-overview]]'
branch: release/2.1
---
# Ticket #3392 — InnovationLab Banner Feature

## Overview
Promotional banner for internal Innovation Lab program, displayed to users. **Hotfixed to stage** (Sprint 14 hotfix). Frontend-only — no backend/DB changes.

**Status**: Closed | **Assignee**: omaksimova (QA) | **Dev**: ishumchenko
**Merged**: 4 MRs (!5273, !5277, !5272 hotfix to master, !5285 back-merge to release/2.1)

## Banner Behavior
Custom web component `<innovation-banner>` from external InnovationLab team, compiled and checked into repo.

### Three Visual States
1. **Collapsed** (default on TTT) — narrow strip (68x372px), logo + cat + slider button, fixed top-right
2. **Expanded** — full card (300px wide), logo, title, description, "Participate" button, close icon
3. **Choice** — shown on close: "Collapse", "Remind Later", "Don't Show Again"

### User Actions
| Action | Effect |
|--------|--------|
| "Participate" | Opens landing page (RU/EN), hides 3 months |
| "Remind Later" | Hides 3 months |
| "Don't Show Again" | Permanent hide (`neverShow` flag) |
| "Collapse" | Switches to collapsed state |
| Slider button | Expands banner |

### State Persistence
- **localStorage** key: `innovation-banner-data-{userId}` (companyStaffId)
- Stores: current state, next show date, never-show flag

## Key Technical Finding — CRITICAL
**Hardcoded role bypass**: AppContainer passes `role: 'Production'` to banner regardless of actual user position type. The banner's internal `shouldShowBanner()` checks `role !== "Production"` to filter, but since TTT always passes `'Production'`, **every user sees the banner**, not just Production-type employees.

This is either intentional (show to all TTT users) or a bug (should check user's actual position type from CompanyStaff data).

## Code Changes (6 files)
1. `config-overrides.js` — webpack alias for innovation-banner
2. `public/innovation-banner/innovation-banner.es.js` (1531 lines, compiled) — full component
3. `public/innovation-banner/style.css` (minified) — all styles + animations
4. `public/innovation-banner/style-overrides.css` (37 lines) — TTT brand colors (#428bca)
5. `src/app/containers/AppContainer/index.js` — integration point, useEffect init
6. `src/index.css` — formatting changes only

## TTT-Specific Deviations
- Initial state is **collapsed** (not expanded) to avoid blocking "Add Task" button
- Light theme only (dark theme not supported)
- Language follows TTT's language setting, not cross-system CS setting
- Banner JS is a compiled artifact — updates require manual rebuild from InnovationLab source

## Test Implications
- Verify banner appears/collapses for different user roles
- Test localStorage persistence across sessions
- Test "Remind Later" / "Don't Show Again" timer behavior
- Test language switching (RU/EN) while banner is visible
- Verify banner doesn't obscure UI elements (especially "Add Task" button)
- **Investigate**: should banner show for non-Production position types?

## Connections
- [[frontend-app]] — integration point
- [[frontend-architecture]] — compilation/build pipeline
- [[external/tickets/sprint-14-15-overview]] — Sprint 14 hotfix context


## Cross-Branch Analysis (Session 26)

**Banner is present and identical on both release/2.1 and stage.**

All three innovation-banner files have identical hashes across branches:
- `innovation-banner.es.js`: `cad6376ec7dde65f5a79ca42e45bbb7919b45f71`
- `style-overrides.css`: `926dc95722b35ef9574e37363c1d7c2597275aa5`
- `style.css`: `66df3a044111efcf8f18536907a5a69160943df2`

### Minor Differences
- **stage**: Has console.log debug statements (`'Banner initialized'`, `'Banner not shown'`)
- **release/2.1**: Debug logs removed (cleaner code)

Both branches call `banner?.collapse()` after initialization. Feature is fully functional on release/2.1.
