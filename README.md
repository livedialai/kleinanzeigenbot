# Kleinanzeigen-Bot (patched)

Fork of [Second-Hand-Friends/kleinanzeigen-bot](https://github.com/Second-Hand-Friends/kleinanzeigen-bot) with patches for the new Kleinanzeigen Auth0 SSO login and headless server support.

## What's Patched

### 1. Auth0 SSO 2-Step Login (`src/kleinanzeigen_bot/__init__.py`)

Kleinanzeigen switched from a classic form (`id="login-email"`, `id="login-password"`) to an Auth0/OpenID Connect SSO flow at `login.kleinanzeigen.de`.

**Old flow (broken):** Single page, email + password in one form, one submit.

**New flow (patched):**
- **Step 1:** `login.kleinanzeigen.de/u/login/identifier` — email field `id="username"`, submit `button[name='action']`
- **Step 2:** `login.kleinanzeigen.de/u/login/password` — password field `id="password"`, submit `button[name='action']`

`fill_login_data_and_send()` rewritten for both steps. Double-login retry removed (Auth0 flow doesn't support re-entry).

### 2. Headless/Root Support (`src/kleinanzeigen_bot/utils/web_scraping_mixin.py`)

- `cfg.sandbox = False` after `Config()` creation — allows Chromium as root
- Xvfb required instead of `--headless=new` (Kleinanzeigen detects headless Chromium and blocks with fake "IP gesperrt" page)

### 3. `.gitignore`

Excludes `venv/`, `__pycache__/`, `config.yaml` (credentials), `*.log`, test files.

## Critical: SSH SOCKS Proxy

**Kleinanzeigen blocks ALL datacenter IPs** (Vultr, Hetzner, etc.) with "IP-Bereich gesperrt". You MUST tunnel through a residential IP via SSH SOCKS proxy.

```bash
# On your home PC (residential IP):
ssh -R 1080 root@<server-ip>
```

This must stay open while the bot runs. If the tunnel drops, the bot can't reach Kleinanzeigen.

## Quick Setup

```bash
# On the server:
git clone https://github.com/livedialai/kleinanzeigenbot.git /opt/kleinanzeigenbot
cd /opt/kleinanzeigenbot
bash setup.sh

# Edit config.yaml — set login credentials + proxy
vi config.yaml

# Start SSH tunnel from home PC:
ssh -R 1080 root@<server-ip>

# Run the bot (MUST use xvfb-run, not --headless):
source venv/bin/activate
xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    python -m kleinanzeigen_bot publish --ads=all
```

## config.yaml (required settings)

```yaml
browser:
  arguments: ["--no-sandbox", "--disable-gpu", "--proxy-server=socks5://127.0.0.1:1080", "--user-data-dir=/tmp/chrome-data"]
  use_private_window: false
login:
  username: your@email
  password: yourpassword
```

**Do NOT use `--headless=new`** — Kleinanzeigen detects it and shows a fake IP-block page. Use `xvfb-run` instead.

## Session Persistence

The bot stores session cookies in `--user-data-dir=/tmp/chrome-data`. After a successful login, subsequent runs skip the login (cookies valid for days/weeks). If `/tmp` is cleared (reboot), a fresh login is needed.

## Known Issues

- **Rate limiting:** Auth0 login endpoint rate-limits after ~5 attempts. Wait 15-30 min between failed login attempts.
- **"Anzeige aufgeben" form:** The publish form (`postad-title` etc.) has also changed on Kleinanzeigen. Publishing new ads needs the same kind of form-selector patch as the login.
- **Listing ads:** The JSON API (`m-meine-anzeigen-verwalten.json`) may return empty when fetched via `fetch()` in page context. The bot's own `web_request()` method works (uses CDP), but standalone scripts need to navigate to `m-meine-anzeigen.html` and scrape the DOM.
