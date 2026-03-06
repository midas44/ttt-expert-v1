---
name: package-install
description: >
  Install software packages on this Ubuntu machine using any package manager: apt, npm, pip3,
  bun, curl-based installers (bun, nvm, rustup, etc.), wget, git clone + build, or snap.
  Use this skill when the user asks to install anything, mentions "install", "apt install",
  "npm install", "pip install", "pip3 install", "curl install", "bun install", "snap install",
  "wget download", "git clone", or encounters installation errors like network timeouts,
  proxy errors, permission denied, SUID sandbox errors, unsupported engine warnings, or
  "command not found" after install. Also use when the user asks to upgrade Node.js, install
  global CLI tools, set up AppImage apps, or troubleshoot failed installations.
---

# Package Installation on This Machine

## Proxy Requirement

This machine accesses the internet through a local proxy. **All package managers need proxy configuration** or downloads will fail with "network unreachable" / "connection timeout" errors.

- **Proxy address**: `http://127.0.0.1:2080`

### Set proxy globally (recommended before any install session)

```bash
export HTTP_PROXY=http://127.0.0.1:2080
export HTTPS_PROXY=http://127.0.0.1:2080
```

This covers most tools (curl, npm, pip3, wget, git, bun, etc.) for the current shell session.

---

## apt (system packages)

apt uses its own proxy config, not environment variables.

```bash
# One-time install with proxy
sudo apt -o Acquire::http::Proxy="http://127.0.0.1:2080" install <package>

# Or just use sudo apt install if system apt proxy is already configured
sudo apt install <package>
```

### Examples

```bash
sudo apt install unzip curl git build-essential
```

**Note:** Some tools (e.g. bun installer) depend on `unzip` — install it with apt first if missing.

---

## npm (Node.js packages)

### Global install (needs sudo + proxy passthrough)

```bash
sudo HTTP_PROXY=http://127.0.0.1:2080 HTTPS_PROXY=http://127.0.0.1:2080 npm install -g <packages>
```

### Local install (in project)

```bash
export HTTP_PROXY=http://127.0.0.1:2080
export HTTPS_PROXY=http://127.0.0.1:2080
npm install <packages>
```

### Node.js version issues

Current Node.js on this machine is **v18**. Some packages (e.g. eslint v10+) require Node >= 20. Options:

1. **Pin older version**: `npm install -g eslint@8` (compatible with Node 18)
2. **Upgrade Node** via `n`:
   ```bash
   sudo HTTP_PROXY=http://127.0.0.1:2080 HTTPS_PROXY=http://127.0.0.1:2080 npm install -g n
   sudo n 20
   ```

---

## pip3 (Python packages)

System Python is PEP 668 managed — requires `--break-system-packages` for global installs.

```bash
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 <packages>
```

### Examples

```bash
# Multiple packages
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 openpyxl pandas numpy

# Specific version
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 flask==3.0.0

# Upgrade
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 --upgrade pip
```

### Uninstall

```bash
pip3 uninstall --break-system-packages <package>
```

---

## bun (JavaScript/TypeScript packages)

Bun respects `HTTP_PROXY`/`HTTPS_PROXY` env vars.

```bash
export HTTP_PROXY=http://127.0.0.1:2080
export HTTPS_PROXY=http://127.0.0.1:2080
bun install <packages>
```

**Important:** `bun install -g <github-url>` does NOT work for GitHub repos. For GitHub projects, use the git clone + build approach below.

---

## git clone + build (GitHub projects)

For tools distributed as source on GitHub (not on npm/PyPI registries):

```bash
export HTTP_PROXY=http://127.0.0.1:2080
export HTTPS_PROXY=http://127.0.0.1:2080
git clone https://github.com/<user>/<repo>.git /tmp/<repo>
cd /tmp/<repo>
```

Then check `package.json` for the build process:
1. Look at `"bin"` field — shows where the executable will be after build
2. Look at `"scripts"` → `"build"` — shows how to build
3. Install deps and build:
   ```bash
   bun install    # or npm install
   bun run build  # or npm run build
   ```
4. Symlink the built binary:
   ```bash
   sudo ln -s /tmp/<repo>/dist/<binary>.js /usr/local/bin/<command>
   ```

