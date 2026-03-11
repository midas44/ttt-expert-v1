# Human Guide — Setting Up and Operating the Case 1 Expert System

> **Purpose:** Step-by-step guide for installing, configuring, and operating the AI expert system for legacy web app investigation and test documentation generation.

---

## 1. Prerequisites

**System:** Ubuntu Server with desktop environment (accessed via RDP).

**Already installed and configured:**
- Node.js >= 18.x and npm
- Claude Code with Opus model access (MAX plan subscription)
- Pre-installed MCPs: GitLab, Confluence, Figma, Qase, Playwright, Swagger/API, PostgreSQL

---

## 2. Component Installation

### 2.1 System Dependencies

```bash
# Java SDK — needed for Maven dependency analysis
sudo apt update
sudo apt install -y openjdk-17-jdk
java --version

# Maven — needed for backend static analysis
sudo apt install -y maven
mvn --version

# Python 3 + libraries for XLSX generation and analysis scripts
sudo apt install -y python3 python3-pip python3-venv
pip3 install --break-system-packages openpyxl pandas
python3 -c "import openpyxl; print('openpyxl OK')"

# Bun runtime — required for QMD
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
bun --version
```

### 2.2 Static Analysis Tools

```bash
npm install -g eslint madge jscpd ts-prune complexity-report

# Verify
which eslint madge jscpd ts-prune cr
```

Optional — standalone PMD for Java (if not in project pom.xml):

```bash
cd /opt
sudo wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.0.0/pmd-dist-7.0.0-bin.zip
sudo unzip pmd-dist-7.0.0-bin.zip
sudo ln -s /opt/pmd-bin-7.0.0/bin/pmd /usr/local/bin/pmd
```

### 2.3 Obsidian

Download from https://obsidian.md/download — use `.deb` for Ubuntu or AppImage.

```bash
# If .deb
sudo dpkg -i obsidian_*.deb

# If AppImage
chmod +x Obsidian-*.AppImage
mv Obsidian-*.AppImage ~/Applications/
```

Open Obsidian → "Open folder as vault" → navigate to `/home/v/Dev/ttt-expert-v1/expert-system/vault/`.

**No Obsidian plugins are required.** The MCP server for Claude Code is a standalone npm package (see 2.5). Obsidian is used purely as a human viewing/editing tool.

**Recommended Obsidian settings:**
- Files & Links → New link format: "Shortest path when possible"
- Files & Links → Use Wikilinks: Enabled
- Core plugins: Enable Graph View, Backlinks, Tags

### 2.4 QMD (Quick Markdown Search)

```bash
# Install
bun install -g https://github.com/tobi/qmd
qmd --version

# Set up vault collection
qmd collection add /home/v/Dev/ttt-expert-v1/expert-system/vault/ --name expert-vault
qmd context add qmd://expert-vault "Expert system knowledge base for legacy web app investigation"

# Build embeddings (first run downloads ~330MB model)
qmd embed

# Start MCP daemon
qmd mcp --http --daemon
qmd status    # should show MCP: running
```

Register QMD with Claude Code:

```bash
claude mcp add --transport http qmd-search http://localhost:8181
```

### 2.5 Obsidian Vault MCP Server (bitbonsai/mcp-obsidian)

This is a standalone npm MCP server — NOT an Obsidian plugin. It gives Claude Code frontmatter-aware read/write/search access to the vault. Obsidian does not need to be running for it to work.

```bash
claude mcp add-json obsidian --scope user '{
  "type": "stdio",
  "command": "npx",
  "args": [
    "@mauricio.wolff/mcp-obsidian@latest",
    "/home/v/Dev/ttt-expert-v1/expert-system/vault"
  ]
}'
```

This provides 11 tools: `read_note`, `write_note`, `delete_note`, `move_note`, `list_directory`, `read_multiple_notes`, `search_notes`, `get_frontmatter`, `update_frontmatter`, `get_notes_info`, `manage_tags`.

Key features: safe YAML frontmatter handling, write modes (overwrite/append/prepend), tag management, token-optimized responses (40-60% smaller), path traversal protection.

### 2.6 SQLite MCP Server

```bash
npm install -g @bytebase/dbhub
```

Register with Claude Code:

```bash
claude mcp add --transport stdio sqlite-analytics -- \
  npx @bytebase/dbhub --dsn "sqlite:///home/v/Dev/ttt-expert-v1/expert-system/analytics.db"
```

Alternative — @anthropic/mcp-server-sqlite:

