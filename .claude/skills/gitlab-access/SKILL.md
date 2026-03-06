---
name: gitlab-access
description: >
  Access the GitLab instance at gitlab.noveogroup.com — read issues/tickets,
  fetch comments, search issues by label/keyword, download file attachments
  (screenshots, images, documents), list pipelines, compare branches, and view
  code changes from the Time Tracking Tool (TTT / ttt-spring) project.
  Use this skill whenever the user mentions a GitLab ticket, issue URL, merge request,
  pipeline, branch, or asks to fetch/download/summarize anything from gitlab.noveogroup.com.
  Also use it when the user pastes a GitLab URL, references an issue number, asks to search
  for tickets, wants to list pipelines, see branch changes, compare commits, or mentions
  TTT/Time Tracking Tool/Time Reporting Tool issues. This includes tasks like
  "read ticket #3036", "get the screenshots from that issue", "summarize the GitLab issue",
  "find all vacation bugs in Sprint 14", "download the attachments",
  "list latest pipelines", "show changes in release/2.1", or "what files changed in the last pipeline".
---

# GitLab Access — Time Tracking Tool (TTT)

This skill provides instructions for interacting with the **Time Tracking Tool**
(also known as Time Reporting Tool, project path: `ttt-spring`) on the self-hosted
GitLab CE 16.11 instance at `gitlab.noveogroup.com`.

This skill is scoped to a single project:

| Field | Value |
|---|---|
| Project name | Time Tracking Tool (TTT) / Time Reporting Tool |
| GitLab path | `noveo-internal-tools/ttt-spring` |
| Project ID | `1288` |
| Web URL | https://gitlab.noveogroup.com/noveo-internal-tools/ttt-spring |

All operations below assume this project. There is no need to resolve the project ID —
always use `1288`.

## Configuration Files

- **PAT (API token):** stored in `.claude/.mcp.json` → `env.GITLAB_PERSONAL_ACCESS_TOKEN`
- **Web credentials (LDAP):** stored in `.claude/context/gitlab-credentials.md`

Read these files at the start of any GitLab operation to get the current credentials.

---

## 1. Reading Tickets (Issues)

Use the REST API with the Personal Access Token (PAT). This is fast and reliable.

### Fetch a Single Issue

Given a URL like `.../ttt-spring/-/issues/3036` or just an issue number, extract the
IID and fetch directly:

```bash
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/issues/$IID" | python3 -m json.tool
```

The response contains `title`, `description` (markdown body), `state`, `labels`,
`assignees`, `author`, `created_at`, `updated_at`, and `web_url`.

### Fetch Comments / Notes

```bash
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/issues/$IID/notes?per_page=100" | python3 -m json.tool
```

Attachments can appear in notes too — always check both `description` and note `body`
fields for `/uploads/` references when asked to download attachments.

### Search Issues

Use query parameters to filter issues by keyword and/or label:

```bash
curl -s --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/issues?labels=LABEL_NAME&search=KEYWORD&per_page=100&scope=all"
```

Label names with spaces need URL encoding (e.g., `Sprint%2014` for "Sprint 14").
Multiple labels can be comma-separated: `labels=Sprint%2014,Backend`.

The `search` parameter matches against title and description text.

### Summarize

When asked to summarize, extract: title, status, labels, assignee, creation date,
and a concise description of the problem and expected behavior. Note any attached
images (they appear as `![alt](/uploads/<hash>/<filename>)` in the description or notes).

---

## 2. Downloading Attachments

Uploaded files (screenshots, images, documents) in issue descriptions or comments are
served through **web routes**, not the API. The PAT does not work for these URLs — they
require a browser session obtained by logging in through the web UI with LDAP credentials.

### Why the API Doesn't Work

On this GitLab version (CE 16.11) at Developer access level, the PAT does not
authenticate web route requests (uploads). The only working method is a headless browser
that signs in via the LDAP form.

### Extract Upload URLs

Parse the issue `description` and all note `body` fields for markdown image references:

```
![alt_text](/uploads/<secret_hash>/<filename>)
```

Build the full URL:
```
https://gitlab.noveogroup.com/noveo-internal-tools/ttt-spring/uploads/<secret_hash>/<filename>
```

### Download Using the Bundled Script

A ready-made Puppeteer script is bundled at `scripts/download_attachments.mjs`.

**Step 1:** Ensure Puppeteer is installed (one-time, installs to `/tmp`):
```bash
cd /tmp && npm install puppeteer 2>&1 | tail -3
```

