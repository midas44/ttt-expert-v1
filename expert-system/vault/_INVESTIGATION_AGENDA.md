# Investigation Agenda

## Priority Legend
- P0: Critical — must complete this session
- P1: High — target for next 1-2 sessions
- P2: Medium — within next 5 sessions
- P3: Low — backlog

## Completed (Sessions 1-64)
<details>
<summary>Sessions 1-62 completed items (click to expand)</summary>

### Sessions 1-52
See session 52 agenda for full history. Summary:
- 52 sessions of knowledge acquisition and Phase B generation
- 159 vault notes, 131 analysis runs, 121 design issues, 173 exploration findings
- Phase B: 520 test cases generated across 5 modules (Statistics, Sick Leave, Day-Off, Security, Accounting)
- Complete coverage across all areas

### Sessions 53-57 (Coverage Reset — Deep Re-Investigation)
- [x] Vacation, Reports, Day-Off, Sick Leave, Accounting, Admin, Calendar, Email deep-dives
- [x] Frontend-backend validation gap analysis (25 gaps)
- [x] Cross-service integration deep-dive (RabbitMQ, CS sync, WebSocket)
- [x] Phase B transition: coverage >=80%, config.yaml updated

### Sessions 58-62 (Phase B — Test Documentation Generation)
- [x] S58: Vacation — 130 cases, 8 suites, 11 tabs
- [x] S59: Sick Leave (120 cases, 6 suites) + Day-Off (108 cases, 6 suites) + Maintenance
- [x] S60: Reports — 110 cases, 7 suites, 10 tabs
- [x] S61: Accounting — 92 cases, 6 suites, 9 tabs
- [x] S62: Admin — 70 cases, 6 suites, 9 tabs

</details>

### Session 63 (Phase B — Statistics Regeneration & Review)
- [x] Review all 8 XLSX workbooks: structure, tab counts, case counts verified
- [x] Regenerate statistics.xlsx from legacy S48 flat format to unified workbook format
- [x] 7 test suites: GeneralUI(26), EmpReports(33), API(16), NormCalc(10), Access(9), DataCache(9), Export(8)
- [x] 14 risks assessed, Plan Overview + Feature Matrix + Risk Assessment + hyperlinks
- [x] SQLite updated: xlsx_file path, analysis_runs entry

### Session 64 (Maintenance + Security Regeneration)
- [x] §9.4 Maintenance: vault audit (167 notes clean), SQLite integrity check, cross-ref audit
- [x] Security workbook regeneration: legacy S51 tuple format → unified dict-based format
- [x] 8 suites preserved: JWTAuth(12), APIToken(12), RoleAccess(14), EndpointPerm(13), SoDuties(9), InfoLeak(10), ObjPerm(9), InputVal(13)
- [x] 13 risks, dynamic Plan Overview + Feature Matrix + hyperlinks
- [x] SQLite updated: test_case_tracking, analysis_runs

## Phase B — ALL MODULES COMPLETE, ALL UNIFIED

**Total: 833 test cases across 8 unified XLSX workbooks (60 test suites)**

### Known Gaps (not blocking — P3)
- [ ] Planner module (Google Doc access denied — blocked)
- [ ] #3400 individual norm export — endpoint 404 despite "Production Ready" ticket
- [ ] Sprint 16 tickets: #2842 (contractor termination), #2954 (sick leave working days), #2876 (vacation event feed bugs)
- [ ] Frontend architecture analysis (useful for future maintenance)
