# Kleinanzeigen-Bot (patched)

Fork of [Second-Hand-Friends/kleinanzeigen-bot](https://github.com/Second-Hand-Friends/kleinanzeigen-bot) with patches for the new Kleinanzeigen Auth0 SSO login system.

## Patches

### 1. Auth0 SSO 2-Step Login (`__init__.py`)

Kleinanzeigen switched from a classic form (`id="login-email"`, `id="login-password"`) to an Auth0/OpenID Connect SSO flow hosted at `login.kleinanzeigen.de`.

**Old flow (broken):**
- Single page, email + password in one form, one submit

**New flow (patched):**
- **Step 1:** `login.kleinanzeigen.de/u/login/identifier` — email field `id="username"`, submit button `button[name='action']`
- **Step 2:** `login.kleinanzeigen.de/u/login/password` — password field `id="password"`, submit button `button[name='action']`

The `fill_login_data_and_send()` method was rewritten to handle both steps sequentially. The double-login retry in `login()` was removed because the 2-step flow does not support re-entry.

### 2. Headless/Root Support (`web_scraping_mixin.py`)

Added `cfg.sandbox = False` after `Config()` creation to allow running Chromium as root on headless servers.

### 3. `.gitignore`

Added to exclude `venv/`, `__pycache__/`, `config.yaml` (contains credentials), `*.log`, and test files.

## Setup (headless server via SSH SOCKS proxy)

Kleinanzeigen blocks datacenter IPs (Vultr, Hetzner). Use an SSH reverse SOCKS proxy from a residential connection:

```bash
# On your home PC:
ssh -R 1080 root@<server-ip>

# On the server:
cd /opt/kleinanzeigenbot
python3 -m venv venv
source venv/bin/activate
pip install -e . requests

# Configure config.yaml:
#   browser.arguments: ["--no-sandbox", "--disable-gpu", "--headless=new",
#                       "--proxy-server=socks5://127.0.0.1:1080",
#                       "--user-data-dir=/tmp/chrome-data"]
#   login.username: your@email
#   login.password: yourpassword

python -m kleinanzeigen_bot publish --ads=all
```

## Requirements

- Python 3.11+
- Chromium (headless)
- SSH SOCKS proxy (residential IP) — datacenter IPs are blocked by Kleinanzeigen
