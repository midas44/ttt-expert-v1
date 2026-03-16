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

    total_sessions = len(sessions)
    total_ok = sum(1 for s in sessions if s['exit_code'] == 0)
    total_duration = sum(s.get('duration_sec', 0) for s in sessions)
    total_turns = sum(s.get('num_turns', 0) for s in sessions)
    total_output = sum(mu.get('output', 0) for s in sessions for mu in s.get('models', {}).values())
    total_cache_read = sum(mu.get('cache_read', 0) for s in sessions for mu in s.get('models', {}).values())
    total_vault_files = sum(s.get('vault_changes', {}).get('files_changed', 0) for s in sessions)
    avg_duration = total_duration / total_sessions if total_sessions else 0

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

    # GitHub Dark Default palette
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>Expert System Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    background: #0d1117;
    color: #e6edf3;
    line-height: 1.5;
    font-size: 14px;
    padding: 24px 32px;
  }}

  .header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #21262d;
  }}
  .header h1 {{
    font-size: 20px;
    font-weight: 600;
    color: #e6edf3;
  }}
  .header .meta {{
    font-size: 12px;
    color: #7d8590;
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  }}

  .metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 8px;
    margin-bottom: 24px;
  }}
  .metric {{
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 12px 16px;
  }}
  .metric .val {{
    font-size: 24px;
    font-weight: 600;
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    line-height: 1.2;
  }}
  .metric .lbl {{
    font-size: 12px;
    color: #7d8590;
    margin-top: 4px;
  }}

  .c-green {{ color: #3fb950; }}
  .c-blue {{ color: #58a6ff; }}
  .c-purple {{ color: #bc8cff; }}
  .c-orange {{ color: #d29922; }}
  .c-red {{ color: #f85149; }}
  .c-cyan {{ color: #39d2c0; }}
  .c-muted {{ color: #7d8590; }}

  .section {{
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 8px;
    margin-top: 16px;
  }}

  .table-wrap {{
    border: 1px solid #21262d;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 16px;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{
    background: #161b22;
    color: #7d8590;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #21262d;
    position: sticky;
    top: 0;
  }}
  td {{
    padding: 6px 12px;
    border-top: 1px solid #21262d;
    color: #e6edf3;
    vertical-align: top;
  }}
  tr:hover td {{ background: #161b22; }}
  .r {{ text-align: right; }}
  .mono {{
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 12px;
  }}

  .label {{
    display: inline-block;
    padding: 1px 7px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid;
  }}
  .l-ok {{ color: #3fb950; border-color: #238636; background: #23863622; }}
  .l-fail {{ color: #f85149; border-color: #da3633; background: #da363322; }}
  .l-timeout {{ color: #d29922; border-color: #9e6a03; background: #9e6a0322; }}
  .l-acq {{ color: #58a6ff; border-color: #1f6feb; background: #1f6feb22; }}
  .l-gen {{ color: #bc8cff; border-color: #8b5cf6; background: #8b5cf622; }}
  .l-unk {{ color: #7d8590; border-color: #30363d; background: #30363d44; }}

  .detail {{
    max-width: 520px;
    color: #7d8590;
    font-size: 12px;
    line-height: 1.4;
  }}
  .detail .files {{
    color: #39d2c0;
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 11px;
  }}

  .note {{
    color: #484f58;
    font-size: 12px;
    margin: 4px 0 16px 0;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>Expert System Dashboard</h1>
  <span class="meta">{now} &middot; auto-refresh 5m</span>
</div>

<div class="metrics">
  <div class="metric">
    <div class="val">{total_sessions}</div>
    <div class="lbl">Sessions</div>
  </div>
  <div class="metric">
    <div class="val c-green">{total_ok}</div>
    <div class="lbl">Successful</div>
  </div>
  <div class="metric">
    <div class="val">{avg_duration / 60:.0f}m</div>
    <div class="lbl">Avg Duration</div>
  </div>
  <div class="metric">
    <div class="val c-blue">{total_turns:,}</div>
    <div class="lbl">Turns</div>
  </div>
  <div class="metric">
    <div class="val c-cyan">{fmt_tokens(total_output)}</div>
    <div class="lbl">Output Tokens</div>
  </div>
  <div class="metric">
    <div class="val c-purple">{fmt_tokens(total_cache_read)}</div>
    <div class="lbl">Cache Read</div>
  </div>
  <div class="metric">
    <div class="val c-orange">{total_vault_files}</div>
    <div class="lbl">Vault Files</div>
  </div>
  <div class="metric">
    <div class="val">{total_duration / 3600:.1f}h</div>
    <div class="lbl">Wall Time</div>
  </div>
</div>

<div class="section">Phase Summary</div>
<div class="table-wrap">
<table>
<tr><th>Phase</th><th>Sessions</th><th>OK</th><th>Fail</th><th>Timeout</th><th>Duration</th><th>Avg</th><th>Turns</th><th class="r">Output</th><th class="r">Cache Read</th><th>Vault</th></tr>
"""

    for phase, p in sorted(phases.items()):
        avg_p = p['total_sec'] / p['count'] / 60 if p['count'] else 0
        l_cls = 'l-acq' if 'acq' in phase else ('l-gen' if 'gen' in phase else 'l-unk')
        label = 'Knowledge Acquisition' if 'acq' in phase else ('Generation' if 'gen' in phase else phase)
        html += f"""<tr>
  <td><span class="label {l_cls}">{label}</span></td>
  <td class="mono">{p['count']}</td>
  <td class="mono c-green">{p['ok']}</td>
  <td class="mono">{p['failed'] or '-'}</td>
  <td class="mono">{p['timeout'] or '-'}</td>
  <td class="mono">{p['total_sec'] / 3600:.1f}h</td>
  <td class="mono">{avg_p:.0f}m</td>
  <td class="mono">{p['total_turns']:,}</td>
  <td class="mono r c-cyan">{fmt_tokens(p['total_output'])}</td>
  <td class="mono r c-purple">{fmt_tokens(p['total_cache_read'])}</td>
  <td class="mono">{p['total_vault_files']}</td>
</tr>"""

    html += """
</table>
</div>

<div class="section">Model Usage</div>
<div class="table-wrap">
<table>
<tr><th>Model</th><th>Sessions</th><th class="r">Input</th><th class="r">Output</th><th class="r">Cache Read</th><th class="r">Cache Create</th></tr>
"""

    for model, mt in sorted(model_totals.items()):
        short = model.replace('claude-', '').replace('-20251001', '')
        html += f"""<tr>
  <td class="mono">{short}</td>
  <td class="mono">{mt['sessions']}</td>
  <td class="mono r">{fmt_tokens(mt['input'])}</td>
  <td class="mono r c-cyan">{fmt_tokens(mt['output'])}</td>
  <td class="mono r c-purple">{fmt_tokens(mt['cache_read'])}</td>
  <td class="mono r">{fmt_tokens(mt['cache_create'])}</td>
</tr>"""

    html += """
</table>
</div>
<p class="note">Per-tool MCP usage not available in claude -p output. Turns = tool calls + responses.</p>

<div class="section">Session History</div>
<div class="table-wrap">
<table>
<tr><th>#</th><th>Phase</th><th>Time</th><th>Duration</th><th>Status</th><th>Turns</th><th class="r">Output</th><th>Vault</th><th>Details</th></tr>
"""

    for s in reversed(sessions):
        exit_code = s['exit_code']
        if exit_code == 0:
            status = '<span class="label l-ok">OK</span>'
        elif exit_code == 124:
            status = '<span class="label l-timeout">TIMEOUT</span>'
        else:
            status = f'<span class="label l-fail">FAIL {exit_code}</span>'

        phase = s.get('phase', 'unknown')
        l_cls = 'l-acq' if 'acq' in phase else ('l-gen' if 'gen' in phase else 'l-unk')
        phase_short = 'Acq' if 'acq' in phase else ('Gen' if 'gen' in phase else '?')
        ts = s.get('timestamp', '')[:16].replace('T', ' ')
        dur = s.get('duration_sec', 0)
        turns = s.get('num_turns', '')
        out = sum(mu.get('output', 0) for mu in s.get('models', {}).values())

        vc = s.get('vault_changes', {})
        vault_count = vc.get('files_changed', 0)
        vault_files = vc.get('files', [])

        summary = esc(s.get('result_summary', ''))
        summary_first = summary.split('\n')[0][:140]

        detail_parts = []
        if vault_files:
            file_list = ', '.join(f.split('/')[-1].replace('.md', '') for f in vault_files[:6])
            if len(vault_files) > 6:
                file_list += f' +{len(vault_files) - 6}'
            detail_parts.append(f'<span class="files">{file_list}</span>')
        if summary_first:
            detail_parts.append(summary_first)

        detail_html = '<br>'.join(detail_parts) if detail_parts else '<span class="c-muted">-</span>'

        html += f"""<tr>
  <td class="mono">{s['session']}</td>
  <td><span class="label {l_cls}">{phase_short}</span></td>
  <td class="mono" style="white-space:nowrap">{ts}</td>
  <td class="mono">{dur // 60}m {dur % 60:02d}s</td>
  <td>{status}</td>
  <td class="mono">{turns}</td>
  <td class="mono r c-cyan">{fmt_tokens(out)}</td>
  <td class="mono">{vault_count or '-'}</td>
  <td class="detail">{detail_html}</td>
</tr>"""

    html += """
</table>
</div>

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