**Step 2:** Create a credentials file to avoid shell escaping issues with special
characters in passwords:
```bash
cat > /tmp/gl_creds.json << 'EOF'
{"login": "<username>", "password": "<password>"}
EOF
```

**Step 3:** Run the download script:
```bash
node <skill-path>/scripts/download_attachments.mjs \
  --credentials-file /tmp/gl_creds.json \
  --output "<output-directory>" \
  --urls "<url1>" "<url2>" ...
```

The `--credentials-file` approach is preferred over `--login`/`--password` CLI args
because passwords with special characters (like `!`) can be mangled by shell expansion.

The script will:
1. Launch headless Chrome
2. Navigate to the GitLab sign-in page
3. Fill the LDAP form (uses `#ldapmain_username` / `#ldapmain_password`)
4. Submit and verify login succeeded
5. Download each URL by navigating to it and saving the response buffer
6. Close the browser

**Step 4:** Verify the downloads:
```bash
file <output-directory>/*
```

Each file should report as the expected type (e.g., `PNG image data`). If it says
`HTML document`, the login likely failed — check credentials.

### Manual Fallback (Without the Script)

If Puppeteer is unavailable, write an inline Node.js script. Critical details:

- The sign-in page defaults to the **LDAP** tab
- Username field: `#ldapmain_username` (name: `username`)
- Password field: `#ldapmain_password` (name: `password`)
- Do NOT use `#user_login` / `#user_password` — those are on the Standard tab and
  typing into them will concatenate both values into one field
- Use `waitUntil: 'domcontentloaded'` (not `networkidle0` which can timeout)
- After login, verify `page.url()` does not contain `sign_in`

---

## 3. Pipelines, Branches & Code Changes

Use the REST API to list pipelines, compare branches, and see what files changed.

### List Pipelines

```bash
curl -s --noproxy "gitlab.noveogroup.com" --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/pipelines?per_page=10&order_by=id&sort=desc"
```

Key response fields: `id`, `iid`, `sha`, `ref` (branch/tag), `status`, `source`, `created_at`, `web_url`.

**Important:** Do NOT use `scope=all` — this GitLab version rejects it. Omit `scope` entirely.

Filter by branch:
```bash
...pipelines?ref=release/2.1&per_page=10&order_by=id&sort=desc
```

Filter by status: `status=success`, `status=failed`, `status=running`, etc.

### Compare Commits (What Changed Between Pipelines)

To see the code diff between two pipeline runs on the same branch, use the `compare` endpoint
with the `sha` values from each pipeline:

```bash
curl -s --noproxy "gitlab.noveogroup.com" --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/repository/compare?from=OLD_SHA&to=NEW_SHA"
```

The response contains:
- `commits[]` — list of commits between the two SHAs (`short_id`, `title`, `author_name`, `created_at`)
- `diffs[]` — list of changed files with fields:
  - `new_path` — file path
  - `new_file` (bool) — added file
  - `deleted_file` (bool) — deleted file
  - `renamed_file` (bool) — renamed file
  - `diff` — unified diff text

### List Branches

```bash
curl -s --noproxy "gitlab.noveogroup.com" --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/repository/branches?per_page=20&order_by=updated&sort=desc"
```

### Get a Single Commit

```bash
curl -s --noproxy "gitlab.noveogroup.com" --header "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.noveogroup.com/api/v4/projects/1288/repository/commits/COMMIT_SHA"
```

### Workflow: "What changed in the latest pipeline on branch X?"

1. Fetch the 2 most recent pipelines for the branch: `?ref=BRANCH&per_page=2&order_by=id&sort=desc`
2. Extract the `sha` from each pipeline (newer = `to`, older = `from`)
3. Call the compare endpoint with those SHAs
4. Parse the `commits` and `diffs` arrays from the response

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Downloaded file is HTML, not image | Login failed or session expired | Check credentials, verify LDAP selectors |
| Both values in username field | Wrong form tab selectors used | Use `#ldapmain_*` not `#user_*` |
| Navigation timeout | `networkidle0` too strict | Switch to `domcontentloaded` |
| 404 on API endpoint | Wrong project ID | Use `1288` for ttt-spring |
| 302 redirect to sign_in | PAT used on web route | Use Puppeteer method instead |
| `scope does not have a valid value` | Used `scope=all` on pipelines endpoint | Omit `scope` param — only valid for issues |
| Password with `!` or special chars mangled | Shell expansion | Use `--credentials-file` instead of `--password` |

---

## Reference Files

- `references/api-reference.md` — Full list of API endpoints, response field mappings, search parameters
- `scripts/download_attachments.mjs` — Puppeteer script for downloading uploads via LDAP auth
