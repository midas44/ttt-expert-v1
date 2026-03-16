---
type: investigation
tags:
  - banner
  - innovationlab
  - frontend
  - sprint-14
  - hotfix
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[modules/admin-panel-deep-dive]]'
  - '[[architecture/frontend-architecture]]'
---
# InnovationLab Banner Integration (#3392)

## Overview

Hotfix Sprint 14 feature: integrate InnovationLab promotional banner into TTT as a compiled external component. Frontend-only change (no backend). Deployed via hotfix to master (MR !5272) on 2026-03-02, also merged to release/2.1 (MRs !5273, !5277).

**Status:** Closed, deployed to production. QA verified.

## Architecture

### Component Integration
- Banner is a **compiled ES module** (`innovation-banner.es.js`) stored as a static asset in `frontend/frontend-js/public/innovation-banner/`
- Webpack alias in `config-overrides.js` maps `'innovation-banner'` → `./public/innovation-banner/`
- Loaded in `AppContainer/index.js` (the root container for authenticated pages)
- NOT a React component — uses custom element `<innovation-banner>` initialized via `InnovationBanner.init()`

### Initialization Code (AppContainer)
```js
useEffect(() => {
    if (applicationReady && currentUser) {
      const banner = InnovationBanner.init({
        userId: currentUser.companyStaffId,
        role: 'Production',
        language: currentLanguage.toLocaleLowerCase(),
        theme: 'light',
        onParticipate: () => {
          console.log('User decided to participate');
        },
      });
      if (banner) {
        banner?.collapse();
      }
    }
  }, [applicationReady, currentUser, currentLanguage]);
```

### Key Implementation Details
- **userId**: `currentUser.companyStaffId` — used for per-user state persistence
- **role**: Hardcoded `'Production'` — **ALL users see the banner** regardless of actual position type. The requirement says "show to Production position type users only" but the code bypasses this check by always passing 'Production'. This is likely intentional TTT simplification (position type data may not be available in TTT frontend).
- **language**: From `LocalStorageService.getItem('language')`, lowercased — follows TTT's language setting, not CS
- **theme**: Hardcoded `'light'` — TTT only supports light theme
- **onParticipate**: No-op callback (only console.log)
- **Initial state**: Always collapsed — `banner.collapse()` called immediately after init

### State Persistence
The banner library internally manages state persistence (likely via localStorage keyed by userId). The TTT-specific behavior:
- Does NOT remember expanded state across sessions
- Only persists: "Participate" (hidden 3 months), "Remind later" (hidden 3 months), "Never show again" (permanent)
- On every login/page refresh, banner re-initializes in collapsed state

## Banner States

### Three States
1. **Expanded**: Logo, title, text, "Participate" button, "Close" icon
2. **Collapsed**: Logo, cat illustration, slider icon. Initial state on TTT.
3. **Choice**: "Collapse", "Remind later", "Never show again" buttons

### State Transitions
```
[Login/Init] → Collapsed
Collapsed + Click slider → Expanded
Expanded + Click Close → Choice
Choice + Click "Collapse" → Collapsed
Choice + Click "Remind later" → Hidden (3 calendar months, then → Expanded)
Choice + Click "Never show again" → Hidden (permanent)
Expanded + Click "Participate" → Hidden (3 months, then → Expanded) + opens landing page
```

### "Participate" Button Behavior
- Opens InnovationLab landing in new tab
- URL depends on language: `https://innovationlab.noveogroup.com/ru/` or `/en/`
- Hides banner for 3 calendar months
- After 3 months, re-shows in expanded state

## CSS Overrides (`style-overrides.css`)
- Background forced to white (`#fff`)
- All interactive buttons: `background-color: #428bca` (Bootstrap blue)
- "Never show" button: blue border, no background fill
- Slider button: `::before` pseudo-element creates 68×372px transparent hit area (entire collapsed banner clickable)
- Font-weight 400 for buttons

## Requirements Summary (28 items)

### Core (1-16)
1. Show to "Production" position type users on first login (after release)
2. Show on all pages
3. Fixed position, top-right under header
4. Stays during scroll
5-6. Three states (expanded/collapsed/choice), first login = expanded (TTT override: collapsed)
7. Expanded shows: logo, title, text, "Participate", "Close"
8. "Participate" → opens landing (new tab), hides 3 months, re-shows expanded
9. "Close" → shows choice state
10. Choice shows: "Collapse", "Remind later", "Never show again"
11. "Collapse" → collapsed state
12. "Remind later" → hidden 3 months, re-shows expanded
13. "Never show again" → permanent hide
14. Collapsed shows: logo, cat, slider icon
15. Slider click → expanded state
16. State persistence across navigation/re-login

### TTT-Specific Overrides
- Initial state = collapsed (not expanded as in base spec)
- Light theme only
- Language follows TTT setting (not CS)
- Landing URL language-dependent (ru/en)
- "Participate" URL: `https://innovationlab.noveogroup.com/{lang}/`

### Nice-to-Have (23-28)
- Mobile FAB ("AI") for collapsed state — not formally supported on TTT

## Potential Test Issues

1. **Role bypass**: Code hardcodes `role: 'Production'` — banner shows to ALL users (employees, contractors, admins, accountants). The requirement says "Production position type only". Possible bug or intentional.
2. **State re-init**: Banner re-collapses on every page refresh due to `banner.collapse()` call — expanded state is NOT persistent across navigation.
3. **Language change**: `useEffect` depends on `currentLanguage` — banner should reinitialize when language is switched mid-session.
4. **Compiled component**: Updates to InnovationLab require manual rebuild and upload — potential version drift.
5. **CSS specificity**: Style overrides may conflict with future InnovationLab updates.
6. **3-month timer**: Calendar months, not 90 days — edge cases around month boundaries.

## Related
- [[modules/admin-panel-deep-dive]] (general frontend architecture)
- [[architecture/frontend-architecture]] (AppContainer)
- MRs: !5272 (hotfix to master), !5273, !5277 (to release/2.1)
- Figma: Multiple nodes linked in issue description
