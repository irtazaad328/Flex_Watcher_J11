
@echo off
title Flex Watcher_J11 - Windows Setup
color 0A
echo.
echo  ============================================
echo   Flex Watcher_J11 - Windows Installation
echo  ============================================
echo.
 
:: ── Find Python ──────────────────────────────────────────────────────────────
set PYTHON=
python --version >nul 2>&1
if not errorlevel 1 ( set PYTHON=python & goto :FIXPIP )
 
py --version >nul 2>&1
if not errorlevel 1 ( set PYTHON=py & goto :FIXPIP )
 
:: Search common install locations
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :FIXPIP
    )
    if exist "C:\Python%%V\python.exe" (
        set PYTHON="C:\Python%%V\python.exe"
        goto :FIXPIP
    )
)
 
:: Microsoft Store Python
for /f "delims=" %%F in ('where /r "%LOCALAPPDATA%\Microsoft\WindowsApps" python.exe 2^>nul') do (
    set PYTHON="%%F" & goto :FIXPIP
)
 
echo  Python not found. Downloading Python 3.11...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "[Net.ServicePointManager]::SecurityProtocol='Tls12';" ^
  "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe'"
if errorlevel 1 ( echo [ERROR] Download failed. Install from https://python.org & pause & exit /b 1 )
"%TEMP%\py_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%TEMP%\py_setup.exe" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
set PYTHON=python
 
:: ── Repair pip (handles corrupted pip on any Python install) ─────────────────
:FIXPIP
echo  [OK] Python: %PYTHON%
echo.
echo  Repairing pip (ensures clean install on all PCs)...
%PYTHON% -m ensurepip --upgrade >nul 2>&1
%PYTHON% -m pip install --upgrade pip --quiet --no-warn-script-location >nul 2>&1
if errorlevel 1 (
    echo  pip repair via ensurepip failed, trying get-pip.py...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "[Net.ServicePointManager]::SecurityProtocol='Tls12';" ^
      "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'" >nul 2>&1
    %PYTHON% "%TEMP%\get-pip.py" --quiet >nul 2>&1
    del "%TEMP%\get-pip.py" >nul 2>&1
)
echo  [OK] pip ready.
 
:: ── Install packages ─────────────────────────────────────────────────────────
echo.
echo  Installing packages...
%PYTHON% -m pip install requests winotify selenium webdriver-manager flask --quiet --no-warn-script-location
if errorlevel 1 (
    echo  Retrying with --user flag...
    %PYTHON% -m pip install requests winotify selenium webdriver-manager flask --quiet --user
)
echo  [OK] Packages installed.
 
:: ── Pre-cache ChromeDriver ────────────────────────────────────────────────────
echo.
echo  Caching ChromeDriver...
%PYTHON% "%~dp0..\\_system\\cache_driver.py"
 
:: ── Auto-start on boot ────────────────────────────────────────────────────────
echo.
echo  Setting up auto-start on boot...
set ROOT=%~dp0..
for %%I in ("%ROOT%") do set ROOT=%%~fI
set WATCHER=%ROOT%\_system\flex_watcher.py
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
 
:: Derive pythonw.exe from whichever python.exe was found (works for ANY Python version)
set PYTHONW=
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe" (
        set PYTHONW=%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe
        goto :GOTPYTHONW
    )
)
:: Fallback: derive path from PYTHON variable by replacing python.exe with pythonw.exe
if not "%PYTHON%"=="" (
    for %%P in (%PYTHON%) do (
        set _PYDIR=%%~dpP
    )
    if exist "%_PYDIR%pythonw.exe" (
        set PYTHONW=%_PYDIR%pythonw.exe
        goto :GOTPYTHONW
    )
)
:: Last resort: search PATH (skip msys/cygwin versions which can't run win scripts)
for /f "delims=" %%i in ('where pythonw 2^>nul') do (
    echo %%i | findstr /i "msys cygwin mingw" >nul
    if errorlevel 1 ( set PYTHONW=%%i & goto :GOTPYTHONW )
)
:: If still nothing, use python.exe (will show a flash console window but works)
set PYTHONW=%PYTHON%
:GOTPYTHONW
 
echo Set w=CreateObject("WScript.Shell") > "%STARTUP%\FlexWatcher.vbs"
echo w.Run Chr(34)^&"%PYTHONW%"^&Chr(34)^&" "^&Chr(34)^&"%WATCHER%"^&Chr(34)^,0^,False >> "%STARTUP%\FlexWatcher.vbs"
echo  [OK] Auto-start configured.
 
:: ── Start watcher now ─────────────────────────────────────────────────────────
echo.
echo  Starting Flex Watcher...
if exist "%PYTHONW%" (
    start "" /min "%PYTHONW%" "%WATCHER%"
) else (
    start "" /min %PYTHON% "%WATCHER%"
)
 
echo.
echo  Generating dashboard...
timeout /t 4 /nobreak >nul
%PYTHON% "%ROOT%\_system\generate_dashboard.py" --no-open >nul 2>&1
echo  [OK] Dashboard generated.
 
echo.
echo  ============================================
echo   DONE!
echo  ============================================
echo.
echo  Flex Watcher is running in the background.
echo  A dialog will ask for your Flex credentials.
echo.
echo  Use open_dashboard.bat to view your dashboard.
echo.
pause
