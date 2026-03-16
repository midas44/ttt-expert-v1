---
type: module
tags:
  - email
  - notification
  - digest
  - deep-dive
  - rabbitmq
  - mustache
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[modules/vacation-service-deep-dive]]'
  - '[[modules/ttt-report-service-deep-dive]]'
  - '[[modules/dayoff-service-deep-dive]]'
  - '[[modules/sick-leave-service-deep-dive]]'
  - '[[modules/accounting-service-deep-dive]]'
branch: release/2.1
---
# Email & Notification Service Deep Dive

The email/notification system is a separate microservice (`email/`) plus cross-service notification infrastructure in vacation and TTT services. Mustache templates, RabbitMQ async path, batch SMTP sending, digest compilation.

## 1. Architecture — End-to-End Flow

```
Business Logic (Vacation/TTT/Calendar service)
  ↓
InternalEmailService.send(EmailApi)
  ↓
Feature toggle EMAIL_ASYNC?
  ├─ ON:  Spring ApplicationEvent → RabbitMQ → SendEmailEventHandler → EmailService.save()
  └─ OFF: Feign EmailClient.send() → EmailController → EmailService.save()
      ↓
EmailService.save():
  1. Render Mustache template (if template code provided)
  2. Append signature (if signatureCode provided)
  3. Prepend subject prefix
  4. Add test BCC addresses
  5. Generate UUID
  6. Insert to DB (status = NEW)
      ↓
EmailSendScheduler (cron) → EmailBatchService.send():
  1. EmailReader.read() — fetch status=NEW emails
  2. EmailProcessor.process() — build MimeMessage with attachments
  3. EmailWriter.write() — JavaMailSender.send() via SMTP
  4. Update status: NEW → SENT | FAILED | INVALID
```

## 2. Email Service Core (EmailServiceImpl)

### save(EmailBO) — Email Persistence

```java
// 1. Template rendering
if (emailBO.getTemplate() != null) {
    RenderedMailBO rendered = emailTemplateService.render(
        emailBO.getTemplate().getCode(),
        emailBO.getTemplate().getData()  // JSON string
    );
    emailBO.setSubject(rendered.getSubject());
    emailBO.setBody(rendered.getBody());
}

// 2. Signature appending
if (emailBO.getSignatureCode() != null) {
    EmailSignature signature = emailSignatureService.find(emailBO.getSignatureCode());
    emailBO.setBody(emailBO.getBody() + "\n" + signature.getBody());
}

// 3. Subject prefix
emailBO.setSubject(subjectPrefix + emailBO.getSubject());

// 4. Test BCC injection
if (testBcc != null) {
    emailBO.getBcc().addAll(Arrays.asList(testBcc.split(",")));
}

// 5. UUID + persist
emailBO.setId(UUID.randomUUID().toString());
emailRepository.insert(convert(emailBO));
// 6. Attachment association
updateAttachments(emailBO.getId(), emailBO.getFiles());
```

### Email Entity Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID (String) | Primary key, generated |
| `from` | String | Sender address |
| `to` | String | Comma-separated recipients |
| `cc` | String | Comma-separated CC |
| `bcc` | String | Comma-separated BCC |
| `subject` | String | Rendered subject line |
| `body` | TEXT | Rendered HTML body |
| `status` | StatusType | NEW → SENT / FAILED / INVALID |
| `errorMessage` | String | Populated on failure |
| `addTime` | LocalDateTime | Auto-set on insert |
| `sentTime` | LocalDateTime | Set after successful SMTP send |

### StatusType State Machine

```
NEW ──→ SENT     (successful SMTP delivery)
    ──→ FAILED   (SMTP connection/auth/delivery error)
    ──→ INVALID  (SendFailedException with invalid email addresses)
```

No retry from FAILED → NEW. Failed emails stay in FAILED state permanently. Only NEW emails are picked up by the batch processor.

## 3. Template Rendering (Mustache)

### EmailTemplateServiceImpl

