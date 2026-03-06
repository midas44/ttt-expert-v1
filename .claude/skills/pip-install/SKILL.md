---
name: pip-install
description: >
  Install Python packages using pip3 on this machine. Use this skill when the user asks to
  install a Python package, pip install something, add a Python dependency, or mentions
  "pip", "pip3", "install pandas", "install numpy", or any Python package installation.
  Also use when pip install fails with network errors, proxy issues, or permission errors.
  This skill covers proxy configuration, system package installation, and common
  pip troubleshooting.
---

# Python Package Installation (pip3)

## Environment

This machine uses an HTTP proxy for internet access. pip3 cannot reach PyPI without it.

- **Proxy**: `http://127.0.0.1:2080`
- **System Python**: pip3 requires `--break-system-packages` for system-wide installs (no venv)

## Install Command

Always use this form:

```bash
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 <package1> <package2> ...
```

### Examples

```bash
# Single package
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 requests

# Multiple packages
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 openpyxl pandas numpy

# Specific version
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 flask==3.0.0

# Upgrade existing package
pip3 install --break-system-packages --proxy http://127.0.0.1:2080 --upgrade pip
```

## Troubleshooting

### "Network is unreachable" / "Failed to establish a new connection"
Missing proxy. Add `--proxy http://127.0.0.1:2080`.

### "externally-managed-environment"
System Python is PEP 668 managed. Add `--break-system-packages`.

### Alternative: use environment variable
```bash
export HTTPS_PROXY=http://127.0.0.1:2080
pip3 install --break-system-packages <package>
```

### Check installed packages
```bash
pip3 list | grep <package>
```

### Uninstall
```bash
pip3 uninstall --break-system-packages <package>
```
