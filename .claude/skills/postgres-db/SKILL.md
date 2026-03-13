---
name: postgres-db
description: >
  Query and explore the TTT PostgreSQL database across all configured environments
  (qa-1, timemachine, stage) using postgres MCP servers (crystaldba/postgres-mcp).
  Use this skill when the user asks to query the database, list tables or schemas,
  inspect table structure, run SQL, check DB health, analyze query performance, or
  mentions "database", "postgres", "SQL", "tables", "schema", "query", "select",
  "employees in DB", "ttt_backend", "ttt_vacation", "ttt_calendar", "ttt_email",
  or asks about data that lives in the database rather than the API. Also use when
  the user wants to understand the data model, find column names, check indexes,
  or troubleshoot slow queries. If the user mentions both "database" and "API",
  use this skill for the database parts.
---

# TTT PostgreSQL Database — Multi-Environment

## Environments & MCP Servers

Each environment has its own MCP server. The naming convention is `postgres-<short>`:

| Environment | Short | MCP Server | DB Host | Tool Prefix |
|-------------|-------|------------|---------|-------------|
| qa-1 | qa1 | `postgres-qa1` | `10.0.4.220:5433` | `mcp__postgres-qa1__` |
| timemachine | tm | `postgres-tm` | `10.0.6.53:5433` | `mcp__postgres-tm__` |
| stage | stage | `postgres-stage` | `10.0.4.241:5433` | `mcp__postgres-stage__` |

All servers connect to database `ttt`, user `ttt`, access mode **restricted** (read-only).

### Choosing the Right Server

1. If the user specifies an environment, use its server
2. If no environment is specified, read `expert-system/config.yaml`:
   - `testing_dev_envs.primary` → default for development/testing queries
   - `testing_dev_envs.secondary` → fallback
   - `testing_prod_envs.primary` → for prod-like data comparison
3. For cross-environment comparison, query multiple servers

### Tool Names by Environment

To call a tool, use the full prefixed name:

```
mcp__postgres-qa1__execute_sql      — query qa-1
mcp__postgres-tm__execute_sql       — query timemachine
mcp__postgres-stage__execute_sql    — query stage
```

Same pattern for all tools: `list_schemas`, `list_objects`, `get_object_details`,
`execute_sql`, `explain_query`, `analyze_query_indexes`, `analyze_workload_indexes`,
`analyze_db_health`, `get_top_queries`.

## Auto-Configuration

If environments change in `expert-system/config.yaml`, run the sync script:

```bash
node .claude/scripts/sync-postgres-mcp.js --apply
```

This script:
1. Reads env names from `expert-system/config.yaml` (all `testing_dev_envs` and `testing_prod_envs`)
2. Reads DB connection details from `config/ttt/envs/<name>.yml`
3. Updates `.claude/.mcp.json` with `postgres-<short>` entries
4. Removes stale postgres entries no longer in config

After running, restart Claude Code for new MCP servers to load.

**Dry-run** (preview without writing):

```bash
node .claude/scripts/sync-postgres-mcp.js
```

### Name Mapping

| Env Name | Short Name |
|----------|------------|
| timemachine | tm |
| qa-1 | qa1 |
| qa-2 | qa2 |
| stage | stage |
| dev-new | devnew |
| preprod | preprod |

## Schemas

There are 4 user schemas (same across all environments):

| Schema | Tables | Purpose |
|--------|--------|---------|
| **ttt_backend** | ~40 | Main time-tracking app — employees, projects, tasks, reports, offices |
| **ttt_vacation** | ~32 | Vacation/dayoff/sick leave management |
| **ttt_calendar** | 8 | Office calendars and working days |
| **ttt_email** | 6 | Email templates and outgoing mail |

Note: `stage` may have fewer tables (~82 vs ~86) due to being on a different release branch.

## Key Workflow: Always Check Columns First

Column names in TTT tables often differ from what you'd guess. Before writing any query, use `get_object_details` to verify actual column names.