```bash
npm install -g @anthropic/mcp-server-sqlite

claude mcp add --transport stdio sqlite-analytics -- \
  npx @anthropic/mcp-server-sqlite /home/v/Dev/ttt-expert-v1/expert-system/analytics.db
```

---

## 3. Directory Setup

```bash
PROJECT=/home/v/Dev/ttt-expert-v1

# Create structure
mkdir -p $PROJECT/expert-system/{vault,scripts,repos,output}

# Vault subdirectories
mkdir -p $PROJECT/expert-system/vault/{architecture,modules,patterns,debt,decisions,investigations,analysis,branches}
mkdir -p $PROJECT/expert-system/vault/external/{requirements,designs,tickets,existing-tests}
mkdir -p $PROJECT/expert-system/vault/exploration/{ui-flows,api-findings,data-findings}
```

---

## 4. Configuration Files

### 4.1 Implementation Prompt

```bash
cp case1-implementation-prompt.md /home/v/Dev/ttt-expert-v1/CLAUDE.md
```

### 4.2 Config File

Create `/home/v/Dev/ttt-expert-v1/expert-system/config.yaml`:

```yaml
session:
  delay_minutes: 30
  max_duration_minutes: 240

phase:
  current: "knowledge_acquisition"
  generation_allowed: false

thresholds:
  knowledge_coverage_target: 0.8
  note_quality_min_links: 2

repos:
  local_clone_path: "expert-system/repos/"
  default_branch: "release/2.1"
  additional_branches: [stage]

testing_dev_envs:
  primary:
    name: "timemachine"
  secondary:
    name: "qa-1"

testing_prod_envs:
  primary:
    name: "stage"

current_sprint: 15
```

> **Note:** Environment parameters (URL, API base, DB host, API tokens) are resolved from `config/ttt/envs/<name>.yml` files — only the env name is needed in config.yaml.

### 4.3 Mission Directive

Create `/home/v/Dev/ttt-expert-v1/expert-system/MISSION_DIRECTIVE.md`:

```markdown
# Mission Directive

## Global Goal
Build comprehensive knowledge base of [PROJECT NAME] and generate
test plans and test cases for all major features.

## Project Context
[Describe the application, business domain, critical areas, known pain points]

## Priority Areas
1. [Most critical area first]
2. [Second priority]
3. ...

## Information Sources

### Codebase
- **GitLab repo**: [URL]
- **Default branch**: develop
- **Key branches**: [list]

### Documentation
- **Confluence space**: [space key / URL]
  - Key pages: [list]
  - Note: Some pages may be outdated

### Designs
- **Figma project**: [URL]

### Test Management
- **Qase project**: [project key]
  - Note: Check before generating — avoid duplication

### Tickets
- **GitLab issues**: [project path]
  - Key labels: [list]

### Additional Documents
- **Google Doc — [name]**: [URL]
- **Google Sheet — [name]**: [URL]

### Testing Environments
- **Primary**: [URL] — version [X.Y]
- **Secondary**: [URL] — version [X.Y]

## Output Requirements
- Test plans as XLSX (one per major module/feature area)
- Test cases as XLSX (detailed, executable)
- Compatible with Google Sheets import
- Must complement (not duplicate) existing Qase tests
```

---

## 5. MCP Configuration Summary

After all installation, verify:

```bash
claude mcp list
```

Expected (25+ servers):

```
obsidian              stdio   @mauricio.wolff/mcp-obsidian  (vault access)
qmd-search            http    http://localhost:8181          (semantic search)
sqlite-analytics      stdio   @bytebase/dbhub               (structured data)
playwright            ...     (pre-installed)
postgresql            ...     (pre-installed)
gitlab                ...     (pre-installed)
confluence            ...     (pre-installed)
figma                 ...     (pre-installed)
qase                  ...     (pre-installed, user scope)
swagger-qa1-ttt-api   ...     (21 swagger servers total)
swagger-qa1-ttt-test  ...     naming: swagger-{env}-{service}-{group}
swagger-tm-ttt-api    ...     env: qa1, tm, stage
...                           service: ttt, vacation, calendar, email
                              group: api, test, default
```

> **Note:** 21 Swagger MCP servers cover 3 environments × 7 service/group combinations. See `.claude/skills/swagger-api/SKILL.md` for the full list and naming convention.

---

## 6. VS Code Extensions

VS Code runs directly on the Ubuntu server. Install for output viewing and knowledge base monitoring:

```bash
# XLSX viewing
code --install-extension GrapeCity.gc-excelviewer

# SQLite browsing
code --install-extension qwtel.sqlite-viewer

# Markdown knowledge base (Obsidian-like graph in VS Code)
code --install-extension foam.foam-vscode
code --install-extension yzhang.markdown-all-in-one
code --install-extension bierner.markdown-mermaid

# Git/code browsing
code --install-extension eamodio.gitlens

# Config editing
code --install-extension redhat.vscode-yaml
```

