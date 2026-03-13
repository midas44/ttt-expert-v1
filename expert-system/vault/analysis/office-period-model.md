---
type: analysis
tags:
  - accounting
  - offices
  - periods
  - salary
  - priority-3
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[database-schema]]'
  - '[[roles-permissions]]'
branch: release/2.1
---
# Office and Period Model

## Offices (Salary Offices / Юрлица)
Offices represent legal entities/salary offices across geographies. Named after celestial bodies (anonymized).

**Active salary offices (~20+)**: Saturn, Mars (Nsk), Iupiter, Venera, Neptun, Uran, Titan (Montenegro), Protei (Georgia), Kallisto (Armenia), Sirius (Paris), Kassiopeia (remote NSK), Andromeda, Persei, Pegas, GoldenStar, Feniks, Skorpion, Mars (SPb), Pluton, Venera RF, Uran RF, Pluton RF, Altair, Venera France, Ulugbek, Venera (Uz)

**Key fields**:
- `salary` (boolean) — TRUE = salary office (employees get paid here). Non-salary offices (Академгородок, Париж, Дюссельдорф) appear legacy/inactive.
- `active` (boolean) — active in system
- Synced from Company Staff (`last_sync_time`)

## Period Model (office_period)
Each salary office has two period types controlling reporting/approval workflows:

| Type | Current (most offices) | Meaning |
|------|----------------------|---------|
| REPORT | 2026-03-01 | Employees can report hours starting from this month |
| APPROVE | 2026-02-01 | Managers can approve hours starting from this month |

**Pattern**: APPROVE period is 1 month behind REPORT period. This means:
- Employees currently report for March 2026
- Managers currently approve February 2026 reports
- Accountants advance these periods monthly

**Unique constraint**: (office, type) — exactly one REPORT and one APPROVE period per office.

**Accounting workflow**: Accountants advance periods forward (monthly operation). This is a critical accounting function — advancing the period closes the previous month for editing.

## Geographic Distribution
Russia (multiple cities: NSK, SPb), Serbia, Montenegro, Georgia, Armenia, France (Paris), Uzbekistan — multinational company.

## Related
- [[database-schema]]
- [[roles-permissions]]
- [[accounting-workflows]]
- [[ttt-service]]
