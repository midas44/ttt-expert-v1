---
name: qase-access
description: >
  Access the Qase test management system (app.qase.io) to browse test suites, test cases, test runs,
  test results, defects, milestones, and plans in the TIMEREPORT project. Use this skill when the user
  asks to list test cases, view test suites, check test run results, search for test cases, browse
  defects, or mentions "Qase", "test cases", "test suites", "test runs", "test results", "test plan",
  "TIMEREPORT", "QQL", or asks about test coverage, test management, or test repository structure.
  Also use when the user pastes a Qase URL (app.qase.io), references a test case ID, asks to search
  for test cases by keyword, or wants to understand the test suite hierarchy.
---

# Qase Test Management

## Project

| Property | Value |
|----------|-------|
| Project code | `TIMEREPORT` |
| URL | https://app.qase.io/project/TIMEREPORT |
| Access mode | **read-only** |
| MCP server | `qase` (@qase/mcp-server) |

Always pass `TIMEREPORT` as the `code` parameter in all Qase MCP tool calls.

## MCP Tools

All tools are prefixed with `mcp__qase__`. Key read-only tools:

### Suites (test suite hierarchy)

| Tool | Description |
|------|-------------|
| `list_suites` | List all suites (supports `search`, `limit`, `offset`) |
| `get_suite` | Get suite details by ID |

### Test Cases

| Tool | Description |
|------|-------------|
| `list_cases` | List cases with filters (`suite_id`, `search`, `status`, `priority`, `severity`, `automation`, `type`, `behavior`) |
| `get_case` | Get full case details by ID (steps, attachments, custom fields) |

### Test Runs & Results

| Tool | Description |
|------|-------------|
| `list_runs` | List test runs |
| `get_run` | Get run details by ID |
| `list_results` | List test results |
| `get_result` | Get result details by ID |

### Test Plans

| Tool | Description |
|------|-------------|
| `list_plans` | List test plans |
| `get_plan` | Get plan details by ID |

### Defects

| Tool | Description |
|------|-------------|
| `list_defects` | List defects |
| `get_defect` | Get defect details by ID |

### Milestones

| Tool | Description |
|------|-------------|
| `list_milestones` | List milestones |
| `get_milestone` | Get milestone details by ID |

### Other

| Tool | Description |
|------|-------------|
| `list_environments` | List test environments |
| `list_shared_steps` | List reusable test steps |
| `list_shared_parameters` | List reusable test parameters |
| `list_authors` | List authors (team members) |
| `list_custom_fields` | List custom fields |
| `list_system_fields` | List system fields |
| `qql_search` | Advanced search using Qase Query Language |
| `qql_help` | Get QQL syntax help |

## Top-Level Suite Structure

The TIMEREPORT project has 258 suites organized hierarchically. Root suites:

| ID | Suite (Russian) | Translation |
|----|-----------------|-------------|
| 1 | Мои задачи | My Tasks |
| 22 | Задачи сотрудника | Employee Tasks |
| 36 | Отпуска | Vacations |
| 131 | Подтверждение | Confirmation |
| 157 | Планировщик | Planner |
| 182 | Статистика | Statistics |
| 183 | Админка | Admin |
| 207 | Бухгалтерия | Accounting |
| 235 | Нотификации | Notifications |
| 239 | Настройки пользователя | User Settings |
| 244 | Почтовые нотификации | Email Notifications |

## Pagination

The API returns max 100 items per request. For large result sets use `limit` and `offset`:

```
list_suites(code="TIMEREPORT", limit=100, offset=0)    # first 100
list_suites(code="TIMEREPORT", limit=100, offset=100)   # next 100
```

Check `total` and `filtered` in the response to know if more pages exist.

## Finding Test Cases

### By suite

To list cases in a specific suite, use `suite_id`:

```
list_cases(code="TIMEREPORT", suite_id=185, limit=100)
```

### By keyword

Use the `search` parameter:

```
list_cases(code="TIMEREPORT", search="сортировка")
```

### By filters

Combine filters for targeted queries:

```
list_cases(code="TIMEREPORT", priority="high", automation="automated")
```

### QQL (advanced)

Use `qql_search` for complex queries across entities. Call `qql_help` first to get syntax reference.

## Navigating Suite Hierarchy

Suites form a tree via `parent_id`. To find children of a suite:

1. Call `list_suites` and filter by `parent_id` in the response
2. Root suites have `parent_id: null`
3. Each suite has `cases_count` showing direct test case count

## Common Workflows

### Explore a feature area

1. Find the root suite (e.g., id=183 for Админка)
2. List all suites, filter those with matching `parent_id`
3. Drill into sub-suites by repeating with their IDs
4. List cases in leaf suites using `suite_id`

### Get case details with steps

```
get_case(code="TIMEREPORT", id=736)
```

Returns full details: title, description, preconditions, steps, expected results, attachments, custom fields.

### Check test run results

1. `list_runs(code="TIMEREPORT")` to find recent runs
2. `get_run(code="TIMEREPORT", id=<run_id>)` for run details
3. `list_results(code="TIMEREPORT", run_id=<run_id>)` for individual results