---

## 7. Verification Checklist

```bash
PROJECT=/home/v/Dev/ttt-expert-v1

# System dependencies
java --version                          # OpenJDK 17+
mvn --version                           # Maven 3.x
python3 --version                       # Python 3.10+
python3 -c "import openpyxl; print('OK')"
node --version                          # Node 18+
bun --version                           # Bun 1.0+

# Claude Code
claude --version

# MCPs registered
claude mcp list                         # all MCPs visible

# QMD running
qmd status                              # MCP: running
qmd collection list                     # expert-vault listed

# Analysis tools
which eslint madge jscpd ts-prune cr

# Workspace structure
ls $PROJECT/expert-system/              # vault/ scripts/ repos/ output/
ls $PROJECT/expert-system/vault/        # architecture/ modules/ etc.

# Config files
cat $PROJECT/expert-system/config.yaml
cat $PROJECT/expert-system/MISSION_DIRECTIVE.md
cat $PROJECT/CLAUDE.md

# Test mcp-obsidian (quick — list vault root)
# Start a Claude Code session and ask: "list files in the vault"

# Test QMD (empty vault, should not error)
qmd search "test" -c expert-vault
```

---

## 8. Operating the Expert System

### 8.1 Starting a Session

1. Verify QMD daemon: `qmd status`
2. Review/edit `expert-system/config.yaml` if needed
3. Review/edit `expert-system/MISSION_DIRECTIVE.md` if priorities changed
4. Start: `cd /home/v/Dev/ttt-expert-v1 && claude`
5. Claude reads CLAUDE.md + config.yaml, follows session protocol
6. Review and approve Claude's proposed plan

### 8.2 During a Session

Your role: approve/redirect plans, answer context questions, approve state-changing actions on test envs, request specific deep dives.

Watch for: notes without wikilinks, full file reads when QMD would suffice, notes too long, raw data instead of insights, generation attempted before Phase A is sufficient.

### 8.3 Between Sessions

- **Obsidian**: Browse knowledge base, graph view, edit notes
- **Read `_SESSION_BRIEFING.md`** for progress
- **Edit `_INVESTIGATION_AGENDA.md`** to adjust priorities
- **Edit `config.yaml`** to change delay, phase, branches
- **Edit `MISSION_DIRECTIVE.md`** to add context or shift goals
- **Add manual notes** to vault — Claude discovers via QMD
- **Review XLSX** output in VS Code or LibreOffice

### 8.4 Transitioning Phase A → Phase B

When knowledge acquisition is sufficient:

1. Review `_KNOWLEDGE_COVERAGE.md`
2. Browse vault in Obsidian graph view
3. Check module_health:
   ```bash
   sqlite3 /home/v/Dev/ttt-expert-v1/expert-system/analytics.db \
     "SELECT module, tech_debt_score, last_analyzed FROM module_health ORDER BY last_analyzed"
   ```
4. Edit config.yaml:
   ```yaml
   phase:
     current: "generation"
     generation_allowed: true
   ```

### 8.5 Session Delay Management

`session.delay_minutes` in config.yaml controls minimum gap between sessions. Adjust based on MAX plan usage:
- Default 30 — conservative steady usage
- Increase to 60-120 — spread across more hours
- Decrease to 10-15 — intensive bursts

---

## 9. Monitoring and Maintenance

### Vault Health (weekly)
```bash
find /home/v/Dev/ttt-expert-v1/expert-system/vault -name "*.md" | wc -l
qmd status         # check embed freshness
qmd embed          # incremental re-embed
qmd embed -f       # force full rebuild
```

### SQLite Health
```bash
sqlite3 /home/v/Dev/ttt-expert-v1/expert-system/analytics.db "
  SELECT 'analysis_runs', count(*) FROM analysis_runs
  UNION ALL SELECT 'module_health', count(*) FROM module_health
  UNION ALL SELECT 'design_issues', count(*) FROM design_issues
  UNION ALL SELECT 'external_refs', count(*) FROM external_refs
  UNION ALL SELECT 'exploration_findings', count(*) FROM exploration_findings
  UNION ALL SELECT 'test_case_tracking', count(*) FROM test_case_tracking;
"
```

