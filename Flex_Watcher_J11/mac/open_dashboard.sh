#!/bin/bash
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then PYTHON=$cmd; break; fi
done
if [ -z "$PYTHON" ]; then echo "Python not found. Run install.sh first."; exit 1; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

$PYTHON "$ROOT/_system/generate_dashboard.py" --no-open 2>/dev/null || true

# macOS: open forces default browser for http:// URLs
open "http://localhost:5000/dashboard.html"
