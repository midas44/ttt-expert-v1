---
type: external
tags:
  - tracker
  - integration
  - requirements
  - google-doc
  - jira
  - gitlab
  - redmine
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[exploration/ui-flows/admin-panel-pages]]'
  - '[[external/requirements/google-docs-inventory]]'
  - '[[EXT-tracker-integration]]'
---

# Tracker Integration Specification (Google Doc)

Source: docs.google.com/document/d/1HakoivdHDIc385EGonau8-57FFaP5_n4itkxuAj5cxg

## Supported Trackers (5)
| Tracker | Status | Auth Method | API Pattern |
|---------|--------|-------------|-------------|
| Redmine | Full | API access key | `{host}/issues/{id}.json` |
| Jira | Full | Email+token (Cloud), user+pass (Server) | REST API v2 |
| GitLab | Full | Personal access token | `{host}/{project}/issues/{id}.json` |
| Trello | Partial | UID-based (problematic) | — |
| Asana | Planned | — | — |

## Core Integration Flow (Two-Stage Search)
1. User searches by ticket number/URL → `GET /v1/suggestions/tasks?forReport=true`
   - Returns DB-matched tasks OR discovered ticket URLs
2. User selects result → `GET /v1/tasks?ticketUrl=X&projectName=Y`
   - Server fetches ticket details from tracker

## Authentication Architecture
- Per-user encrypted credentials stored per tracker hostname
- Different auth methods per tracker type
- Credentials stored in `employee_tracker_credentials` table

## Proxy Configuration
- Nginx reverse proxy for VPN-restricted trackers
- 3 failure modes: tracker down, proxy down, tracker inaccessible via proxy
- Proxy URL configured per project in admin

## Custom Scripting System (Server-Side JS)
| Function | Purpose |
|----------|---------|
| `getTaskName()` | Formats ticket data into task display names |
| `getTicketInfo()` | Extracts scheduler/planner information |
| `prepareWorkLogRequest()` | Syncs hours back to Jira |
| `isFinished()` | Determines assignment completion |
| `analyzeAssignmentUpdate()` | Validates remaining work changes |
| `setFormat()` | Applies conditional cell formatting |

Scripts run in **zero-trust sandbox**: no network access, no external function calls.

## Error Handling
- Standard HTTP errors: 401/403/404 from tracker
- 3 custom proxy errors identifying failure point

## Key Design Points
- Tracker credentials are per-user, per-hostname (not per-project)
- Projects configure tracker script + URL + proxy per project
- Work log sync is Jira-specific (`prepareWorkLogRequest`)
- Zero-trust scripting prevents RCE vectors

## Related
- [[modules/ttt-service]] — backend service managing tracker integration
- [[exploration/ui-flows/admin-panel-pages]] — tracker settings in admin
- [[external/requirements/google-docs-inventory]] — source catalog
- [[EXT-tracker-integration]] — Confluence tracker setup docs