```java
// Uses com.samskivert.mustache (Mustache.js compiler)
// 1. Fetch EmailTemplate by code from DB
// 2. Parse data (JSON string) → Map via Jackson ObjectMapper
// 3. Compile subject template → execute with data → rendered subject
// 4. Compile body template → execute with data → rendered body
```

### Template Database Storage

Templates stored as `email_template` records (code, subject, body). Managed via Flyway repeatable migrations (`R__*.sql` files).

### Template Categories (35+ templates)

**Vacation:**
- `NEW_VACATION_PM` — New vacation request notification to PM
- `NEW_VACATION_DM` — New vacation request notification to DM
- `APPROVE_REQUEST` — Approval request to approver
- `APPROVE_REJECT` — Rejection notification
- `APPROVE_REQUEST_FOR_EMPLOYEE` — Approval confirmation to employee
- `ASK_MANAGER_FOR_VACATION_APPROVAL` — Reminder to approve

**Sick Leave:**
- `NOTIFY_SICKLEAVE_OPEN` — Sick leave opened notification

**Day-Off:**
- `NOTIFY_CALENDAR_UPDATE_DAYOFF_DELETED_TO_EMPLOYEE` — Day-off deleted due to calendar change

**Reports:**
- `REPORT_SHEET_CHANGED` — Report modified notification
- `FORGOTTEN_REPORT` — Report not submitted reminder
- `STATISTICS_FORGOTTEN_REPORT` — Statistics-based forgotten report

**Budget:**
- `BUDGET_NOTIFICATION_EXCEEDED` — Budget exceeded alert
- `BUDGET_NOTIFICATION_NOT_REACHED` — Budget not reached
- `BUDGET_NOTIFICATION_DATE_UPDATED` — Budget date changed

**Employee:**
- `EMPLOYEE_NEW` — New employee welcome
- `EMPLOYEE_RATING_EVALUATION` — Rating evaluation notification

**Accruals:**
- `NOTIFY_ABOUT_ACCRUALS_BY_HIRE_TEMPLATE_NAME` — Vacation days accrual notification

**Digest:**
- `DIGEST` — Comprehensive multi-event digest (21KB template — largest)

**Signature:**
- Email signature defined in `R__EDIT_TTT_EMAIL_SIGNATURE.sql` (14KB)

### Mustache Syntax

```mustache
<!-- Variables -->
{{to_name}}, {{reportDate}}, {{manager}}

<!-- Conditionals -->
{{#managerDateLine}}...shown if truthy...{{/managerDateLine}}

<!-- Arrays/loops -->
{{#taskReportLine}}
  {{taskName}} — {{actualEfforts}}h
{{/taskReportLine}}
```

## 4. Batch Email Processing

### EmailSendScheduler

```java
@Scheduled(cron = "${email.scheduler.send.cron}")
@SchedulerLock(name = "EmailSendScheduler.sendEmails")
@Timed(value = "scheduled", longTask = true)
public void sendEmails() {
    int count = emailBatchService.send();
    log.info("Sent {} emails", count);
}
```

### EmailBatchServiceImpl.send()

```java
// 1. Create temp directory for attachments
Path tempDir = Files.createTempDirectory("email-attachments");
try {
    // 2. Read unprocessed emails (status=NEW, limit=pageSize)
    List<Email> emails = emailReader.read();
    
    // 3. Process each: build MimeMessage
    List<MimeMessage> messages = emails.stream()
        .map(email -> emailProcessor.process(email, attachments, tempDir))
        .filter(Objects::nonNull)  // skip processing failures
        .collect(toList());
    
    // 4. Send batch via SMTP
    emailWriter.write(messages);
} finally {
    // 5. Cleanup temp directory
    FileUtils.deleteDirectory(tempDir);
}
```

### EmailProcessor.process()

```java
// 1. Create IdentifiableMimeMessage (custom MimeMessage subclass with email UUID)
// 2. MimeMessageHelper with UTF-8, multipart=true
// 3. Set from, to, cc, bcc (parse comma-separated via parseAddresses())
// 4. Fetch file attachments via Feign FileClient.getFileInputStream()
//    - Save to temp directory
//    - Extract content type from response headers
//    - Extract filename from Content-Disposition header
//    - Attach with lazy-loaded InputStreamResource
// 5. Set subject and body as HTML: setText(body, true)
```

