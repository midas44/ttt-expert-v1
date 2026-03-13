#!/usr/bin/env bash
#
# coverage-report.sh — Phase A coverage estimation for the expert system
#
# Queries SQLite + counts vault notes to produce objective metrics:
# - Module health completeness
# - External refs by source type
# - Exploration findings by method
# - Vault note count by directory
# - Wikilink density
# - Composite coverage score
#
# Usage:
#   ./coverage-report.sh              # default: expert-system/analytics.db
#   ./coverage-report.sh /path/to.db  # custom database path
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DB="${1:-$PROJECT_ROOT/expert-system/analytics.db}"
VAULT_DIR="$PROJECT_ROOT/expert-system/vault"

if [[ ! -f "$DB" ]]; then
    echo "Database not found: $DB"
    echo "Run at least one session first to create the database."
    exit 1
fi

echo "═══════════════════════════════════════════════════"
echo "  Expert System — Phase A Coverage Report"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════"
echo ""

# ── Module Health ────────────────────────────────────────────────────────────
echo "── Module Health ──"
sqlite3 "$DB" <<'SQL'
.mode column
.headers on
SELECT
    'Total modules' AS metric,
    count(*) AS value
FROM module_health
UNION ALL
SELECT
    'Complete (complexity + tech_debt)',
    count(*)
FROM module_health
WHERE complexity_avg IS NOT NULL AND tech_debt_score IS NOT NULL;
SQL
echo ""

module_total=$(sqlite3 "$DB" "SELECT count(*) FROM module_health;")
module_complete=$(sqlite3 "$DB" "SELECT count(*) FROM module_health WHERE complexity_avg IS NOT NULL AND tech_debt_score IS NOT NULL;")

# ── External References ──────────────────────────────────────────────────────
echo "── External References by Source ──"
sqlite3 "$DB" <<'SQL'
.mode column
.headers on
SELECT
    source_type,
    count(*) AS count
FROM external_refs
GROUP BY source_type
ORDER BY count DESC;
SQL
echo ""

source_types=$(sqlite3 "$DB" "SELECT count(DISTINCT source_type) FROM external_refs;")
target_source_types=4  # Confluence, GitLab, Figma, Qase

# ── Exploration Findings ─────────────────────────────────────────────────────
echo "── Exploration Findings by Method ──"
sqlite3 "$DB" <<'SQL'
.mode column
.headers on
SELECT
    method,
    count(*) AS count
FROM exploration_findings
GROUP BY method
ORDER BY count DESC;
SQL
echo ""

exploration_methods=$(sqlite3 "$DB" "SELECT count(DISTINCT method) FROM exploration_findings;")
target_methods=3  # UI, API, DB

# ── Design Issues ────────────────────────────────────────────────────────────
echo "── Design Issues ──"
sqlite3 "$DB" <<'SQL'
.mode column
.headers on
SELECT
    'Total issues' AS metric,
    count(*) AS value
FROM design_issues;
SQL
echo ""

# ── Vault Notes ──────────────────────────────────────────────────────────────
echo "── Vault Notes by Directory ──"
if [[ -d "$VAULT_DIR" ]]; then
    total_notes=0
    while IFS= read -r dir; do
        rel="${dir#$VAULT_DIR/}"
        count=$(find "$dir" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l)
        if [[ "$count" -gt 0 ]]; then
            printf "  %-40s %d\n" "$rel/" "$count"
            total_notes=$((total_notes + count))
        fi
    done < <(find "$VAULT_DIR" -type d 2>/dev/null | sort)
    echo "  ────────────────────────────────────────────"
    printf "  %-40s %d\n" "TOTAL" "$total_notes"
else
    echo "  Vault directory not found: $VAULT_DIR"
    total_notes=0
fi
echo ""

# ── Wikilink Density ─────────────────────────────────────────────────────────
echo "── Wikilink Density ──"
if [[ -d "$VAULT_DIR" && "$total_notes" -gt 0 ]]; then
    total_links=$(grep -roh '\[\[.*\]\]' "$VAULT_DIR" --include='*.md' 2>/dev/null | wc -l)
    avg_links=$(python3 -c "print(f'{$total_links / $total_notes:.2f}')")
    echo "  Total wikilinks:     $total_links"
    echo "  Notes:               $total_notes"
    echo "  Avg links per note:  $avg_links"
else
    total_links=0
    avg_links="0.00"
    echo "  No notes to analyze."
fi
echo ""

# ── Composite Score ──────────────────────────────────────────────────────────
echo "── Composite Coverage Score ──"
python3 - "$module_total" "$module_complete" "$source_types" "$target_source_types" \
           "$exploration_methods" "$target_methods" "$avg_links" <<'PYTHON'
import sys

module_total     = int(sys.argv[1])
module_complete  = int(sys.argv[2])
source_types     = int(sys.argv[3])
target_sources   = int(sys.argv[4])
expl_methods     = int(sys.argv[5])
target_methods   = int(sys.argv[6])
avg_links        = float(sys.argv[7])
target_links     = 2.0

# Component scores (0.0 – 1.0, capped at 1.0)
module_score  = min(module_complete / module_total, 1.0) if module_total > 0 else 0.0
source_score  = min(source_types / target_sources, 1.0)
method_score  = min(expl_methods / target_methods, 1.0)
link_score    = min(avg_links / target_links, 1.0)

# Weighted composite
composite = (
    0.30 * module_score +
    0.25 * source_score +
    0.25 * method_score +
    0.20 * link_score
)

print(f"  Module health completeness:  {module_score:6.1%}  (weight 30%)")
print(f"  External source coverage:    {source_score:6.1%}  (weight 25%)")
print(f"  Exploration method coverage: {method_score:6.1%}  (weight 25%)")
print(f"  Wikilink density:            {link_score:6.1%}  (weight 20%)")
print(f"  ─────────────────────────────────────")
print(f"  COMPOSITE SCORE:             {composite:6.1%}")
print()
if composite >= 0.8:
    print("  ✓ Phase A target (≥80%) REACHED — consider transitioning to Phase B")
else:
    print(f"  ○ Phase A target (≥80%) not yet reached — {0.8 - composite:.0%} gap remaining")
PYTHON
echo ""
