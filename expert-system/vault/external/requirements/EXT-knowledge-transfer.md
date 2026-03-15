---
type: external
tags: [testing, knowledge-transfer, automation, process, google-docs, technical-debt]
created: 2026-03-13
updated: 2026-03-13
status: active
related: ["[[EXT-test-plan]]", "[[EXT-vacation-testing-notes]]", "[[architecture/roles-permissions]]"]
---

# Knowledge Transfer — nshevtsova (Google Doc)

Source: docs.google.com/document/d/14BeQg5tPuxMmU4cFi2izeB8tnt7MEQyGDjxxvF3bF5A

QA handoff document from nshevtsova. Key technical knowledge:

## Automation Status (at time of transfer)
- **Admin > Projects**: Partially done (6/10 endpoints covered)
- **Admin > Employees/Contractors**: Only GET list endpoint
- **Admin > API, Parameters, Calendar**: Not started
- **Accounting**: Not started
- **Planner**: Not started

## Known Technical Quirks

### Project country field
- Was optional, became required in UI but remained optional in backend
- Server has implicit logic: if country not sent, copies from existing project of same customer
- Can cause test failures: empty country → unparseable response → temp project not cleaned up → role leakage

### Project deletion race condition
- Project creation is 2-phase: response + async event history
- Immediate delete after create can fail with 500 (event not yet written)
- Workaround: `request_retry` wrapper (GitLab #2076)

### String comparison inconsistency
- Projects: case-insensitive sort ("Noveo" == "noveo")
- Employees: case-sensitive sort ("Noveo" ≠ "noveo")
- GitLab #2049

### Role parametrization issues
- Observer/Owner roles must be assigned in fixture, not hardcoded
- ~75 admin tests fail due to missing seniorManager on test user
- Permissions are derived from roles/assignments, not set directly

### Other notes
- Marshmallow warning in test output (unresolved, related to dataclasses)
- Accept-Language header unused (agreed not to test, 19.10.21)
- Pagination service in utils for multi-page API responses
- Cyclic import workaround: temp_project fixture in separate file (not conftest)

## Open TODOs (at transfer time)
1. Role parametrization fixes (GitLab #2169)
2. Rename error dataclasses per Swagger spec
3. Swagger-coverage "Missing" column meaning unknown
4. Fixture scope optimization for test speed
