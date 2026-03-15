#!/usr/bin/env python3
"""Generate HTML dashboard from runner-state.json and session log files."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def fmt_tokens(n):
    """Format token count: 1234567 -> 1.2M, 12345 -> 12.3K"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


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
                             'total_cache_read': 0, 'total_cache_create': 0}
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
        for model, mu in s.get('models', {}).items():
            p['total_input'] += mu.get('input', 0)
            p['total_output'] += mu.get('output', 0)
            p['total_cache_read'] += mu.get('cache_read', 0)
            p['total_cache_create'] += mu.get('cache_create', 0)

    # Overall stats
    total_sessions = len(sessions)
    total_ok = sum(1 for s in sessions if s['exit_code'] == 0)
    total_duration = sum(s.get('duration_sec', 0) for s in sessions)
    total_turns = sum(s.get('num_turns', 0) for s in sessions)
    total_input = sum(mu.get('input', 0) for s in sessions for mu in s.get('models', {}).values())
    total_output = sum(mu.get('output', 0) for s in sessions for mu in s.get('models', {}).values())
    total_cache_read = sum(mu.get('cache_read', 0) for s in sessions for mu in s.get('models', {}).values())
    total_cache_create = sum(mu.get('cache_create', 0) for s in sessions for mu in s.get('models', {}).values())
    avg_duration = total_duration / total_sessions if total_sessions else 0

    # Model usage aggregation
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

    # Per-session token totals for the session table
    def session_tokens(s):
        inp = sum(mu.get('input', 0) for mu in s.get('models', {}).values())
        out = sum(mu.get('output', 0) for mu in s.get('models', {}).values())
        cr = sum(mu.get('cache_read', 0) for mu in s.get('models', {}).values())
        cc = sum(mu.get('cache_create', 0) for mu in s.get('models', {}).values())
        return inp, out, cr, cc

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="300">
<title>Expert System Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         margin: 20px; background: #1a1a2e; color: #e0e0e0; }}
  h1 {{ color: #00d4ff; margin-bottom: 5px; }}
  h2 {{ color: #7b68ee; border-bottom: 1px solid #333; padding-bottom: 5px; }}
  .updated {{ color: #666; font-size: 0.85em; margin-bottom: 20px; }}
  .cards {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 25px; }}
  .card {{ background: #16213e; border-radius: 8px; padding: 15px 20px;
           min-width: 150px; border: 1px solid #333; }}
  .card .value {{ font-size: 1.8em; font-weight: bold; color: #00d4ff; }}
  .card .label {{ font-size: 0.85em; color: #888; margin-top: 2px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; font-size: 0.9em; }}
  th {{ background: #16213e; color: #7b68ee; text-align: left; padding: 8px 12px;
       border-bottom: 2px solid #333; position: sticky; top: 0; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #222; }}
  tr:hover {{ background: #1a1a3e; }}
  .ok {{ color: #4caf50; }}
  .fail {{ color: #f44336; }}
  .timeout {{ color: #ff9800; }}
  .tokens {{ color: #80cbc4; }}
  .phase-tag {{ display: inline-block; padding: 2px 8px; border-radius: 3px;
               font-size: 0.8em; font-weight: bold; }}
  .phase-knowledge_acquisition {{ background: #1b5e20; color: #a5d6a7; }}
  .phase-generation {{ background: #1a237e; color: #9fa8da; }}
  .phase-unknown {{ background: #333; color: #888; }}
  .summary {{ max-width: 500px; white-space: nowrap; overflow: hidden;
             text-overflow: ellipsis; color: #aaa; font-size: 0.85em; }}
  .right {{ text-align: right; }}
</style>
</head>
<body>
<h1>Expert System Dashboard</h1>
<div class="updated">Updated: {now} &middot; Auto-refreshes every 5 minutes</div>

<div class="cards">
  <div class="card">
    <div class="value">{total_sessions}</div>
    <div class="label">Total Sessions</div>
  </div>
  <div class="card">
    <div class="value ok">{total_ok}</div>
    <div class="label">Successful</div>
  </div>
  <div class="card">
    <div class="value">{avg_duration / 60:.0f} min</div>
    <div class="label">Avg Duration</div>
  </div>
  <div class="card">
    <div class="value">{total_turns:,}</div>
    <div class="label">Total Turns</div>
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
    <div class="value">{total_duration / 3600:.1f}h</div>
    <div class="label">Total Wall Time</div>
  </div>
</div>

<h2>Phase Summary</h2>
<table>
<tr><th>Phase</th><th>Sessions</th><th>OK</th><th>Fail</th><th>Timeout</th><th>Duration</th><th>Avg</th><th>Turns</th><th>Input</th><th>Output</th><th>Cache Read</th><th>Cache Create</th></tr>
"""

    for phase, p in sorted(phases.items()):
        avg_p = p['total_sec'] / p['count'] / 60 if p['count'] else 0
        html += f"""<tr>
  <td><span class="phase-tag phase-{phase}">{phase}</span></td>
  <td>{p['count']}</td>
  <td class="ok">{p['ok']}</td>
  <td class="fail">{p['failed']}</td>
  <td class="timeout">{p['timeout']}</td>
  <td>{p['total_sec'] / 3600:.1f}h</td>
  <td>{avg_p:.0f}m</td>
  <td>{p['total_turns']:,}</td>
  <td class="right tokens">{fmt_tokens(p['total_input'])}</td>
  <td class="right tokens">{fmt_tokens(p['total_output'])}</td>
  <td class="right tokens">{fmt_tokens(p['total_cache_read'])}</td>
  <td class="right tokens">{fmt_tokens(p['total_cache_create'])}</td>
</tr>"""

    html += """
</table>

<h2>Model Usage</h2>
<table>
<tr><th>Model</th><th>Sessions</th><th>Input</th><th>Output</th><th>Cache Read</th><th>Cache Create</th></tr>
"""

    for model, mt in sorted(model_totals.items()):
        html += f"""<tr>
  <td>{model}</td>
  <td>{mt['sessions']}</td>
  <td class="right tokens">{fmt_tokens(mt['input'])}</td>
  <td class="right tokens">{fmt_tokens(mt['output'])}</td>
  <td class="right tokens">{fmt_tokens(mt['cache_read'])}</td>
  <td class="right tokens">{fmt_tokens(mt['cache_create'])}</td>
</tr>"""

    html += """
</table>

<h2>Session History</h2>
<table>
<tr><th>#</th><th>Phase</th><th>Time</th><th>Duration</th><th>Status</th><th>Turns</th><th>Output</th><th>Cache Read</th><th>Summary</th></tr>
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
        inp, out, cr, cc = session_tokens(s)
        summary = s.get('result_summary', '')
        summary = summary.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        summary_short = summary.split('\n')[0][:120]

        html += f"""<tr>
  <td>{s['session']}</td>
  <td><span class="phase-tag phase-{phase}">{phase[:5]}</span></td>
  <td>{ts}</td>
  <td>{dur // 60}m {dur % 60}s</td>
  <td>{status}</td>
  <td>{turns}</td>
  <td class="right tokens">{fmt_tokens(out)}</td>
  <td class="right tokens">{fmt_tokens(cr)}</td>
  <td class="summary" title="{summary}">{summary_short}</td>
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
