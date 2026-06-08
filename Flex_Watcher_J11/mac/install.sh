#!/bin/bash
echo ""
echo "============================================"
echo "  Flex Watcher_J11 - macOS Installation"
echo "============================================"
echo ""

# ── Find Python 3 ─────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$($cmd -c "import sys; print(sys.version_info>=(3,8))" 2>/dev/null)
        if [ "$VER" = "True" ]; then PYTHON=$cmd; break; fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python 3.8+ not found."
    echo "  Install via: brew install python3"
    echo "  Or download from: https://python.org"
    exit 1
fi

echo "[OK] Python: $($PYTHON --version)"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WATCHER="$ROOT/_system/flex_watcher.py"
DATA_DIR="$ROOT/_data"
mkdir -p "$DATA_DIR"

# ── Install packages ──────────────────────────────────────────────────────────
echo ""
echo "Repairing pip..."
$PYTHON -m ensurepip --upgrade 2>/dev/null || true
$PYTHON -m pip install --upgrade pip --quiet 2>/dev/null || \
    curl -s https://bootstrap.pypa.io/get-pip.py | $PYTHON 2>/dev/null || true

echo "Installing packages..."
# try normal first, then --user, then --break-system-packages for newer macOS
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet 2>/dev/null || \
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet --user 2>/dev/null || \
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet --break-system-packages 2>/dev/null || true
echo "[OK] Packages installed."

# ── Cache ChromeDriver ────────────────────────────────────────────────────────
echo ""
echo "Caching ChromeDriver..."
$PYTHON "$ROOT/_system/cache_driver.py" 2>/dev/null || true

# ── Collect credentials ───────────────────────────────────────────────────────
CONFIG="$DATA_DIR/config.json"
if [ ! -f "$CONFIG" ]; then
    echo ""
    echo "============================================"
    echo "  Flex Credentials Setup"
    echo "============================================"
    echo ""
    printf "Enter your Flex username: "
    read -r FW_USER
    printf "Enter your Flex password: "
    read -rs FW_PASS
    echo ""
    if [ -z "$FW_USER" ] || [ -z "$FW_PASS" ]; then
        echo "[ERROR] Username and password are required."
        exit 1
    fi
    $PYTHON -c "import json,pathlib,sys; p=pathlib.Path(sys.argv[3]); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({'username':sys.argv[1],'password':sys.argv[2]},indent=2),encoding='utf-8'); print('[OK] Credentials saved.')" "$FW_USER" "$FW_PASS" "$CONFIG"
fi

# ── Auto-start via launchd ─────────────────────────────────────────────────────
echo ""
echo "Setting up auto-start..."
PLIST="$HOME/Library/LaunchAgents/com.flexwatcher.j11.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.flexwatcher.j11</string>
  <key>ProgramArguments</key><array>
    <string>$PYTHON</string><string>$WATCHER</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$DATA_DIR/flex_watcher.log</string>
  <key>StandardErrorPath</key><string>$DATA_DIR/flex_watcher.log</string>
</dict></plist>
PLIST_EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST" 2>/dev/null || true
echo "[OK] Auto-start configured (launchd)."

# ── Start watcher now ─────────────────────────────────────────────────────────
echo ""
echo "Starting Flex Watcher..."
nohup $PYTHON "$WATCHER" >> "$DATA_DIR/flex_watcher.log" 2>&1 &
echo "[OK] Started (PID $!)"

echo ""
echo "Generating dashboard..."
sleep 4
$PYTHON "$ROOT/_system/generate_dashboard.py" --no-open 2>/dev/null || true
echo "[OK] Dashboard generated."

echo ""
echo "============================================"
echo "  DONE!"
echo "============================================"
echo ""
echo "Flex Watcher is running in the background."
echo ""
echo "To view your dashboard:"
echo "  Run: bash open_dashboard.sh"
echo "  Or open: http://localhost:5000/dashboard.html"
echo ""
