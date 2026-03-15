---
type: investigation
tags:
  - testing
  - backend
  - quality
  - coverage
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[frontend-test-suite-analysis]]'
  - '[[architecture/frontend-structural-quality]]'
branch: release/2.1
---
# Backend Test Suite Analysis

## Summary
150 test files covering 2,839 source files — **5.3% test-to-source ratio**. Modern stack (JUnit 5, Mockito 4, Cucumber 7, TestContainers) but critically low coverage across all services.

## Framework Stack
- **JUnit 5** (5.9.2) — primary test runner
- **Mockito** (4.4.0) — mocking
- **AssertJ** (3.27.6) — fluent assertions
- **Spring Boot Test** — MockMvc, TestRestTemplate
- **TestContainers** (1.17.2) — PostgreSQL 12.6 + RabbitMQ 3.8.0 Docker containers
- **Cucumber** (7.15.0) — BDD/Gherkin features (4 feature files, 5 step definition classes)
- **WireMock** (3.3.1) — HTTP mocking for CS/PM Tool APIs
- **Awaitility** (4.2.0) — async testing

## Coverage by Service

| Service | Test Files | Source Files | Ratio | Test Methods |
|---------|-----------|-------------|-------|-------------|
| TTT Backend | 71 | 1,473 | 4.8% | ~250+ |
| Vacation | 65 | 973 | 6.7% | ~170+ |
| Calendar | 6 | 192 | 3.1% | ~30+ |
| Email | 1 | 100 | 1.0% | 3 |
| Common | 7 | 168 | 4.2% | ~20+ |

## Test Types
- **Unit** (71%): Mockito-based, no Spring context — fast
- **Integration** (27%): @SpringBootTest + TestContainers — full stack
- **BDD** (2%): Cucumber features for statistic reports + vacation creation

## Test Infrastructure
- TestContainers initializers in 3 services (ttt, vacation, calendar)
- 32 SQL fixture files (14 setup + 18 cleanup)
- 9 JSON fixtures for external API mocking (CS, PM Tool)
- JaCoCo configured — excludes conf, dto, bo, entity, model, event, jooq packages

## Critical Gaps
1. **Email service**: 1 test file, 3 methods — 99% untested (templates, batch, scheduler)
2. **Calendar service**: 3.1% — business logic, period calculations untested
3. **Infrastructure**: RabbitMQ config, Unleash, metric config — all untested
4. **~1,500 untested business classes** in TTT service alone
5. No mutation testing (no pit-maven-plugin)
6. No end-to-end workflow tests (report → approval → accounting)

## Cucumber BDD Coverage
- `statistic_report_submit_comment.feature` (2 scenarios)
- `statistic_report_get_employees.feature`
- `statistic_report_get_projects.feature`
- `vacation.feature` (vacation creation/approval)

## Observations
- Tests exist primarily for newer features (statistics, vacation BDD)
- Legacy core (reports, planner, tasks) has minimal direct test coverage
- Good test data management pattern (SQL fixtures + cleanup scripts)
- No base test class — each test duplicates setup

Related: [[frontend-test-suite-analysis]], [[architecture/frontend-structural-quality]], [[vacation-service-implementation]], [[ttt-report-service]]
