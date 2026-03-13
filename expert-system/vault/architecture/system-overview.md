---
type: architecture
tags:
  - architecture
  - overview
  - microservices
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[ttt-service]]'
  - '[[vacation-service]]'
  - '[[calendar-service]]'
  - '[[email-service]]'
  - '[[frontend-app]]'
branch: release/2.1
---
# System Overview

TTT (Time Tracking Tool) is a microservices-based web application for corporate time tracking, absence management, and related administrative functions.

## Architecture Pattern
Microservices with API Gateway and Service Discovery (Spring Cloud).

## Deployable Services
1. **[[ttt-service]]** — Core time tracking: task reports, employee management, tracker integrations, notifications, sync with external systems (Company Staff)
2. **[[vacation-service]]** — Absence management: vacations, days-off, sick leaves, approvals, vacation day calculations
3. **[[calendar-service]]** — Production calendars, salary offices, working/non-working day management
4. **[[email-service]]** — Email notification delivery, template rendering
5. **[[gateway]]** — Spring Cloud Gateway for API routing
6. **[[discovery]]** — Eureka service discovery
7. **[[frontend-app]]** — React SPA served via Spring Boot wrapper

## Inter-Service Communication
Services communicate via REST (Feign clients) through the gateway. Service discovery via Eureka.

## Tech Stack
- **Backend**: Java 17, Spring Boot 2.5.6, Spring Cloud 2020.0.4
- **Frontend**: React 18.2, TypeScript/JavaScript, Redux Toolkit, Redux Saga
- **Database**: PostgreSQL 12.2 (shared DB `ttt`, likely schema-per-service)
- **Persistence**: JPA/Hibernate, QueryDSL, JOOQ, Flyway migrations
- **Auth**: JWT (jjwt 0.11.2)
- **Real-time**: WebSocket (STOMP + SockJS)
- **Feature Flags**: Unleash
- **Build**: Maven (backend), Create React App (frontend)
- **CI/CD**: GitLab CI, Docker (Jib), 9 environment configs
- **Quality**: Checkstyle, PMD, SpotBugs, JaCoCo, ESLint, Prettier

## External Integrations
- **Company Staff (CS)**: Employee and salary office data sync
- **Trackers (8)**: JIRA, GitLab, Asana, ClickUp, Redmine, YouTrack, Presales, generic API
- **Email**: SMTP for notifications

## Code Scale
~5,500 code files: 3,089 Java, 1,270 JS/JSX, 670 TS/TSX, 368 SQL, 89 Maven POMs.
205 Java test files, 28 frontend test files, plus Cypress/Cucumber E2E suite (11 modules).

## Related
- [[frontend-architecture]]
- [[backend-architecture]]
- [[database-schema]]
- [[api-surface]]
