@echo off
echo Stopping Flex Watcher...
wmic process where "commandline like '%%flex_watcher%%'" delete >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo Done.
pause
