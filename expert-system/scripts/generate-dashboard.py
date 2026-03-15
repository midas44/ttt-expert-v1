#!/usr/bin/env python3
"""Generate HTML dashboard from runner-state.json."""

import json
import sys
from datetime import datetime
from pathlib import Path


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def load_state(state_file):
    with open(state_file) as f:
        return json.load(f)


def generate_html(state, output_file):
    sessions = state.get('sessions', [])
    if not sessions:
        return

    # Phase breakdown
    phases = {}
    for s in sessions:
        phase = s.get('phase', 'unknown')
        if phase not in phases:
            phases[phase] = {'count': 0, 'ok': 0, 'failed': 0, 'timeout': 0,
                             'total_sec': 0, 'total_turns': 0,
                             'total_input': 0, 'total_output': 0,
                             'total_cache_read': 0, 'total_cache_create': 0,
                             'total_vault_files': 0}
        p = phases[phase]
        p['count'] += 1
        if s['exit_code'] == 0:
            p['ok'] += 1
        elif s['exit_code'] == 124:
            p['timeout'] += 1
        else:
            p['failed'] += 1
        p['total_sec'] += s.get('duration_sec', 0)
        p['total_turns'] += s.get('num_turns', 0)
        p['total_vault_files'] += s.get('vault_changes', {}).get('files_changed', 0)
        for mu in s.get('models', {}).values():
            p['total_input'] += mu.get('input', 0)
            p['total_output'] += mu.get('output', 0)
            p['total_cache_read'] += mu.get('cache_read', 0)
            p['total_cache_create'] += mu.get('cache_create', 0)

    # Overall stats
    total_sessions = len(sessions)
    total_ok = sum(1 for s in sessions if s['exit_code'] == 0)
    total_duration = sum(s.get('duration_sec', 0) for s in sessions)
    total_turns = sum(s.get('num_turns', 0) for s in sessions)
    total_output = sum(mu.get('output', 0) for s in sessions for mu in s.get('models', {}).values())
    total_cache_read = sum(mu.get('cache_read', 0) for s in sessions for mu in s.get('models', {}).values())
    total_vault_files = sum(s.get('vault_changes', {}).get('files_changed', 0) for s in sessions)
    avg_duration = total_duration / total_sessions if total_sessions else 0

    # Model usage
    model_totals = {}
    for s in sessions:
        for model, mu in s.get('models', {}).items():
            if model not in model_totals:
                model_totals[model] = {'input': 0, 'output': 0, 'cache_read': 0,
                                       'cache_create': 0, 'sessions': 0}
            mt = model_totals[model]
            mt['input'] += mu.get('input', 0)
            mt['output'] += mu.get('output', 0)
            mt['cache_read'] += mu.get('cache_read', 0)
            mt['cache_create'] += mu.get('cache_create', 0)
            mt['sessions'] += 1

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # --- HTML ---
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="300">
<title>Expert System Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Courier New', 'Liberation Mono', monospace;
         margin: 20px; background: #1d1f21; color: #c5c8c6; font-size: 14px; }}
  h1 {{ color: #b5bd68; margin-bottom: 4px; font-size: 1.4em; }}
  h2 {{ color: #81a2be; border-bottom: 1px solid #373b41; padding-bottom: 4px;
       font-size: 1.1em; margin-top: 24px; }}
  .updated {{ color: #969896; font-size: 0.85em; margin-bottom: 16px; }}
  .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }}
  .card {{ background: #282a2e; border: 1px solid #373b41; border-radius: 4px;
           padding: 10px 14px; min-width: 130px; }}
  .card .value {{ font-size: 1.5em; font-weight: bold; color: #b5bd68; }}
  .card .label {{ font-size: 0.8em; color: #969896; margin-top: 2px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 0.85em; }}
  th {{ background: #282a2e; color: #81a2be; text-align: left; padding: 6px 10px;
       border-bottom: 1px solid #373b41; position: sticky; top: 0; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #282a2e; }}
  tr:hover {{ background: #282a2e; }}
  .ok {{ color: #b5bd68; }}
  .fail {{ color: #cc6666; }}
  .timeout {{ color: #de935f; }}
  .tokens {{ color: #8abeb7; }}
  .muted {{ color: #969896; }}
  .right {{ text-align: right; }}
  .phase-tag {{ display: inline-block; padding: 1px 6px; border-radius: 2px;
               font-size: 0.8em; }}
  .phase-knowledge_acquisition {{ background: #373b41; color: #b5bd68; }}
  .phase-generation {{ background: #373b41; color: #b294bb; }}
  .phase-unknown {{ background: #373b41; color: #969896; }}
  .detail {{ max-width: 600px; color: #969896; font-size: 0.85em; }}
  .detail .files {{ color: #8abeb7; }}
  .expandable {{ cursor: pointer; }}
  .expandable:hover {{ color: #c5c8c6; }}
  details summary {{ cursor: pointer; color: #81a2be; }}
  details summary:hover {{ color: #c5c8c6; }}
  .note {{ color: #969896; font-size: 0.8em; margin: 8px 0; font-style: italic; }}
</style>
</head>
<body>
<h1>Expert System Dashboard</h1>
<div class="updated">Updated: {now} | Auto-refreshes every 5 min</div>

<div class="cards">
  <div class="card">
    <div class="value">{total_sessions}</div>
    <div class="label">Sessions</div>
  </div>
  <div class="card">
    <div class="value ok">{total_ok}</div>
    <div class="label">Successful</div>
  </div>
  <div class="card">
    <div class="value">{avg_duration / 60:.0f}m</div>
    <div class="label">Avg Duration</div>
  </div>
  <div class="card">
    <div class="value">{total_turns:,}</div>
    <div class="label">Turns</div>
  </div>
  <div class="card">
    <div class="value tokens">{fmt_tokens(total_output)}</div>
    <div class="label">Output Tokens</div>
  </div>
  <div class="card">
    <div class="value tokens">{fmt_tokens(total_cache_read)}</div>
    <div class="label">Cache Read</div>
  </div>
  <div class="card">
    <div class="value">{total_vault_files}</div>
    <div class="label">Vault Files Touched</div>
  </div>
  <div class="card">
    <div class="value">{total_duration / 3600:.1f}h</div>
    <div class="label">Wall Time</div>
  </div>
</div>

<h2>Phase Summary</h2>
<table>
<tr><th>Phase</th><th>Sessions</th><th>OK</th><th>Fail</th><th>Timeout</th><th>Duration</th><th>Avg</th><th>Turns</th><th>Output</th><th>Cache Read</th><th>Vault Files</th></tr>
"""

    for phase, p in sorted(phases.items()):
        avg_p = p['total_sec'] / p['count'] / 60 if p['count'] else 0
        html += f"""<tr>
  <td><span class="phase-tag phase-{phase}">{phase}</span></td>
  <td>{p['count']}</td><td class="ok">{p['ok']}</td>
  <td class="fail">{p['failed']}</td><td class="timeout">{p['timeout']}</td>
  <td>{p['total_sec'] / 3600:.1f}h</td><td>{avg_p:.0f}m</td>
  <td>{p['total_turns']:,}</td>
  <td class="right tokens">{fmt_tokens(p['total_output'])}</td>
  <td class="right tokens">{fmt_tokens(p['total_cache_read'])}</td>
  <td>{p['total_vault_files']}</td>
</tr>"""

    html += """
</table>

<h2>Model Usage</h2>
<table>
<tr><th>Model</th><th>Sessions</th><th>Input</th><th>Output</th><th>Cache Read</th><th>Cache Create</th></tr>
"""

    for model, mt in sorted(model_totals.items()):
        html += f"""<tr>
  <td>{model}</td><td>{mt['sessions']}</td>
  <td class="right tokens">{fmt_tokens(mt['input'])}</td>
  <td class="right tokens">{fmt_tokens(mt['output'])}</td>
  <td class="right tokens">{fmt_tokens(mt['cache_read'])}</td>
  <td class="right tokens">{fmt_tokens(mt['cache_create'])}</td>
</tr>"""

    html += """
</table>
<p class="note">Note: Per-tool MCP usage is not available in claude -p output format. Turns count reflects total tool calls + responses.</p>

<h2>Session History</h2>
<table>
<tr><th>#</th><th>Phase</th><th>Time</th><th>Dur</th><th>Status</th><th>Turns</th><th>Output</th><th>Vault</th><th>Details</th></tr>
"""

    for s in reversed(sessions):
        exit_code = s['exit_code']
        if exit_code == 0:
            status = '<span class="ok">OK</span>'
        elif exit_code == 124:
            status = '<span class="timeout">TIMEOUT</span>'
        else:
            status = f'<span class="fail">FAIL({exit_code})</span>'

        phase = s.get('phase', 'unknown')
        ts = s.get('timestamp', '')[:16].replace('T', ' ')
        dur = s.get('duration_sec', 0)
        turns = s.get('num_turns', '')
        out = sum(mu.get('output', 0) for mu in s.get('models', {}).values())

        # Vault changes
        vc = s.get('vault_changes', {})
        vault_count = vc.get('files_changed', 0)
        vault_files = vc.get('files', [])

        # Build detail cell
        summary = esc(s.get('result_summary', ''))
        summary_first = summary.split('\n')[0][:150]

        detail_parts = []
        if vault_files:
            file_list = ', '.join(f.split('/')[-1].replace('.md', '') for f in vault_files[:8])
            if len(vault_files) > 8:
                file_list += f' +{len(vault_files) - 8} more'
            detail_parts.append(f'<span class="files">{vault_count} files: {file_list}</span>')
        if summary_first:
            detail_parts.append(summary_first)

        detail_html = '<br>'.join(detail_parts) if detail_parts else '<span class="muted">-</span>'

        html += f"""<tr>
  <td>{s['session']}</td>
  <td><span class="phase-tag phase-{phase}">{phase[:5]}</span></td>
  <td>{ts}</td>
  <td>{dur // 60}m</td>
  <td>{status}</td>
  <td>{turns}</td>
  <td class="right tokens">{fmt_tokens(out)}</td>
  <td>{vault_count or '-'}</td>
  <td class="detail">{detail_html}</td>
</tr>"""

    html += """
</table>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent.parent
    state_file = project_root / 'expert-system' / 'logs' / 'runner-state.json'
    output_file = project_root / 'expert-system' / 'logs' / 'dashboard.html'

    if not state_file.exists():
        print(f"State file not found: {state_file}", file=sys.stderr)
        sys.exit(1)

    state = load_state(state_file)
    generate_html(state, output_file)
    print(f"Dashboard generated: {output_file}")
