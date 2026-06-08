@echo off
title FlexHub Dashboard

:: Find Python
set PYTHON=
python --version >nul 2>&1
if not errorlevel 1 ( set PYTHON=python & goto :RUN )
py --version >nul 2>&1
if not errorlevel 1 ( set PYTHON=py & goto :RUN )
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" & goto :RUN
    )
)
for /f "delims=" %%F in ('where /r "%LOCALAPPDATA%\Microsoft\WindowsApps" python.exe 2^>nul') do (
    set PYTHON="%%F" & goto :RUN
)
echo [ERROR] Python not found. Run install.bat first.
pause & exit /b 1

:RUN
:: Regenerate dashboard with latest data
%PYTHON% "%~dp0..\\_system\\generate_dashboard.py" --no-open

:: Open via localhost (enables auto-refresh), fallback to file://
start "" "http://localhost:5000/dashboard.html"