### EmailWriter.write() — SMTP Send + Status Update

```java
// 1. Send all messages: javaMailSender.send(messages.toArray())
// 2. On success: update all emails to SENT with sentTime
// 3. On MailSendException (partial failure):
//    - Extract failed messages map from exception
//    - Failed: status = FAILED or INVALID
//    - INVALID if SendFailedException with invalid addresses
//    - Succeeded (not in failed map): status = SENT
// 4. On MailAuthenticationException: log error (no status update!)
```

**Design issue**: `MailAuthenticationException` is caught and logged but email statuses are NOT updated. Emails stay as NEW and will be retried every batch cycle, potentially forever.

**Design issue**: No retry count tracking. FAILED emails stay in FAILED state permanently, but the only way to retry is manual DB update back to NEW.

## 5. Async Email Path (RabbitMQ)

### Feature Toggle: EMAIL_ASYNC

Both vacation and TTT services check `EMAIL_ASYNC` feature toggle:

```java
// InternalEmailService (Vacation service)
public void send(EmailApi email) {
    email.setSignatureCode(signatureCode);
    if (featureToggleService.isEnabled(EMAIL_ASYNC)) {
        eventPublisher.publishEvent(new SendEmailApplicationEvent(
            conversionService.convert(email, EmailBO.class)));
    } else {
        emailClient.send(email, apiToken);  // sync Feign call
    }
}
```

### TTT Service Variant

```java
// InternalEmailService (TTT service) — slightly different
public boolean send(EmailApi email) {
    if (email.getFrom() == null) {
        email.setFrom(emailSettingsService.getFrom());  // default from address
    }
    email.setSignatureCode(signatureCode);
    try {
        if (featureToggleService.isEnabled(EMAIL_ASYNC)) {
            eventPublisher.publishEvent(new SendEmailApplicationEvent(...));
        } else {
            emailClient.send(email, apiToken);
        }
        return true;
    } catch (Exception e) {
        log.warn("Failed to send email", e);
        return false;  // swallows exception!
    }
}
```

**Design issue**: TTT InternalEmailService swallows all exceptions and returns false. Callers cannot distinguish "email service down" from "template not found" from "invalid data".

### SendEmailEventHandler (Email Service — MQ Consumer)

```java
@Timed("rabbit_handler")
public void handle(SendEmailEvent event) {
    EmailBO emailBO = conversionService.convert(event.getPayload(), EmailBO.class);
    emailService.save(emailBO);
}
```

Simply converts RabbitMQ event to EmailBO and saves to DB for batch processing.

## 6. Vacation Notification Helpers

### AbstractVacationNotificationHelper — Base Class

```java
// fillBaseInfo(Map data, VacationBO vacation, String to)
// Populates template variables:
data.put("employee", formatName(employeeName));       // Russian name format
data.put("approver", formatName(approverName));
data.put("dm", formatName(dmName));
data.put("vacationType", type);   // "Очередная" (Regular) or "Административная" (Administrative)
data.put("status", status);       // Russian: "Новая", "Подтверждена", "Отклонена", "Отменена", "Оплачена"
data.put("period", startDate + " - " + endDate);
data.put("regularDays", count);
data.put("adminDays", count);
data.put("paymentDate", date);     // if applicable
data.put("comment", comment);      // stripped of blank
data.put("confirmUrl", "https://ttt.noveogroup.com/vacation/request");  // HARDCODED!
```

**Design issue**: Confirmation URL is hardcoded to `ttt.noveogroup.com` — won't work for testing environments. Should be configurable.

### Concrete Helpers

| Helper | Purpose |
|--------|---------|
| `VacationChangeStatusNotificationHelper` | Status change emails (approve/reject/cancel) |
| `VacationApproverChangeNotificationHelper` | Approver changed notification |
| `VacationCalendarCreationHelper` | Calendar-triggered vacation creation |
| `VacationCalendarUpdateNotificationHelper` | Calendar change affecting vacation |
| `SickLeaveNotificationHelper` | Sick leave lifecycle emails |
| `EmployeeDayOffNotificationHelper` | Day-off lifecycle emails |
| `AvailabilityScheduleNotificationHelper` | Availability chart notifications |

