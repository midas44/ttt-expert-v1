---
type: architecture
tags:
  - deployment
  - docker
  - infrastructure
  - ci-cd
  - spring-cloud
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/system-overview]]'
  - '[[rabbitmq-messaging]]'
  - '[[database-performance-analysis]]'
branch: release/2.1
---
# Deployment Architecture

## Architecture Pattern
Spring Cloud microservices with Eureka service discovery + Spring Cloud Gateway, deployed as Docker containers via docker-compose.

## Services (7 Deployable Units)

| Service | Port | App Name | DB Schema | Route |
|---------|------|----------|-----------|-------|
| TTT Backend | 9583 | ttt-backend | ttt_backend | /api/ttt/** |
| Calendar | 9580 | ttt-calendar | ttt_calendar | /api/calendar/** |
| Vacation | 9581 | ttt-vacation | ttt_vacation | /api/vacation/** |
| Email | 9582 | ttt-email | ttt_email | /api/email/** |
| Frontend | 9584 | ttt-frontend | — | /** (catch-all) |
| Discovery | 8761 | ttt-discovery | — | /eureka/* |
| Gateway | 8577 | ttt-gateway | — | (routes all) |

## Infrastructure
- **PostgreSQL 12.2**: Port 5433, single instance, 4 schemas (schema isolation, no sharding)
- **RabbitMQ 3.10.23**: AMQP on 15002, Management on 15003, Prometheus on 15004
- **Nginx**: Optional reverse proxy (HTTP 80, HTTPS 443)

## Build & Containerization
- **Java 17**, **Spring Boot 2.5.6**, **Spring Cloud 2020.0.4**
- **Jib Maven Plugin** (3.2.1) for container builds (no Dockerfile for app services)
- **Custom JRE image**: `jre17-alpine` via jlink (minimal footprint)
- **Registry**: gitlab.noveogroup.com:4567/noveo-internal-tools/ttt-spring

## Environment Deployment Matrix
Docker compose overrides per environment: dev, qa-1, qa-2, timemachine, stage, preprod, prod.
- Docker tag: production uses `{version}`, non-prod uses `{branch}-{version}`

## CI/CD Pipeline (GitLab CI)
Stages: build → merge → pre-release → deploy → deploy-doc → autotest → migrate → restart → pre-release-after-test.
- SchemaSpy for auto-generated DB documentation
- Environment-specific deploy files under `/gitlab/environments/`

## Gateway Routing
All external traffic enters via Gateway (8577), which routes to services via Eureka load balancer (`lb://service-name`). Each route strips `/api` prefix.

## Database Migrations
**Flyway** with out-of-order and ignore-missing-migrations enabled. Baseline version 1.1. Each service manages its own schema migrations.

## Connection Pools
HikariCP per service, max 15-20 connections. Total potential: ~80 connections across 4 DB-connected services.

## Authentication
- **CAS** for browser login (external CAS server)
- **JWT** tokens for API auth (public/private key pairs in each service config)
- **API tokens** per service for inter-service and external tool access

## External Integrations
- **Company Staff**: Sync every 15 min + daily full sync
- **PM Tool**: Sync every 15 min with retry batching
- **SMTP**: Direct on 10.0.5.103:25
- **Feature Flags**: Unleash via GitLab

## Monitoring
- **Spring Boot Actuator**: /health, /info, /metrics, /prometheus
- **Micrometer + Prometheus**: Metrics collection
- **Logback**: Structured logging with Spring Cloud Sleuth tracing
- **RabbitMQ**: Prometheus exporter on port 15004

## File Storage
Vacation service uses local volume mount at `/srv/ttt/uploads/files`. No size limits configured (multipart max: -1).

## Related
- [[architecture/system-overview]] — high-level architecture
- [[rabbitmq-messaging]] — inter-service messaging details
- [[database-performance-analysis]] — PostgreSQL performance findings
- [[EXT-cron-jobs]] — scheduled jobs across services
