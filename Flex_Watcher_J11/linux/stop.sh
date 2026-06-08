#!/bin/bash
echo "Stopping Flex Watcher..."
pkill -f flex_watcher.py && echo "Stopped." || echo "Was not running."
systemctl --user stop flexwatcher 2>/dev/null || true
