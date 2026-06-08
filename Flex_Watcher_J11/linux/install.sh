#!/bin/bash
echo ""
echo "============================================"
echo "  Flex Watcher_J11 - Linux Installation"
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
    echo "  Run: sudo apt install python3 python3-pip"
    exit 1
fi

echo "[OK] Python: $($PYTHON --version)"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WATCHER="$ROOT/_system/flex_watcher.py"
DATA_DIR="$ROOT/_data"
mkdir -p "$DATA_DIR"

# ── Install packages ──────────────────────────────────────────────────────────
echo ""
echo "Installing packages..."
# Ubuntu 22.04+ uses "externally managed" Python — need --break-system-packages
# Try in order: normal → --user → --break-system-packages
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet 2>/dev/null || \
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet --user 2>/dev/null || \
$PYTHON -m pip install requests selenium webdriver-manager flask --quiet --break-system-packages 2>/dev/null

# verify selenium actually importable
if ! $PYTHON -c "import selenium" 2>/dev/null; then
    echo "  pip install failed, trying pipx or apt fallback..."
    # try apt for selenium on Ubuntu
    sudo apt-get install -y python3-selenium 2>/dev/null || true
    # retry pip with --break-system-packages explicitly
    $PYTHON -m pip install selenium webdriver-manager --break-system-packages --quiet 2>/dev/null || true
fi

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

# ── Auto-start via systemd user service ───────────────────────────────────────
echo ""
echo "Setting up auto-start (systemd)..."
SVC_DIR="$HOME/.config/systemd/user"
mkdir -p "$SVC_DIR"
cat > "$SVC_DIR/flexwatcher.service" << SVC_EOF
[Unit]
Description=Flex Watcher J11
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON $WATCHER
Restart=on-failure
RestartSec=30
StandardOutput=append:$DATA_DIR/flex_watcher.log
StandardError=append:$DATA_DIR/flex_watcher.log

[Install]
WantedBy=default.target
SVC_EOF
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable flexwatcher 2>/dev/null || true
echo "[OK] Auto-start configured (systemd)."

# ── Create .desktop launcher (so it doesn't open in gedit) ───────────────────
echo ""
echo "Creating desktop launcher..."
DESKTOP_DIR="$HOME/Desktop"
mkdir -p "$DESKTOP_DIR"
# detect a terminal emulator
TERM_APP=""
for t in gnome-terminal xterm konsole xfce4-terminal mate-terminal lxterminal tilix; do
    if command -v "$t" &>/dev/null; then TERM_APP=$t; break; fi
done

if [ -n "$TERM_APP" ]; then
    # build exec command per terminal (gnome-terminal uses --, others use -e)
    if [ "$TERM_APP" = "gnome-terminal" ]; then
        EXEC_CMD="$TERM_APP -- bash \"$ROOT/linux/install.sh\"; bash"
    else
        EXEC_CMD="$TERM_APP -e 'bash \"$ROOT/linux/install.sh\"; bash'"
    fi

    cat > "$DESKTOP_DIR/FlexWatcher-Install.desktop" << DESK_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Flex Watcher - Install
Comment=Run Flex Watcher Installer
Exec=$EXEC_CMD
Icon=utilities-terminal
Terminal=false
Categories=Utility;
DESK_EOF
    chmod +x "$DESKTOP_DIR/FlexWatcher-Install.desktop"
    echo "[OK] Desktop launcher created at $DESKTOP_DIR/FlexWatcher-Install.desktop"
fi

# ── Start watcher now ─────────────────────────────────────────────────────────
echo ""
echo "Starting Flex Watcher..."
nohup $PYTHON "$WATCHER" >> "$DATA_DIR/flex_watcher.log" 2>&1 &
echo "[OK] Started (PID $!)"

# give watcher a moment to seed data then generate dashboard
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
echo "IMPORTANT: To run this script again, right-click"
echo "the .sh file and choose 'Run as Program',"
echo "or open a terminal and type: bash install.sh"
echo ""
