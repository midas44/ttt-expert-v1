---
type: exploration
tags:
  - email
  - templates
  - legacy
  - code-analysis
  - dead-code
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[exploration/data-findings/email-templates-inventory]]'
  - '[[exploration/data-findings/email-template-field-mapping]]'
  - '[[modules/email-service]]'
  - '[[patterns/email-notification-triggers]]'
---

# Legacy vs New Email Template Coexistence

## Conclusion: No Active Coexistence

The 50 legacy templates (NEW_VACATION_PM, CANCEL_VACATION_DM, etc.) are **database artifacts only**. Zero references in active Java source code. All current notification code exclusively uses NOTIFY_* templates (70 templates).

## Evidence

**Code search**: Grep across entire `src/main/java/` for legacy template names (NEW_VACATION_, CANCEL_VACATION_, DELETE_VACATION_, UPDATE_VACATION_, VACATION_CONFIRMED_, VACATION_IS_COMING, VACATION_STATUS_CHANGED_) — **zero matches**.

**Template constants**: All active templates defined in dedicated constants classes:
- `VacationTemplateConstants.java` — NOTIFY_VACATION_* constants
- `DayOffTemplateConstants.java` — NOTIFY_DAYOFF_* constants
- `SickLeaveTemplateConstants.java` — NOTIFY_SICKLEAVE_* constants

## Routing Architecture

**No conditional selection**: Template code is hardcoded per notification helper. No feature toggle, config flag, or conditional logic selects between legacy/new.

**Dispatch chain**: Domain event → Event listener → Notification helper → hardcoded NOTIFY_* constant → `AbstractVacationNotificationHelper.doSendEmail()` → `InternalEmailService.send()`.

**Async toggle**: `EMAIL_ASYNC` feature flag controls sync vs async delivery, NOT template selection.

## Legacy Template Status: Dead Code

Legacy templates were likely created in a previous application version. The current codebase (release/2.1) has no mechanism to invoke them. They remain in the `email_template` DB table but are never referenced.

**Implication for testing**: Only 70 NOTIFY_* templates need test coverage. The 50 legacy templates can be ignored for functional testing (but may warrant a cleanup ticket).

## Connections
- [[exploration/data-findings/email-templates-inventory]] — full 120-template inventory
- [[exploration/data-findings/email-template-field-mapping]] — per-template variable mapping
- [[patterns/email-notification-triggers]] — trigger patterns
- [[modules/email-service]] — email service architecture
