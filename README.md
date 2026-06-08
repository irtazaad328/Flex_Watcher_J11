<div align="center">

# ⚡ Flex Watcher J11 — NUCES Dashboard
### Automated grade, attendance & GPA tracker

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Chrome](https://img.shields.io/badge/Chrome-Required-4285F4?style=flat-square&logo=googlechrome&logoColor=white)
![Platform](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-333333?style=flat-square)
![License](https://img.shields.io/badge/All%20Rights%20Reserved-red?style=flat-square)

Flex Watcher automatically logs into your NUCES Flex portal, fetches your grades, attendance, marks, and transcript, and builds a fully offline dashboard — updated automatically every 2 minutes. It also starts itself on every PC boot. No manual launch needed.

</div>

---

## 📌 Quick Navigation

- [✨ Key Features](#-key-features)
- [📋 System Requirements](#-system-requirements)
- [🚀 Interactive Installation Guide](#-interactive-installation-guide)
- [🔄 First Sync — What to Expect](#-first-sync--what-to-expect)
- [🖥️ Auto-Start on Boot Setup](#️-auto-start-on-boot-setup)
- [📂 Folder Structure](#-folder-structure)
- [🧩 CAPTCHA Solver Guide](#-captcha--what-to-do)
- [🛠️ Troubleshooting & Fixes](#️-troubleshooting)
- [🔒 Privacy & Disclaimer](#-privacy--security)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📈 **Grades & GPA** | Live CGPA/SGPA history across all semesters, with predicted grades for ongoing courses and comprehensive performance stats. |
| 📅 **Attendance Tracking** | Interactive dashboard display with built-in shortage warnings and instant push alerts if attendance drops below 80%. |
| 📝 **Marks Breakdown** | Detailed breakdown of quizzes, assignments, midterms, and finals exactly as styled on the official website. |
| 🧮 **What-If GPA Calculator** | Test hypothetical grades for active courses to instantly see how they impact your overall SGPA & CGPA. |
| 🎯 **CGPA / SGPA Planner** | Define your target academic targets and let the dashboard calculate the exact grade trajectory required. |
| 🔔 **Desktop Notifications** | Instant background system alerts for marks updates, attendance drops, or newly posted grades (with offline catch-up history!). |
| 📴 **100% Offline Access** | Run locally with zero external calls. Transfer `dashboard.html` directly to your phone or access via local network sharing! |

---

## 📋 System Requirements

- **Python 3.8+** — Autodetected & installed automatically if missing across Windows, macOS, and Linux
- **Google Chrome** — Required for background page rendering
- **Internet Connection** — Only for background syncing; the dashboard itself works 100% offline

---

## 🚀 Interactive Installation Guide

Choose your operating system below to reveal tailored setup steps:

<details>
<summary><b>🪟 Windows</b></summary>

<br>

1. Open the `windows/` folder inside the project
2. Double-click **`install.bat`** to begin
   - Detects Python — downloads & installs it if missing
   - Installs all required packages automatically
   - Asks for your Flex username & password *(once only)*
   - Sets up **AUTO-START ON BOOT** via Windows Startup folder
   - Starts the watcher immediately in the background
   - > ⚠️ If a **ReCAPTCHA** notification comes — open Chrome from the Chrome icon on the taskbar, solve the ReCAPTCHA, and Chrome will vanish from the screen again. *(This ReCAPTCHA won't happen most of the time)*

3. Wait for this notification to appear:
   ```
   ✅ Flex Watcher Running
   "Monitoring Flex every 2 minutes."
   ```
   > You can also track detailed initialization progress inside `_data/flex_watcher.log` until you see: `Check done at HH:MM:SS(Time)`

4. Open **`dashboard.html`** in your browser *(automatically created in the `Flex_Watcher_J11/` folder)*

> ✅ After this, the dashboard updates itself automatically. The watcher also starts itself on every Windows login. **You do NOT need to run anything again.**

</details>

<details>
<summary><b>🍎 macOS</b></summary>

<br>

1. Open the `mac/` folder
2. Run **`install.sh`** — try these options in order:

   **OPTION A — Double-click** *(easiest)*
   Double-click `install.sh` — macOS opens it in Terminal automatically → runs ✓

   **OPTION B — Terminal**
   Open Terminal → type `bash ` → drag `install.sh` into the terminal window → press Enter ✓

   The installer will:
   - Detect Python — download & install it automatically if missing
   - *(In the very rare event the automatic installer fails, it will provide instructions for manual installation: `brew install python3` or via python.org)*
   - Install all required packages automatically
   - Ask for your Flex username & password *(once only)*
   - Set up **AUTO-START ON BOOT** via macOS launchd
   - Start the watcher immediately in the background
   - > ⚠️ If a **ReCAPTCHA** notification comes — open Chrome from the Chrome icon on the dock, solve the ReCAPTCHA, and Chrome will vanish from the screen again. *(This ReCAPTCHA won't happen most of the time)*

3. Wait for this notification to appear:
   ```
   ✅ Flex Watcher Running
   "Monitoring Flex every 2 minutes."
   ```
   > Or open `_data/flex_watcher.log` and watch the progress. Wait until you see: `Check done at HH:MM:SS`

4. Open **`dashboard.html`** in your browser *(automatically created in the `Flex_Watcher_J11/` folder)*

> ✅ After this, the dashboard updates itself automatically. The watcher also starts itself on every Mac login. **You do NOT need to run anything again.**

</details>

<details>
<summary><b>🐧 Linux / Ubuntu</b></summary>

<br>

1. Open the `linux/` folder
2. Run **`install.sh`** — try these options in order:

   **OPTION A — Right-click**
   Right-click `install.sh` → if you see **"Run as Program"** → click it ✓

   **OPTION B — Properties**
   Right-click → Properties → Permissions tab → check **"Allow executing as program"** → close → right-click again → **"Run as a Program"** ✓

   **OPTION C — Terminal** *(always works)*
   Open Terminal (`Ctrl+Alt+T`) → type `bash ` → drag `install.sh` into the terminal window → press Enter ✓

   The installer will:
   - Detect Python — download & install it automatically if missing
   - *(In the very rare event the automatic installer fails, it will display the exact command needed for a manual setup)*
   - Install all required packages automatically
   - Ask for your Flex username & password *(once only)*
   - Set up **AUTO-START ON BOOT** via systemd user service
   - Start the watcher immediately in the background
   - > ⚠️ If a **ReCAPTCHA** notification comes — open Chrome from the Chrome icon on the taskbar, solve the ReCAPTCHA, and Chrome will vanish from the screen again. *(This ReCAPTCHA won't happen most of the time)*

3. Wait for this notification to appear:
   ```
   ✅ Flex Watcher Running
   "Monitoring Flex every 2 minutes."
   ```
   > Or open `_data/flex_watcher.log` and watch the progress. Wait until you see: `Check done at HH:MM:SS(Time)`

4. Open **`dashboard.html`** in your browser *(automatically created in the `Flex_Watcher_J11/` folder)*

> ✅ After this, the dashboard updates itself automatically. The watcher also starts itself on every Linux login. **You do NOT need to run anything again.**

</details>

---

## 🔄 First Sync — What to Expect

> [!NOTE]
> During your initial configuration session, the Flex session may expire once or twice. This is completely normal. The background engine automatically detects expired tokens, logs back in, and proceeds silently.

Track progress anytime by reading `_data/flex_watcher.log`:

```log
[INFO] Flex Watcher started.
[INFO] Checking every 2 minutes.
[INFO] Marks: seeded.
[INFO] Attendance: seeded.
[INFO] Transcript: seeded.
[INFO] Check done at HH:MM:SS   ← Your dashboard is now ready!
```

---

## 🖥️ Auto-Start on Boot Setup

Flex Watcher integrates directly with native system utilities to ensure it wakes up alongside your hardware without causing annoying terminal popups:

| Operating System | Process Manager | Execution Style |
|---|---|---|
| **Windows** | User Startup Directory | Runs minimized/silently on system user login |
| **macOS** | System launchd Agent | Triggers auto-start silently on user session start |
| **Linux** | systemd User Service | Starts up directly with the background target system |

---

## 📂 Folder Structure

```
Flex_Watcher_J11/
├── windows/                ← Windows scripts
│   ├── install.bat         ← Run FIRST on Windows
│   ├── open_dashboard.bat  ← Reopen dashboard / relaunch if needed
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
│   ├── *.pdf               ← Exported transcript PDFs
│   └── (other files)       ← Store notifications, other information
├── dashboard.html          ← Open this in any browser
└── README.txt              ← Original quick-start text guide
```

---

## 🛑 Stopping the Watcher

Want to stop background checks? Run the shutdown script for your OS:

- **Windows** — Open the `windows/` folder and double-click `stop.bat`
- **macOS** — Open the `mac/` folder and double-click `stop.sh`
- **Linux** — Open the `linux/` folder and execute `bash stop.sh` in your terminal

> [!TIP]
> Stopping the script will automatically de-register the background boot services so it doesn't spin up on your next restart. To re-enable, run your platform's `open_dashboard` launcher script.

---

## 🧩 CAPTCHA — What to Do

The watcher manages Chrome silently behind the scenes. In rare instances, Flex may require an explicit CAPTCHA security match.

1. You will receive a system push notification: **"CAPTCHA Needs Solving"**
2. Locate and click the active background Chrome session icon on your taskbar/dock
3. Solve the quick visual puzzle
4. The page will instantly minimize/disappear on its own and background tasks will resume smoothly

---

## 🛠️ Troubleshooting

Below is a diagnostic chart for common operational problems:

| Problem | Cause | Resolution |
|---|---|---|
| Dashboard blank / outdated | Cached DOM error | Delete `dashboard.html` and launch the local `open_dashboard` script |
| Persistent expired sessions | Initial Handshake | This is expected behavior during the first handshake — wait for self-recovery |
| Python auto-install fails (Windows) | System path/permissions | Download and run the Python installer manually from [python.org](https://python.org/downloads), or check user system permissions |
| Python auto-install fails (macOS) | Xcode developer tools / Brew missing | Execute manual installation: `brew install python3` or fetch the installer from [python.org](https://python.org/downloads) |
| Python auto-install fails (Linux) | Package index out-of-date | Run manually: `sudo apt update && sudo apt install python3 python3-pip` |
| ChromeDriver matches fail | Browser mismatch | Make sure standard Google Chrome is installed, then rerun the installer |
| Package blockages (Linux) | PEP 668 restriction | Force install via: `pip install requests selenium webdriver-manager flask --break-system-packages` |

---

## 🔒 Privacy & Security

Your username and password are written strictly onto your local drive inside `_data/config.json`. No external analytic services, webhooks, or third-party servers are ever contacted. The background process speaks exclusively to your designated official academic NUCES Flex web portal.

---

## ⚠️ Disclaimer & License

This tool is designed strictly for personal academic monitoring. It is not affiliated with, authorized, or officially endorsed by NUCES/FAST. Use at your own risk.

You may **NOT** modify, reverse engineer, or redistribute this software or any part of it without explicit written permission from the author.

### Under Copyright Law:

- ✅ **Allowed:** Personal academic monitoring use
- ✅ **Allowed:** Distributing the original secure download link
- ❌ **Forbidden:** Code modification, repackaging, or unauthorized web uploads
- ❌ **Forbidden:** Claiming ownership or authorship over the intellectual assets

The selection of "All Rights Reserved" represents robust copyright protection. Under legal frameworks, reserving all rights ensures no unauthorized modifications, redistribution channels, or downstream packaging can be conducted without written authority.

**© 2026 Irtaza Ahmad. All Rights Reserved.**