### Backup
```bash
# Git for vault (recommended)
cd /home/v/Dev/ttt-expert-v1/expert-system/vault
git init   # first time
git add -A && git commit -m "Snapshot $(date +%Y-%m-%d)"

# Full backup
tar -czf ~/ttt-expert-backup-$(date +%Y%m%d).tar.gz \
  /home/v/Dev/ttt-expert-v1/expert-system/
```

### QMD Auto-start
Add to `~/.bashrc`:
```bash
if ! qmd status 2>/dev/null | grep -q "MCP: running"; then
  qmd mcp --http --daemon
fi
```

---

## 10. Troubleshooting

### mcp-obsidian Issues
- Verify: `npx @mauricio.wolff/mcp-obsidian@latest /home/v/Dev/ttt-expert-v1/expert-system/vault` (should start without error, Ctrl+C to stop)
- Check MCP registration: `claude mcp get obsidian`
- Test in Claude Code: ask "list files in the vault"

### QMD Returns No Results
- `qmd collection list` — verify collection
- `qmd status` — check embeddings count
- `qmd embed -f` — force rebuild
- Test: `qmd search "test" -c expert-vault`

### SQLite MCP Errors
- `ls /home/v/Dev/ttt-expert-v1/expert-system/analytics.db`
- `sqlite3 /home/v/Dev/ttt-expert-v1/expert-system/analytics.db ".tables"`
- Claude creates schema on first session; or run SQL from CLAUDE.md Section 6 manually

### Maven/Java Analysis
- `java --version` and `mvn --version`
- `mvn dependency:tree -f <path-to-pom>`

### XLSX Generation
- `python3 -c "import openpyxl"`
- Check `expert-system/output/` exists

### High Token Usage
- Is Claude reading full files instead of QMD search?
- Are shell wrappers compressing output?
- Use `/compact` if context fills up

---

## 11. Architecture Rationale

**Why two phases?** Complex entangled project — generating tests without deep understanding produces shallow, incomplete results.

**Why Obsidian + QMD + SQLite?** Obsidian: qualitative knowledge with wikilinks. QMD: semantic search with 96% token savings. SQLite: structured metrics queryable with SQL.

**Why mcp-obsidian (bitbonsai)?** Standalone npm server, no Obsidian plugin needed, frontmatter-aware, tag management, token-optimized responses, active maintenance (v0.8.1, 472 stars). Obsidian remains a pure human viewing tool.

**Why XLSX?** Best balance of local editing (LibreOffice/VS Code), structure (multi-sheet), and Google Sheets import compatibility.

**Why clone-and-analyze?** Static analysis tools work on source. No runtime needed. Maven only for dependency resolution.

**Why configurable delay?** MAX plan has no programmatic usage API. Simple delay provides reliable pacing.

---

## 12. Quick Start Checklist

```
[ ] Install Java SDK: sudo apt install openjdk-17-jdk
[ ] Install Maven: sudo apt install maven
[ ] Install Python + openpyxl: pip3 install openpyxl pandas
[ ] Install Bun: curl -fsSL https://bun.sh/install | bash
[ ] Install analysis tools: npm install -g eslint madge jscpd ts-prune complexity-report
[ ] Install Obsidian, open vault at .../expert-system/vault/
[ ] Install QMD, create collection, embed, start daemon
[ ] Register mcp-obsidian: claude mcp add-json obsidian ...
[ ] Register QMD MCP: claude mcp add --transport http qmd-search ...
[ ] Register SQLite MCP: claude mcp add --transport stdio sqlite-analytics ...
[ ] Create directory structure (Section 3)
[ ] Create config.yaml (Section 4.2)
[ ] Create MISSION_DIRECTIVE.md (Section 4.3)
[ ] Copy implementation prompt as CLAUDE.md at project root
[ ] Install VS Code extensions (Section 6)
[ ] Run verification checklist (Section 7)
[ ] Start: cd /home/v/Dev/ttt-expert-v1 && claude
```

---

## Component Reference

| Component | Install |
|-----------|---------|
| Java SDK | `sudo apt install openjdk-17-jdk` |
| Maven | `sudo apt install maven` |
| Python 3 + openpyxl | `sudo apt install python3; pip3 install openpyxl pandas` |
| Bun | `curl -fsSL https://bun.sh/install \| bash` |
| Obsidian | https://obsidian.md/download |
| mcp-obsidian | `claude mcp add-json obsidian ...` (npx, no pre-install) |
| QMD | `bun install -g https://github.com/tobi/qmd` |
| SQLite MCP | `npm install -g @bytebase/dbhub` |
| ESLint | `npm install -g eslint` |
| madge | `npm install -g madge` |
| jscpd | `npm install -g jscpd` |
| ts-prune | `npm install -g ts-prune` |
