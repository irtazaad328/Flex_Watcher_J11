#!/bin/bash
echo "Stopping Flex Watcher..."
pkill -f flex_watcher.py && echo "Stopped." || echo "Was not running."
launchctl unload "$HOME/Library/LaunchAgents/com.flexwatcher.j11.plist" 2>/dev/null || true
