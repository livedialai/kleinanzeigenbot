# Setup script for headless server with SSH SOCKS proxy
# Run this on a fresh server to get the bot working

#!/bin/bash
set -e

REPO_DIR="/opt/kleinanzeigenbot"
GIT_REPO="https://github.com/livedialai/kleinanzeigenbot.git"

echo "=== Installing system packages ==="
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip chromium xvfb

echo "=== Cloning repo ==="
if [ -d "$REPO_DIR" ]; then
    echo "Repo already exists, pulling latest..."
    cd "$REPO_DIR" && git pull
else
    git clone "$GIT_REPO" "$REPO_DIR"
fi

cd "$REPO_DIR"

echo "=== Creating venv and installing dependencies ==="
python3 -m venv venv
source venv/bin/activate
pip install -e . requests

echo "=== Creating config.yaml ==="
if [ ! -f config.yaml ]; then
    python -m kleinanzeigen_bot create-config
fi

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Before running the bot, you need:"
echo ""
echo "1. SSH SOCKS PROXY (from your home PC, residential IP):"
echo "   ssh -R 1080 root@<this-server-ip>"
echo "   (Kleinanzeigen blocks datacenter IPs — must tunnel through residential IP)"
echo ""
echo "2. Edit config.yaml:"
echo "   login:"
echo "     username: your@email"
echo "     password: yourpassword"
echo "   browser:"
echo "     arguments: [\"--no-sandbox\", \"--disable-gpu\", \"--proxy-server=socks5://127.0.0.1:1080\", \"--user-data-dir=/tmp/chrome-data\"]"
echo "     use_private_window: false"
echo ""
echo "3. Run the bot with Xvfb (anti-bot-detection):"
echo "   source venv/bin/activate"
echo "   xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python -m kleinanzeigen_bot publish --ads=all"
echo ""
echo "4. List ads / check login:"
echo "   xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python /tmp/list_ads5.py"