**Gotcha:** Don't symlink before building — check `package.json` `"bin"` field for the actual output path (often `dist/`).

---

## curl-based installers (bun, nvm, rustup, etc.)

Always pass proxy to curl:

```bash
# Option 1: inline proxy flag
curl -fsSL --proxy http://127.0.0.1:2080 <url> | bash

# Option 2: export env vars first (recommended — covers sub-downloads too)
export HTTP_PROXY=http://127.0.0.1:2080
export HTTPS_PROXY=http://127.0.0.1:2080
curl -fsSL <url> | bash
```

### Common installers

```bash
# Bun (requires unzip to be installed first)
curl -fsSL --proxy http://127.0.0.1:2080 https://bun.sh/install | bash
source ~/.bashrc

# nvm (Node Version Manager)
curl -fsSL --proxy http://127.0.0.1:2080 https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash

# Rustup
curl -fsSL --proxy http://127.0.0.1:2080 https://sh.rustup.rs | sh
```

**Important:** Always `source ~/.bashrc` after install — the new command won't be available until the shell is reloaded.

---

## wget (downloading files/archives)

```bash
# With inline proxy flags
sudo wget -e use_proxy=yes -e https_proxy=http://127.0.0.1:2080 <url>

# Or with env vars already exported (sudo needs inline vars)
sudo HTTP_PROXY=http://127.0.0.1:2080 HTTPS_PROXY=http://127.0.0.1:2080 wget <url>
```

### Example: installing from a zip release (e.g. PMD)

```bash
cd /opt
sudo wget -e use_proxy=yes -e https_proxy=http://127.0.0.1:2080 <release-zip-url>
sudo unzip <archive>.zip
sudo ln -s /opt/<extracted-dir>/bin/<command> /usr/local/bin/<command>
```

---

## AppImage applications

AppImage files are self-contained executables. Setup:

```bash
# Make executable and move to ~/Applications/
chmod +x <App>.AppImage
mkdir -p ~/Applications
mv <App>.AppImage ~/Applications/
```

### Running

```bash
~/Applications/<App>.AppImage
```

### SUID sandbox error

If you get `The SUID sandbox helper binary was found, but is not configured correctly`:

```bash
~/Applications/<App>.AppImage --no-sandbox
```

Or extract and run (avoids sandbox entirely):

```bash
~/Applications/<App>.AppImage --appimage-extract-and-run
```

### Creating a desktop shortcut (app launcher entry)

```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/<app>.desktop << 'EOF'
[Desktop Entry]
Name=<App Name>
Exec=/home/v/Applications/<App>.AppImage --no-sandbox
Icon=<app>
Type=Application
Categories=Office;
EOF
update-desktop-database ~/.local/share/applications/
```

To also add to the Desktop:

```bash
cp ~/.local/share/applications/<app>.desktop ~/Desktop/
chmod +x ~/Desktop/<app>.desktop
# Then right-click on Desktop → "Allow Launching"
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Network is unreachable` / `Failed to connect` / `Connection timed out` | Missing proxy | Set `HTTP_PROXY` / `HTTPS_PROXY` or use `--proxy` flag |
| `EACCES: permission denied` | npm global install without sudo | Add `sudo` with proxy env vars passed through |
| `EBADENGINE Unsupported engine` | Package requires newer Node.js | Pin older version or upgrade Node via `n` |
| `externally-managed-environment` | PEP 668 system Python | Add `--break-system-packages` to pip3 |
| `sudo: command not found` for proxy vars | sudo doesn't inherit env | Pass vars inline: `sudo HTTP_PROXY=... npm install -g ...` |
| `unzip is required` | Missing system dependency | `sudo apt install unzip` first |
| `SUID sandbox helper` / `chrome-sandbox` error | AppImage/Electron sandbox issue | Add `--no-sandbox` flag |
| `Command not found` after curl installer | Shell not reloaded | Run `source ~/.bashrc` |
| `bun: command not found` inside `bun run build` | sudo doesn't see user's bun | Use full path or run without sudo |
| `ConnectionRefused` with `bun install -g <github-url>` | bun can't install from GitHub URLs | Use git clone + build instead |

### Check what's installed

```bash
apt list --installed | grep <pkg>
npm list -g --depth=0
pip3 list | grep <pkg>
bun --version
which <command>
<command> --version
```