### doSendEmail Pattern

```java
protected void doSendEmail(String to, String templateCode, Map<String, String> data, Long vacationId) {
    EmailApi email = new EmailApi();
    email.setFrom(emailSettings.getFrom());
    email.setTo(Set.of(to));
    email.setTemplate(new TemplateBodyApi(templateCode, objectMapper.valueToTree(data)));
    try {
        internalEmailService.send(email);
        log.info("Sent {} to {} for vacation {}", templateCode, to, vacationId);
    } catch (Exception e) {
        log.error("Failed to send {} to {} for vacation {}", templateCode, to, vacationId, e);
    }
}
```

## 7. Scheduled Notification Jobs

### TTT Service Schedulers

| Job | ShedLock Name | Cron Config | Purpose |
|-----|--------------|-------------|---------|
| `sendReportsChangedNotifications` | `TaskReportNotificationScheduler.sendReportsChangedNotifications` | `${ttt.notification.report-sheet-changed.cron}` | Notify when reports modified |
| `sendReportsForgottenNotifications` | `TaskReportNotificationScheduler.sendReportsForgottenNotifications` | `${ttt.notification.report-forgotten.cron}` | Remind about missing reports |
| `sendReportsForgottenDelayedNotifications` | `TaskReportNotificationScheduler.sendReportsForgottenDelayedNotifications` | `${ttt.notification.report-forgotten-delayed.cron}` | Second reminder wave |
| `sendRejectNotifications` | `TaskReportNotificationScheduler.sendRejectNotifications` | `${ttt.notification.reject.cron}` | Notify about rejected reports |
| `sendBudgetNotifications` | `BudgetNotificationScheduler.sendBudgetNotifications` | `${ttt.notification.budget.cron}` | Budget exceeded/not reached alerts |

### Vacation Service Schedulers

| Job | ShedLock Name | Cron Config | Purpose |
|-----|--------------|-------------|---------|
| `sendDigests` | `DigestScheduler.sendDigests` | `${digest.cron}` | Daily/weekly absence digest emails |

### Email Service Scheduler

| Job | ShedLock Name | Cron Config | Purpose |
|-----|--------------|-------------|---------|
| `sendEmails` | `EmailSendScheduler.sendEmails` | `${email.scheduler.send.cron}` | Batch SMTP delivery |

All jobs use ShedLock for distributed locking and `@Timed` for Prometheus metrics.

## 8. Digest System (Vacation Service)

### Architecture

```
DigestScheduler (cron)
  → DigestService.sendDigests()
    → TimelineEventProcessor(s) — 28+ implementations
      → Process each timeline event into digest items
      → Group by receiver
      → Render DIGEST template
      → Send via InternalEmailService
```

### Event Processors (per absence type)

**Vacation processors** (in `digest/processor/vacation/`):
- VacationCreatedEventProcessor
- VacationApprovedEventProcessor
- AllApprovedEventProcessor
- VacationRejectedEventProcessor
- VacationCanceledEventProcessor
- VacationPaidEventProcessor
- etc.

**Day-off processors** (in `digest/processor/dayoff/`):
- DayOffCreatedEventProcessor
- DayOffApprovedEventProcessor
- etc.

**Sick leave processors** (in `digest/processor/sickleave/`):
- SickLeaveOpenedEventProcessor
- SickLeaveClosedEventProcessor
- etc.

### Receiver Calculation

```java
// AbstractTimelineEventProcessor.getReceivers()
// Determines who gets this event in their digest:
ReceiverRole.APPROVER          — the vacation approver
ReceiverRole.OPTIONAL_APPROVER — additional optional approvers
ReceiverRole.NOTIFY_ALSO       — office notification receivers + custom notify recipients
// Sorted by priority, falls back to timeline event data if vacation deleted
```

### Digest Template

