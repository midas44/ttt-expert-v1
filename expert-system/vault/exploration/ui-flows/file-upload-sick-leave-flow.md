---
type: exploration
tags:
  - file-upload
  - sick-leave
  - vacation-service
  - security
  - playwright
  - timemachine
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[sick-leave-service-implementation]]'
  - '[[vacation-service]]'
  - '[[file-upload-sick-leave-flow]]'
  - '[[security-patterns]]'
branch: release/2.1
---

# File Upload Flow — Sick Leave Attachments

Live testing of the complete file upload flow on timemachine environment via Playwright UI, covering sick leave creation with attachment, verification, and cleanup.

## Upload Architecture

- **Endpoint**: `POST /api/vacation/v1/files/upload` (multipart)
- **Auth**: Requires AUTHENTICATED_USER (JWT) — API_SECRET_TOKEN insufficient (403)
- **Storage**: Files saved as `/srv/ttt/uploads/files/{UUID}.{ext}` (original name discarded)
- **DB tables**: `ttt_vacation.file` (metadata + UUID path) → `ttt_vacation.sick_leave_file` (junction)
- **Frontend**: react-dropzone in `FileUploader` component, saga-based upload with rollback on failure

## Validation Rules

| Rule | Frontend | Backend |
|------|----------|---------|
| Max file size | 5 MB (client check) | Custom `@MultipartSizeValid` annotation |
| Max file count | 5 files (`@Size(max=5)`) | Same annotation |
| File types | PDF, PNG, JPEG (MIME check) | **No backend MIME validation** |
| Spring multipart | N/A | `max-file-size: -1`, `max-request-size: -1` (unlimited) |

## Security Findings

1. **No backend MIME validation** — Only frontend checks file types. Backend accepts any file if multipart size passes. Potential for malicious file upload.
2. **Unlimited Spring multipart** — `max-file-size: -1` and `max-request-size: -1` in application.yml bypass Spring's built-in size limits, relying solely on custom annotation.
3. **Stack trace leakage on 403** — When API_SECRET_TOKEN used for file operations, full Java stack trace (90+ frames) returned in error response. Confirmed on vacation service.

## UI Flow Verified

1. Create sick leave → date picker calendar widget (inputs readonly, click cells)
2. Attach file → react-dropzone hidden `input[type="file"]`, not native dialog
3. Submit → multipart upload, file gets UUID name, DB records created
4. View attachment → inline panel in sick leave list, "View sick note" link + thumbnail
5. Delete sick leave → cascading delete removes junction record and file record

## Test Data (Cleaned Up)

- Created sick leave id=353 (10-11 Mar 2026) as Galina Perekrest
- Uploaded test-sick-leave.pdf (450 bytes) → file id=360, UUID 533f52cc-6829-4fb9-8de9-09443018c7f0
- Junction: sick_leave_file id=254
- **Deleted via UI** — net zero impact on environment

## Key Observations

- Date picker inputs are readonly (`<input readonly>`), must interact via calendar widget clicks
- react-dropzone requires `setInputFiles()` on hidden input, not native file dialog
- File deletion cascades properly when parent sick leave is deleted
- Upload endpoint correctly rejects API_SECRET_TOKEN (AUTHORIZED but not AUTHENTICATED_USER)
