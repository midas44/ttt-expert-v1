---
type: exploration
tags:
  - admin
  - projects
  - pm-tool
  - ui-exploration
  - timemachine
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[exploration/ui-flows/admin-panel-pages]]'
  - '[[external/tickets/pm-tool-integration]]'
  - '[[modules/ttt-service]]'
  - '[[architecture/api-surface]]'
branch: release/2.1
---
# Admin Projects Deep Exploration

Comprehensive live testing of Admin Projects page on timemachine (user: perekrest).

## Page Structure
URL: `/admin/projects/all` (All) / `/admin/projects/my` (My)
Access: Admin panel dropdown → Projects

**No create project button** — confirmed PM Tool integration removed this capability.

## All Projects Tab

### Data Scale
- Active projects: ~200 (11 pages × 20 per page)
- With inactive: ~2900+ (147 pages)

### Search & Filtering
- Instant search by "Project name, customer" with scope buttons (Project/Customer)
- **Column filters** (checkbox dropdowns): Supervisor (~55 people), Manager, Type (9 values), Status (7 values)
- **Status defaults**: Active/Unconfirmed/Suspended/Acceptance/Warranty shown; Finished/Cancelled hidden
- **"Show inactive projects"** checkbox toggles Finished+Cancelled visibility

### Project Types (9)
Production, Learning, Administration, Commercial, Idle time, Internal, Investment, Investment without invoicing, Project manager

### Status Values (7)
Active, Finished, Unconfirmed, Suspended, Acceptance, Warranty, Cancelled

### Cell Links
- Supervisor/Manager → CompanyStaff profile (`cs.noveogroup.com/profile/{username}`)
- Name: plain text (not a link) in All Projects

## My Projects Tab
- **Fewer columns**: Name, Manager, Status, Actions (no Customer/Supervisor/Type)
- **Name is a link** (unlike All Projects) but targets `href="#"` — non-functional, likely a PM Tool integration bug
- Shows only projects where current user = Manager
- Tab label shows count: "My projects (N)"

## Action Buttons (3 per row)

### 1. More About Project Dialog
Opens overlay with URL hash `#<projectId>`. All fields **read-only**:

| Field | Notes |
|-------|-------|
| Name | **Links to PM Tool**: `pm.noveogroup.com/projects/{id}/profile/general` |
| Account name | Plain text |
| Customer | Plain text |
| Country | e.g. "France" |
| Supervisor | CS profile link |
| Manager | CS profile link |
| Owner | CS profile link |
| Watchers | List (may be empty) |
| Status | Plain text |
| Type | Plain text |
| Model | e.g. "ODC" |
| Total cost | With "md" unit (e.g. "4759.5 md") |
| First/Last report dates | DD.MM.YYYY format |

**History of changes**: Expandable section showing chronological changes (date, user, field change from→to).

### 2. Edit Tracker Data Dialog
**Only 3 editable fields** (all URL fields with `https://` prefix):
1. Script of synchronization with tracker (pre-filled with default)
2. Link to task tracker (empty, example: gitlab URL)
3. Link to task tracker proxy server (empty, helper link to Google Doc)

### 3. Task Templates Dialog
- Empty state: "No templates" + "Add a template" button
- Template format: project name prefix + " /" + editable suffix
- **"Assign the task to employee"** toggle per template (off by default)
- Templates auto-numbered: "1 task template", "2 task templates"
- CRUD: Add/Delete available; Save/Cancel buttons

## Key Findings
1. **PM Tool link pattern**: `https://pm.noveogroup.com/projects/{pmtId}/profile/general`
2. **My Projects name link bug**: href="#" does nothing — likely incomplete PM Tool integration
3. **Task templates**: Important for report entry — templates define available tasks per project
4. **"Assign to employee" toggle**: Controls whether task requires employee assignment in reports
5. **All project data read-only** — confirms TTT is consumer, PM Tool is source of truth
6. **History of changes**: Full audit trail available in project detail dialog
7. **FINISHED projects**: May hide Task Templates button but keep other actions
