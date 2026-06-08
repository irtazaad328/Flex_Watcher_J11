╔══════════════════════════════════════════════════════════════════╗
║              FLEX WATCHER_J11 — NUCES Dashboard                 ║
║         Automated grade, attendance & GPA tracker               ║
╚══════════════════════════════════════════════════════════════════╝

Flex Watcher automatically logs into your NUCES Flex portal,
fetches your grades, attendance, marks, and transcript, and builds
a fully offline dashboard — updated automatically every 2 minutes.
It also starts itself on every PC boot. No manual launch needed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  - Python 3.8+  (downloaded & installed automatically if missing)
  - Google Chrome
  - Internet (only for syncing — dashboard works fully offline)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─ WINDOWS ─────────────────────────────────────────┐
  │                                                                 │
  │  1. Open the  windows/  folder                                  │
  │  2. Double-click  install.bat                                   │
  │     → Detects Python, downloads & installs it if missing        │
  │     → Installs all required packages automatically              │
  │     → Asks for your Flex username & password (once only)        │
  │     → Sets up AUTO-START ON BOOT via Windows Startup folder     │
  │     → Starts the watcher immediately in the background          │
  │     → If ReCAPTCHA notification comes , open chrome from the    │
  │        chrome icon on task bar,solve ReCAPTCHA and chrome will  │
  │        vanish from the screen again.This recaptacha won't happen│
  │        most of the times.                                       │
  │                                                                 │
  │  3. Wait for this notification to appear:                       │
  │       ✅ Flex Watcher Running                                  │
  │       "Monitoring Flex every 2 minutes."                        │
  │     Or open _data/flex_watcher.log and watch the progress.      │
  │     Wait until you see:  Check done at HH:MM:SS(Time)           │
  │                                                                 │
  │  4. Open  dashboard.html  in your browser[Automatically created │
  │      in Flex_Watcher_J11 Folder(go back to see)]                │
  │                                                                 │
  │  After this the dashboard updates itself automatically.         │
  │  The watcher also starts itself on every Windows login.         │
  │  You do NOT need to run anything again.                         │
  │                                                                 │
  └────────────────────────────────────────────────┘

  ┌─ macOS ──────────────────────────────────────────┐
  │                                                                │
  │  1. Open the  mac/  folder                                     │
  │                                                                │
  │  2. Run install.sh — try these in order:                       │
  │                                                                │
  │     OPTION A — Double-click (easiest)                          │
  │       Double-click install.sh                                  │
  │       macOS opens it in Terminal automatically → runs ✓        │
  │                                                                │
  │     OPTION B — Terminal                                        │
  │       Open Terminal                                            │
  │       Type  bash  then drag  install.sh  into the terminal     │
  │       window → press Enter ✓                                   │
  │                                                                │
  │     The installer will:                                        │
  │     → Detect Python, tell you exact install command if         │
  │       missing (brew install python3 or python.org)             │
  │     → Install all required packages automatically              │
  │     → Ask for your Flex username & password (once only)        │
  │     → Set up AUTO-START ON BOOT via macOS launchd              │
  │     → Start the watcher immediately in the background          │
  │    → If ReCAPTCHA notification comes , open chrome from the    │
  │       chrome icon on task bar,solve ReCAPTCHA and chrome will  │
  │       vanish from the screen again.This recaptacha won't happen│
  │       most of the times.                                       │
  │                                                                │
  │  3. Wait for this notification to appear:                      │
  │       ✅ Flex Watcher Running                                  │
  │       "Monitoring Flex every 2 minutes."                       │
  │     Or open _data/flex_watcher.log and watch the progress.     │
  │     Wait until you see:  Check done at HH:MM:SS                │
  │                                                                │
  │  4. Open  dashboard.html  in your browser[Automatically created│
  │      in Flex_Watcher_J11 Folder(go back to see)]               │
  │                                                                │
  │  After this the dashboard updates itself automatically.        │
  │  The watcher also starts itself on every Mac login.            │
  │  You do NOT need to run anything again.                        │
  │                                                                │
  └────────────────────────────────────────────────┘

  ┌─ LINUX / UBUNTU ───────────────────────────────────┐
  │                                                                │
  │  1. Open the  linux/  folder                                   │
  │                                                                │
  │  2. Run install.sh — try these options in order:               │
  │                                                                │
  │     OPTION A — Right-click install.sh                          │
  │       If you see "Run as Program" → click it ✓                │
  │                                                                │
  │     OPTION B — Properties                                      │
  │       Right-click → Properties → Permissions tab               │
  │       Check "Allow executing as program" → close               │
  │       Right-click again → "Run as a Program" ✓                 │
  │                                                                │
  │     OPTION C — Terminal (always works)                         │
  │       Open Terminal (Ctrl+Alt+T)                               │
  │       Type  bash  then drag the install.sh file into the       │
  │       terminal window → press Enter ✓                          │
  │                                                                │
  │     The installer will:                                        │
  │     → Detect Python, tells you exact command if missing        │
  │     → Install all required packages automatically              │
  │     → Ask for your Flex username & password (once only)        │
  │     → Set up AUTO-START ON BOOT via systemd user service       │
  │     → Start the watcher immediately in the background          │
  │     → If ReCAPTCHA notification comes , open chrome from the   │
  │       chrome icon on task bar,solve ReCAPTCHA and chrome will  │
  │       vanish from the screen again.This recaptacha won't happen│
  │       most of the times.                                       │
  │                                                                │
  │                                                                │
  │  3. Wait for this notification to appear:                      │
  │       ✅ Flex Watcher Running                                  │
  │       "Monitoring Flex every 2 minutes."                       │
  │     Or open _data/flex_watcher.log and watch the progress.     │
  │     Wait until you see:  Check done at HH:MM:SS(Time)          │
  │                                                                │
  │  4. Open  dashboard.html  in your browser[Automatically created│
  │      in Flex_Watcher_J11 Folder(go back to see)]               │
  │                                                                │
  │  After this the dashboard updates itself automatically.        │
  │  The watcher also starts itself on every Linux login.          │
  │  You do NOT need to run anything again.                        │
  │                                                                │
  └────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FIRST SYNC — WHAT TO EXPECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  During first install the Flex session may expire once or twice.
  This is completely normal — do nothing, do not close anything.
  The watcher detects it, logs back in, and continues on its own.

  Watch progress in  _data/flex_watcher.log — look for:
    [INFO] Flex Watcher started.
    [INFO] Checking every 2 minutes.
    [INFO] Marks: seeded.
    [INFO] Attendance: seeded.
    [INFO] Transcript: seeded.
    [INFO] Check done at HH:MM:SS   ← ready when you see this

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AUTO-START ON BOOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Windows  → Added to Startup folder, runs silently on every login
  macOS    → Registered with launchd, starts on every login
  Linux    → Registered as systemd user service, starts on boot

  You never need to manually start the watcher after first install.
  open_dashboard is only needed to recreate the browser tab, or if
  something went wrong and you need to restart the watcher.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FOLDER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Flex_Watcher_J11/
  ├── windows/                ← Windows scripts
  │   ├── install.bat         ← Run FIRST on Windows
  │   ├── open_dashboard.bat  ← Reopen/restart if needed
  │   └── stop.bat            ← Stop the watcher
  ├── mac/                    ← macOS scripts
  │   ├── install.sh
  │   ├── open_dashboard.sh
  │   └── stop.sh             ← Stop the watcher
  ├── linux/                  ← Linux/Ubuntu scripts
  │   ├── install.sh
  │   ├── open_dashboard.sh
  │   └── stop.sh             ← Stop the watcher
  ├── _system/                ← Core engine — do not touch
  ├── _data/                  ← Created after first run
  │   ├── config.json         ← Your credentials (local only)
  │   ├── state.json          ← Cached Flex data
  │   ├── flex_watcher.log    ← Sync activity log
  │   ├──*.pdf               ← Exported transcript PDFs
  │   └── some other files    ←store notifications, other information
  │   
  ├── dashboard.html          ← Open this in any browser
  └── README.txt              ← This file
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STOPPING THE WATCHER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Windows  → open windows/ folder → double-click stop.bat
  macOS    → open mac/ folder → double-click stop.sh
  Linux    → open linux/ folder → run: bash stop.sh

  This stops the current session and unregisters auto-start so
  it does not restart on next boot.
  To start again, just run open_dashboard for your OS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  GRADES & GPA
  • Live CGPA and SGPA with full grade history across all semesters
  • Predicted grade shown for each current semester course
  • Grand total, aggregate, min, and max displayed per course

  ATTENDANCE
  • Per-course attendance tracking with shortage warnings
  • Instant notification if your attendance drops below 80%

  MARKS
  • Full marks breakdown per course (Just like on flex website)

  GPA TOOLS
  • What-If Calculator — you assign a hypothetical grade to each
    current semester course and instantly see what CGPA and
    SGPA you would get from that combination
  • CGPA & SGPa Planner — enter your target CGPA or SCGPA and it tells 
    you approximately how much work is needed based on your
    current performance

  NOTIFICATIONS
  • Background pop-up notifications like any other app —
    no need to keep Chrome, Flex, or the dashboard open
  • Get notified the moment your marks, attendance, or grade
    updates on Flex — just carry on with your work
  • If your PC was off and something changed while it was
    down, you get a catch-up notification on next startup
  • Last 30 notifications stored and viewable in the
    Notifications page inside the dashboard
  • Last 15 notifications also visible on the Dashboard home

  TRANSCRIPT
  • Full transcript grouped by semester with SGPA per semester
  • Export or Save as PDF — Transcript tab → Export → Ctrl+P

  INSTALL ONCE, RUNS FOREVER
  • One-time install — no re-activation, no extension toggle
  • Auto-starts silently every time your PC turns on
  • Runs entirely in the background, no visible window

  OFFLINE & PHONE ACCESS
  • dashboard.html works fully offline after first sync
  • Open on your phone by transferring the file directly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CAPTCHA — WHAT TO DO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Flex Watcher runs Chrome completely in the background — you
  will never see it and it will never interrupt your work.

  However, Flex occasionally shows a CAPTCHA during login.
  When this happens:

  1. You will get a notification saying CAPTCHA needs solving
  2. Look for the small Chrome icon in your taskbar / dock
  3. Click it — the Flex page with the CAPTCHA will appear
  4. Solve the CAPTCHA
  5. Chrome vanishes again automatically — everything resumes

  This is rare and only takes a few seconds. Everything else
  is completely automatic.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PRIVACY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Credentials saved only in _data/config.json on your machine.
  Nothing sent anywhere. Only talks to NUCES Flex portal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Dashboard blank or outdated
    → Delete dashboard.html and run open_dashboard again

  Session keeps expiring at first
    → Normal. Watcher recovers automatically. Just wait.

  Python not found (Windows)
    → Installer downloads and installs it automatically

  Python not found (Mac)
    →  install script handles it automatically; if it still fails: brew install python3
  Python not found (Linux)
    → sudo apt install python3 python3-pip

  ChromeDriver error
    →  install script handles it automatically; if it still fails: sudo apt install python3 python3-pip

  Packages failed (Linux)
    → pip install requests selenium webdriver-manager flask
                  --break-system-packages

  .sh opens in text editor (Linux)
    → Use Option C: terminal  →  bash install.sh

  Watcher not running after reboot
    → Run open_dashboard once to restart it manually

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DISCLAIMER & LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  This tool is for personal academic use only. It is not affiliated
  with or endorsed by NUCES/FAST. The author takes no responsibility
  for any misuse. Use at your own risk.

  You may NOT modify, reverse engineer, or redistribute this
  software or any part of it without explicit written permission
  from the author.

  © 2026 Irtaza. All Rights Reserved.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