Common surprises:
- English name is `latin_first_name` + `latin_last_name`, not `english_name` or `name_en`
- Employee start date lives in `ttt_vacation.employee.first_date`, not in `ttt_backend.employee` (which has no start date column)
- `ttt_backend.employee_work_period` exists but may be empty in QA environments
- The `name` column in `ttt_backend.employee` contains the display name (often Russian), not the English name

**Correct pattern:**

1. Use `get_object_details` to check the table structure
2. Identify the actual column names
3. Write the query using those exact names

## Always Use Schema-Qualified Names

Tables with the same name exist across schemas (e.g., `employee` in both `ttt_backend` and `ttt_vacation`). Always qualify:

```sql
-- Correct
SELECT * FROM ttt_backend.employee WHERE login = 'jdoe'

-- Wrong — ambiguous
SELECT * FROM employee WHERE login = 'jdoe'
```

## Schema Overview

### ttt_backend (main app)

Key tables:

| Table | Description |
|-------|-------------|
| `employee` | All employees — login, names, email, office, roles, department |
| `project` | Projects tracked in TTT |
| `project_member` | Employee-project assignments |
| `task` | Tasks within projects |
| `task_report` | Time reports submitted by employees |
| `task_assignment` | Task assignments to employees |
| `office` | Office locations |
| `office_managers` / `office_hrs` / `office_accountants` | Office role assignments |
| `statistic_report` | Cached statistics for reporting |
| `reject` / `rejected_week` | Report rejection tracking |
| `employee_global_roles` | Global roles (admin, manager, etc.) |
| `employee_managers` | Manager-employee relationships |
| `token` / `token_permissions` | API tokens |
| `schema_version` | Flyway migration history |

### ttt_vacation

Key tables:

| Table | Description |
|-------|-------------|
| `employee` | Employee data with `first_date` (start) and `last_date` (end) |
| `vacation` | Vacation records |
| `vacation_approval` | Approval workflow for vacations |
| `employee_dayoff` / `employee_dayoff_request` / `employee_dayoff_approval` | Day-off management |
| `sick_leave` | Sick leave records |
| `employee_period` | Employment periods |
| `office_annual_leave` | Annual leave allowances per office |

### ttt_calendar

| Table | Description |
|-------|-------------|
| `calendar` | Calendar definitions |
| `calendar_days` | Individual day entries (working/holiday) |
| `office` / `office_calendar` | Office-calendar mappings |

### ttt_email

| Table | Description |
|-------|-------------|
| `email` | Outgoing email queue |
| `email_template` | Email templates |
| `email_signature` | Email signatures |
| `attachment` | Email attachments |

## Cross-Schema Lookups

Employee data is split across schemas. To get a full picture, you sometimes need to join or query multiple schemas:

- **Names and login**: `ttt_backend.employee` (canonical source)
- **Start/end dates**: `ttt_vacation.employee` (`first_date`, `last_date`)
- **Office info**: both schemas have `office` tables, linked by ID
- **Vacations/sick leave**: `ttt_vacation` schema only

Example — employees who started in 2026 with English names:

```sql
SELECT e.login,
       e.latin_first_name || ' ' || e.latin_last_name AS english_name,
       e.first_date
FROM ttt_vacation.employee e
WHERE e.first_date >= '2026-01-01' AND e.first_date < '2027-01-01'
ORDER BY e.first_date
```

## Exploration Workflow

When exploring an unfamiliar part of the schema:

1. `list_schemas` — see all schemas
2. `list_objects(schema_name=...)` — see tables in a schema
3. `get_object_details(schema_name=..., object_name=...)` — see columns, types, constraints, indexes
4. `execute_sql` — run queries

## Performance & Health

- Use `explain_query` to understand how a query will execute before running expensive queries
- Use `analyze_db_health` to check for index bloat, connection issues, vacuum health, etc.
- Use `get_top_queries` to find slow queries (requires `pg_stat_statements` extension)
- Use `analyze_query_indexes` to get index recommendations for specific queries
