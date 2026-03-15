---
type: external
tags:
  - planner
  - requirements
  - confluence
  - assignments
  - tasks
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[modules/frontend-app]]'
branch: release/2.1
---
# Planner Requirements (Планировщик)

Confluence page 130386435, version 8 (actively maintained). Tickets: #3375, #2724, #3258, #2319.

## Core Concepts

**Assignments (Ассайнменты)** — two types:
- **Generated** (сгенерированные): Created manually in Planner OR reported via "My Tasks" then opened for edit in Planner. Persists indefinitely.
- **Non-generated** (несгенерированные): Appears for task reported via "My Tasks" on selected date. Auto-disappears next day if no new reports.

## Task Ordering
- Projects sorted alphabetically (A-Z, then Cyrillic А-Я)
- Non-generated above generated within project (before editing)
- Generated assignments: drag-and-drop reorderable, order persists across days
- New task highlighted green 5s, auto-scroll if off-screen
- Opening for edit must NOT reorder (known jumping bug exists)

## Tabs
- **Tasks tab:** Calls `generate` with `projectId` (previously had cross-project sorting — now removed)
- **Projects tab:** Employee order matches "Project Settings" popup (#2724/#3375). Task order matches Tasks tab order per project.

## Project Settings Popup (formerly "Employees on project")
Renamed to "Настройки проекта" / "Project settings". Two tabs:
- **Project Members** (7.3): Employee dropdown (required), role field (optional), immediate add/delete with notification, drag-and-drop reorder
- **Tasks Closing** (7.4, NEW): Tag-based closing. Tags max 200 chars. During generation, tagged assignments treated as `closed=true` — shown only if they have reported hours

**Flags:** Points 8.3-8.4 explicitly ask to "verify" behaviors. Old cross-project sorting code may cause regression.

Links: [[modules/ttt-service]], [[modules/frontend-app]], [[architecture/frontend-architecture]]
Figma: node 40576-520558. Google Docs: old spec by V. Bryzgalov, tracker integration spec.
