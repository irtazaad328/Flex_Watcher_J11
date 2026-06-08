#!/bin/bash
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then PYTHON=$cmd; break; fi
done
if [ -z "$PYTHON" ]; then echo "Python not found. Run install.sh first."; exit 1; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

$PYTHON "$ROOT/_system/generate_dashboard.py" --no-open 2>/dev/null || true

URL="http://localhost:5000/dashboard.html"

# try common browsers before falling back to xdg-open
BROWSER=""
for b in google-chrome chromium-browser chromium firefox; do
    if command -v "$b" &>/dev/null; then BROWSER="$b"; break; fi
done

if [ -n "$BROWSER" ]; then
    "$BROWSER" "$URL" &
elif command -v xdg-open &>/dev/null; then
    # xdg-open on some systems opens .html as text — force browser via BROWSER env
    BROWSER=$(xdg-mime query default text/html 2>/dev/null || true)
    xdg-open "$URL" &
else
    echo "Could not find a browser. Open this URL manually: $URL"
fi
