#!/usr/bin/env node
/**
 * sync-postgres-mcp.js
 *
 * Reads environment definitions from config.yaml + config/ttt/envs/<name>.yml
 * and generates/updates postgres MCP server entries in .claude/.mcp.json.
 *
 * Usage:
 *   node .claude/scripts/sync-postgres-mcp.js           # preview changes (dry-run)
 *   node .claude/scripts/sync-postgres-mcp.js --apply    # apply to .mcp.json
 *
 * Environment name → MCP server name mapping:
 *   timemachine → postgres-tm
 *   qa-1        → postgres-qa1
 *   qa-2        → postgres-qa2
 *   stage       → postgres-stage
 *   dev-new     → postgres-devnew
 *   preprod     → postgres-preprod
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '../..');
const CONFIG_YAML = path.join(PROJECT_ROOT, 'expert-system/config.yaml');
const ENVS_DIR = path.join(PROJECT_ROOT, 'config/ttt/envs');
const MCP_JSON = path.join(PROJECT_ROOT, '.claude/.mcp.json');
const UVX_PATH = '/home/v/.local/bin/uvx';

const KEEPALIVE_PARAMS = 'connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3';

// Simple env-name → short-name mapping
const SHORT_NAMES = {
  'timemachine': 'tm',
  'qa-1': 'qa1',
  'qa-2': 'qa2',
  'stage': 'stage',
  'dev-new': 'devnew',
  'preprod': 'preprod',
};

function shortName(envName) {
  return SHORT_NAMES[envName] || envName.replace(/[^a-z0-9]/g, '');
}

// Parse simple YAML (key: value or key: "value") — enough for our env files
function parseSimpleYaml(text) {
  const result = {};
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const match = trimmed.match(/^(\w+)\s*:\s*"?([^"]*)"?\s*$/);
    if (match) {
      result[match[1]] = match[2];
    }
  }
  return result;
}

// Extract env names from config.yaml
function getEnvNames() {
  const text = fs.readFileSync(CONFIG_YAML, 'utf8');
  const names = new Set();
  // Match lines like:   name: "qa-1"
  for (const match of text.matchAll(/name:\s*"([^"]+)"/g)) {
    names.add(match[1]);
  }
  return [...names];
}

// Build MCP server entry for a given env
function buildPostgresEntry(envConfig) {
  const host = envConfig.dbHost;
  const port = envConfig.dbPort || '5433';
  const db = envConfig.initialDatabase || 'ttt';
  const user = envConfig.dbUsername || 'ttt';
  const password = envConfig.dbPassword || '';
  const uri = `postgresql://${user}:${password}@${host}:${port}/${db}?${KEEPALIVE_PARAMS}`;

  return {
    type: 'stdio',
    command: UVX_PATH,
    args: ['postgres-mcp', '--access-mode=restricted'],
    env: {
      DATABASE_URI: uri,
      NO_PROXY: host,
      no_proxy: host,
      HTTP_PROXY: '',
      HTTPS_PROXY: '',
    },
  };
}

function main() {
  const apply = process.argv.includes('--apply');

  // 1. Get env names from config.yaml
  const envNames = getEnvNames();
  console.log(`Environments in config.yaml: ${envNames.join(', ')}`);

  // 2. Read env files and build entries
  const newEntries = {};
  for (const name of envNames) {
    const envFile = path.join(ENVS_DIR, `${name}.yml`);
    if (!fs.existsSync(envFile)) {
      console.warn(`  SKIP ${name}: no env file at ${envFile}`);
      continue;
    }
    const envConfig = parseSimpleYaml(fs.readFileSync(envFile, 'utf8'));
    if (!envConfig.dbHost) {
      console.warn(`  SKIP ${name}: no dbHost in env file`);
      continue;
    }
    const serverName = `postgres-${shortName(name)}`;
    newEntries[serverName] = buildPostgresEntry(envConfig);
    console.log(`  ${serverName} → ${envConfig.dbHost}:${envConfig.dbPort || 5433}`);
  }

  if (Object.keys(newEntries).length === 0) {
    console.log('No postgres entries to sync.');
    return;
  }

  // 3. Read current .mcp.json
  const mcpConfig = JSON.parse(fs.readFileSync(MCP_JSON, 'utf8'));

  // 4. Remove old postgres-* entries
  const removed = [];
  for (const key of Object.keys(mcpConfig.mcpServers)) {
    if (key.startsWith('postgres-') || key === 'postgres') {
      removed.push(key);
      delete mcpConfig.mcpServers[key];
    }
  }
  if (removed.length) console.log(`\nRemoved old entries: ${removed.join(', ')}`);

  // 5. Add new entries (insert after confluence, before figma for readability)
  const ordered = {};
  for (const [k, v] of Object.entries(mcpConfig.mcpServers)) {
    ordered[k] = v;
    if (k === 'confluence') {
      for (const [nk, nv] of Object.entries(newEntries)) {
        ordered[nk] = nv;
      }
    }
  }
  // If confluence wasn't found, just append
  if (!mcpConfig.mcpServers.confluence) {
    Object.assign(ordered, newEntries);
  }
  mcpConfig.mcpServers = ordered;

  // 6. Write or preview
  const json = JSON.stringify(mcpConfig, null, 2) + '\n';
  if (apply) {
    fs.writeFileSync(MCP_JSON, json);
    console.log(`\nUpdated ${MCP_JSON}`);
    console.log('Restart Claude Code for changes to take effect.');
  } else {
    console.log('\n--- DRY RUN (pass --apply to write) ---');
    // Show just the postgres entries
    for (const [k, v] of Object.entries(newEntries)) {
      console.log(`\n"${k}": ${JSON.stringify(v, null, 2)}`);
    }
  }
}

main();
