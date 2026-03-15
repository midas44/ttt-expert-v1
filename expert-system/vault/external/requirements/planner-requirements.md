---
type: external
tags:
  - planner
  - requirements
  - assignments
  - drag-and-drop
  - project-settings
  - confluence
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/frontend-planner-module]]'
  - '[[modules/ttt-service]]'
  - '[[investigations/planner-dnd-bugs-analysis]]'
branch: release/2.1
---
# Planner Requirements

Confluence page ID 130386435. Detailed functional spec (RU), version 8. Linked Figma: node 40576-520558. Linked tickets: #3375, #2724, #3258, #2319.

## Core Concepts

### Assignment Types
- **Generated**: Created when task added manually in Planner OR when task from "My Tasks" is opened for editing. Persists indefinitely until manually removed.
- **Non-generated**: Appears for tasks reported via "My Tasks" on report date only. Auto-disappears next day unless new reports exist.

## Task Ordering Rules (Sections 5, 8)
- Projects sorted alphabetically (A-Z, А-Я)
- New task added via Planner appears at **TOP** of list within its project
- Generate endpoint called with `projectId` parameter
- Before editing: non-generated assignments shown ABOVE generated within project
- On "Open for editing": order must NOT change (**known bug**: "everything jumps")
- Generated assignments support drag-and-drop reordering; order is persisted
- New task highlighted with green banner for 5 seconds
- Auto-scroll to newly added task if off-screen

## Projects Tab (Section 6)
- Employee ordering within project matches Project Settings popup order (#2724)
- Task ordering per employee matches Planner > Tasks tab for that project
- Comment field icon tooltip: "Project settings" (changed from "Add/remove employees")

## Project Settings Popup (Section 7)
Renamed from "Employees on Project" to "Project Settings". Two tabs:

### Project Members Tab (7.3)
- Employee dropdown (required, error on empty)
- "Role on project" field (optional, placeholder "Add role")
- "+" button → adds to table at bottom, green highlight, auto-scroll
- Drag-and-drop reordering when 2+ rows
- Inline role editing on hover
- Delete with "Delete" tooltip
- **Immediate save** with "Changes saved" notification inside popup

### Tasks Closing Tab (7.4)
- "Tag for closing tasks" input (required, 200 char max)
- Same UX as Project Members (add, reorder, inline edit, delete, immediate save)
- **Backend rule**: During assignment generation, assignments containing listed tags get `closed=true` → shown ONLY if they have reported hours on selected date

### OK Button (7.5)
Closes popup. Future change planned (#2319): non-instant save with Cancel/Save.

## UI Standards (Section 9, #3258)
- Side padding: 16px
- Font: 13 for text, 13 semibold for headers
- Left alignment except column 5 (date/hours)

## External References
- Old tech spec: Google Doc `1tJiSoUIVEYXj0LB1-dOf_1CmcAiVhjfbxk0y615YGRQ`
- Tracker integration spec: Google Doc `1HakoivdHDIc385EGonau8-57FFaP5_n4itkxuAj5cxg`
- New Figma mockups: node 40576-520558
