---
name: figma-access
description: >
  Access the Figma project for the Time Tracking Tool (TTT / Noveo-TTT) — read design
  mockups, inspect node structure, take screenshots, and extract design specs. Use this
  skill whenever the user mentions Figma, pastes a figma.com URL, asks to inspect a design,
  get a screenshot of a mockup, extract design details, or references "Noveo-TTT" designs.
  Also use when the user asks to "read the Figma", "get the mockup", "screenshot this node",
  "inspect the design", "download from Figma", or mentions a Figma node ID. If the user
  provides a Figma URL, always use this skill.
---

# Figma Access — Time Tracking Tool (TTT)

This skill provides instructions for reading designs from the **Noveo-TTT** Figma file.

| Field | Value |
|---|---|
| Project name | Noveo-TTT |
| File key | `H2aXBseq7Ui60zlh5vhyjy` |
| File URL | https://www.figma.com/design/H2aXBseq7Ui60zlh5vhyjy/Noveo-TTT |

## Authentication

Two auth methods are available:

| Method | Purpose | Source |
|---|---|---|
| **Figma MCP** (OAuth) | Read metadata, screenshots inline, design context | Configured in `.claude/.mcp.json` → `figma` server |
| **Personal Access Token** | Download/export images to files via REST API | Stored in `.claude/context/secrets/figma-token.txt` |

Read the token file at the start of any export/download operation:

```bash
FIGMA_TOKEN=$(cat .claude/context/secrets/figma-token.txt)
```

## URL Parsing

Extract `fileKey` and `nodeId` from Figma URLs:

| URL pattern | fileKey | nodeId |
|---|---|---|
| `figma.com/design/:fileKey/:name?node-id=A-B` | `:fileKey` | `A:B` (replace `-` with `:`) |
| `figma.com/design/:fileKey/branch/:branchKey/:name` | `:branchKey` | from `node-id` param |
| `figma.com/board/:fileKey/:name` | `:fileKey` | FigJam — use `get_figjam` |

**Important:** Node IDs in URLs use `-` as separator (`38435-3910904`) but MCP tools
accept both `-` and `:` formats (`38435:3910904`).

---

## 1. Inspecting Design Structure (Metadata)

Use `mcp__figma__get_metadata` to get the XML-like node tree:

```
fileKey: H2aXBseq7Ui60zlh5vhyjy
nodeId: <extracted from URL, or "0:1" for first page>
```

This returns node IDs, layer names, types, positions, and sizes. Useful for getting an
overview of what's in a frame before drilling deeper.

**Note:** For large nodes (full pages), the response can be very large (600K+). Use
`get_design_context` on specific sub-nodes instead.

---

## 2. Getting Design Context

Use `mcp__figma__get_design_context` for design-to-code workflows. Returns reference code,
a screenshot, and contextual metadata.

```
fileKey: H2aXBseq7Ui60zlh5vhyjy
nodeId: <node ID>
```

If the selected node is a **section**, you'll get sparse metadata. Drill into individual
child nodes for full design context.

---

## 3. Taking Screenshots (Inline)

Use `mcp__figma__get_screenshot` to get a visual screenshot rendered inline in the conversation:

```
fileKey: H2aXBseq7Ui60zlh5vhyjy
nodeId: <node ID>
```

This is useful for AI understanding of the design but does **not** save to a file.
To save screenshots to disk, use the REST API export method below.

---

## 4. Exporting Screenshots to Files

The MCP tools return screenshots inline but cannot save them to disk. Use the Figma
REST API with the Personal Access Token to export and download images.

### Step 1: Get the image export URL

```bash
FIGMA_TOKEN=$(cat .claude/context/secrets/figma-token.txt)

curl -s \
  -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/H2aXBseq7Ui60zlh5vhyjy?ids=$NODE_ID&format=png&scale=2"
```

Response:
```json
{
  "err": null,
  "images": {
    "38435:3910904": "https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/..."
  }
}
```

### Step 2: Download the PNG

```bash
IMAGE_URL=$(curl -s \
  -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/H2aXBseq7Ui60zlh5vhyjy?ids=$NODE_ID&format=png&scale=2" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d['images'].values())[0])")

mkdir -p artifacts/figma
curl -s -o "artifacts/figma/$FILENAME.png" "$IMAGE_URL"
```

### Step 3: Flatten transparency

Figma exports often have **transparent backgrounds**, making text hard to read on dark
backgrounds. Always flatten RGBA to RGB with a white background:

```bash
cd /tmp && node -e "
const sharp = require('sharp');
sharp('$INPUT_PATH')
  .flatten({ background: '#ffffff' })
  .toFile('$OUTPUT_PATH')
  .then(() => console.log('OK'))
  .catch(e => console.error(e));
"
```

**Prerequisites:** sharp must be installed in `/tmp`:
```bash
cd /tmp && npm install sharp 2>&1 | tail -3
```

### Step 4: Verify

```bash
file artifacts/figma/*.png
ls -lh artifacts/figma/*.png
```

Expected: `PNG image data, ... 8-bit/color RGB` (not RGBA).

### Bundled Script

A convenience script is available at `<skill-path>/scripts/export_screenshot.sh`:

```bash
.claude/skills/figma-access/scripts/export_screenshot.sh <node-id> <output-filename>
```

---

## 5. Summarizing Design Content

When asked to summarize a Figma node:

1. Use `get_screenshot` to visually inspect the design
2. Use `get_metadata` to get the structural breakdown
3. Extract from the screenshot:
   - Frame/section title and ticket reference (e.g., "#3093 pt 3")
   - All visible text labels and field values
   - UI element types (dialogs, tables, buttons, forms)
   - Color-coded legend if present
   - Spec notes / annotations
4. Present as a structured summary with tables for field lists

---

## Output Directory

Save all exported Figma artifacts to:
```
artifacts/figma/
```

Use descriptive filenames based on the node name and ID:
```
artifacts/figma/<descriptive-name>-<nodeId>.png
```

Example: `project-details-38435-3910904.png`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| MCP not visible in `/mcp` | Not registered as local-scope | Run `claude mcp add-json figma '{"type":"http","url":"https://mcp.figma.com/mcp"}'` |
| "Authentication required" | OAuth session expired | Run `/mcp` → figma → Authenticate |
| Exported PNG has transparent BG | Figma default export | Flatten with sharp (see Step 3) |
| `sharp` not found | Not installed | `cd /tmp && npm install sharp` |
| REST API 403 | Invalid or expired PAT | Generate new token at Figma Settings → Personal access tokens |
| Huge metadata response | Queried a full page | Query specific sub-nodes by their ID instead |
| `get_design_context` returns sparse data | Selected a section node | Drill into individual child nodes |
