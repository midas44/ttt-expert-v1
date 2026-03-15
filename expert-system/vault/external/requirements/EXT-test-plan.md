---
type: external
tags: [testing, test-plan, automation, process, google-docs]
created: 2026-03-13
updated: 2026-03-13
status: active
related: ["[[EXT-vacation-testing-notes]]", "[[EXT-knowledge-transfer]]", "[[architecture/roles-permissions]]", "[[modules/statistics-service-implementation]]"]
---

# TTT Test Plan (Google Doc)

Source: docs.google.com/document/d/1HUmYid-2oJHffuehsYs_PwOo-6X0gzfNfknuEglJVFA

Comprehensive testing documentation in Russian. Key sections:

## 1. General Info
- Test envs: timemachine, dev-new, qa-1, qa-2, stage
- Test data from cs_dev_users, role management via CS sync (10 min)
- Bug workflow: template with labels (To Do, Low, High), assignees by area

## 2. Automated Tests (API)
- **Stack**: Python + pytest + requests (chosen over Postman)
- **Envs**: ttt-dev-new, ttt-preprod; CI via tox; 1h GitLab timeout
- **Reports**: pytest-html + swagger-coverage (3 reports: TTT, Calendar, Vacation)
- **Sections covered**: My Tasks, Approvals, Vacation, Statistics, Admin, Accounting, Planner, Notifications, User Profile, Suggestions, General
- **Roles tested**: EMPLOYEE, CONTRACTOR, PROJECT_MANAGER, DEPARTMENT_MANAGER, TECH_LEAD, ADMIN, CHIEF_ACCOUNTANT, VIEW_ALL, office roles, project roles
- **Priority**: Based on API call frequency statistics
- **Conventions**: Detailed coding standards, parametrization by roles, xfail for known bugs

## 3. Manual Tests
- Only ticket-based testing (no regression due to resource constraints)
- Test documentation in Qase (free tier)
- Browser support: Chrome, Mozilla, Edge, Safari at 1920px
- Team: Anna and Ivan handle manual testing

## Key Insights for Test Generation
- Automated tests exist for API layer but gaps in Admin, Accounting, Planner sections
- Manual regression not performed systematically — high value in comprehensive test cases
- Role parametrization is critical — each endpoint tested across all applicable roles
- swagger-coverage reports show API coverage gaps
- Priority based on real usage statistics (API call frequency)