The `DIGEST` template (21KB) is the largest template — it renders a multi-section email containing all relevant events for a receiver within the digest period.

## 9. Inter-Service Communication

### Feign Email Client

```java
@FeignClient(name = "ttt-email", configuration = RequestMetaClientConfiguration.class)
public interface EmailClient {
    @PostMapping("/v1/emails")
    String send(@RequestBody EmailApi email, @RequestHeader("API_SECRET_TOKEN") String apiToken);
}
```

### EmailApi DTO

```java
public class EmailApi {
    String id;                    // optional reference ID
    String from;                  // sender address
    Set<String> to;               // recipients
    Set<String> cc, bcc;          // CC/BCC
    String subject;               // pre-rendered OR empty if template used
    String body;                  // pre-rendered HTML OR empty if template used
    String signatureCode;         // signature to append
    TemplateBodyApi template;     // template code + JSON data
    Set<UUID> files;              // attachment file UUIDs
}

public class TemplateBodyApi {
    String code;                  // template identifier (e.g., "REPORT_SHEET_CHANGED")
    JsonNode data;                // template variables as JSON
}
```

**Dual rendering paths**: Emails can be sent with pre-rendered subject/body OR with a template code + data. The email service renders templates server-side if template is provided.

## 10. Configuration Parameters

```properties
# Email Service
email.scheduler.send.cron          # Batch send frequency
email.scheduler.send.pageSize      # Emails per batch
email.scheduler.prune.older        # Retention duration (e.g., PT30D)
email.test.bcc                     # Test BCC addresses (comma-separated)
email.subject-prefix               # Prefix for all subjects
email.signature-code               # Default signature code

# Vacation Service
vacation.api-token                  # Feign client auth token
email.signature-code               # Vacation-specific signature
digest.cron                        # Digest frequency

# TTT Service
ttt.api-token                      # Feign client auth token
ttt.notification.signature-code    # TTT-specific signature
ttt.notification.report-sheet-changed.cron
ttt.notification.report-forgotten.cron
ttt.notification.report-forgotten-delayed.cron
ttt.notification.reject.cron
ttt.notification.budget.cron
```

## 11. Design Issues Catalog

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **Critical** | `EmailWriter` | `MailAuthenticationException` caught but email statuses NOT updated — emails stay NEW, retried indefinitely |
| 2 | **Major** | `AbstractVacationNotificationHelper` | Confirmation URL hardcoded to `ttt.noveogroup.com` — broken on test environments |
| 3 | **Major** | TTT `InternalEmailService` | Swallows all exceptions, returns false — callers cannot distinguish failure types |
| 4 | **Major** | Email service | No retry count tracking. FAILED emails permanent unless manual DB intervention |
| 5 | **Minor** | Email entity | `to`/`cc`/`bcc` stored as comma-separated strings, not arrays. Parsing relies on ADDRESS_SEPARATOR = "," |
| 6 | **Minor** | `EmailProcessor` | File attachment errors logged but wrapped as RuntimeException — one bad attachment fails entire email |
| 7 | **Minor** | Template rendering | If template code doesn't exist in DB, `EmailTemplateService.render()` will throw — no graceful fallback |
| 8 | **Minor** | Batch processing | No dead letter queue or max retry concept. Only batch size limits throughput |

## 12. Boundary Values for Testing

- Email addresses: empty string, null, invalid format, multiple comma-separated
- Template code: existing, non-existing, empty string
- Template data: valid JSON, missing required variables, extra variables
- Subject prefix: empty, with prefix, with special characters
- Attachment UUIDs: valid, non-existing file UUID, null
- Signature code: existing, non-existing, null
- Batch processing: 0 emails, 1 email, pageSize emails, partial SMTP failure
- Status transitions: NEW→SENT, NEW→FAILED, NEW→INVALID
- Digest period: no events, single event, multiple event types, deleted vacation referenced

See also: [[modules/vacation-service-deep-dive]], [[modules/ttt-report-service-deep-dive]], [[modules/sick-leave-service-deep-dive]], [[modules/dayoff-service-deep-dive]]
