---
type: external
tags:
  - testing
  - automation
  - confluence
  - external-sources
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[EXT-test-plan]]'
  - '[[EXT-vacation-testing-notes]]'
  - '[[EXT-knowledge-transfer]]'
  - '[[external/requirements/google-docs-inventory]]'
---
# Confluence Automation Test Plans

## Two Automation Frameworks

TTT has **two separate** automation test frameworks documented in Confluence, reflecting different eras and approaches.

### 1. API Tests (Confluence page 110298204)
- **Stack**: Python, pytest, requests, cached_property, dataclasses-json, swagger-coverage-py
- **Reports**: Allure
- **Repo**: Inside TTT monorepo at `autotests/` directory on `development-ttt` branch
- **CI**: GitLab CI, runner on 10.0.5.45
- **Auth**: CAS via PhantomJS browser
- **Structure**: 10 test directories: accounting, admin, calendar, data, notifications, planner, report, statistic, utils, vacations
- **Authors**: Anna Chelondaeva, Natalya Tarelkina (until end 2021)
- **Key docs referenced**: TTT test plan (already fetched as [[EXT-test-plan]]), vacation testing notes (already fetched), knowledge transfer doc (already fetched)

### 2. Front-end Grey-box Tests (Confluence page 75923811, v44)
- **Stack**: Java, JUnit5, Gradle, Selenide (UI), REST Assured (API), PostgreSQL (DB), Allure
- **CI**: TeamCity
- **Repo**: Separate GitLab repo `noveo-internal-tools/ttt-automation`
- **Architecture**: Keyword-driven (Tests → Steps → Pages), self-contained tests, dynamic data generation
- **Approach**: Grey-box — combines UI (Selenide), API (REST Assured), and DB (PostgreSQL queries)
- **Browsers**: Chrome, Firefox, Edge on Windows 10+
- **Authors**: Ульянов В.В. (architect/developer)
- **Milestones**: 3-phase plan (basic overnight regression → coverage expansion → advanced diff-based testing)
- **Test data**: Dynamic generation with replay capability (pesticide resistance principle)
- **Locators**: id, name, text, css only — NO xpath (performance + readability)

### Google Docs Referenced (from Confluence page)
| Document | Status | Vault Note |
|----------|--------|------------|
| TTT test plan | Fetched | [[EXT-test-plan]] |
| Vacation testing notes | Fetched | [[EXT-vacation-testing-notes]] |
| Knowledge transfer | Fetched | [[EXT-knowledge-transfer]] |
| Auto tests follow-up (TTT automation sheet) | **Inaccessible** (Google Docs dynamic rendering) | — |
| Testers meeting MoM | **Inaccessible** (401) | — |
| Old automation plan (Test Automation) | **Inaccessible** (Google Docs dynamic rendering) | — |
| Auto test cases spreadsheet | **Inaccessible** (Google Docs dynamic rendering) | — |

### Assessment
- The API test suite (Python) aligns with the existing test plan and is the "current" framework
- The grey-box framework (Java) appears to be an ambitious but potentially stalled initiative — detailed architecture but unclear if fully realized
- 4 Google Docs remain inaccessible via WebFetch due to Google's dynamic rendering; the 3 most important docs from this set were already fetched in prior sessions

## Related
- [[EXT-test-plan]] — pytest test plan (already in vault)
- [[EXT-vacation-testing-notes]] — regression cases
- [[EXT-knowledge-transfer]] — automation gaps
- [[external/requirements/google-docs-inventory]] — full docs inventory
