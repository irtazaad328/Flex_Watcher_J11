"""
Flex Watcher - fully automatic, self-healing session management.
Auto-logins when session expires using Selenium + reCAPTCHA automation.
Includes FlexHub Dashboard (web UI at http://localhost:5000).
"""

import sys, time, json, hashlib, re, os, logging, threading, webbrowser
from pathlib import Path
from datetime import datetime

import requests
import platform as _platform
_IS_WINDOWS = _platform.system() == "Windows"
if _IS_WINDOWS:
    try:
        from winotify import Notification, audio as _wino_audio
    except ImportError:
        _IS_WINDOWS = False

DIR         = Path(__file__).parent.parent  # root folder (parent of _system)
SYSTEM_DIR  = Path(__file__).parent          # _system folder
DATA_DIR    = DIR / "_data"
DATA_DIR.mkdir(exist_ok=True)
DASHBOARD_PORT = 5000
STATE_FILE  = DATA_DIR / "flex_state.json"
LOG_FILE    = DATA_DIR / "flex_watcher.log"
CONFIG_FILE = DATA_DIR / "config.json"
COOKIE_FILE = DATA_DIR / "flex_cookie.txt"
NOTIF_FILE  = DATA_DIR / "flex_notifications.json"
LOCK_FILE_PATH = DATA_DIR / "login.lock"

BASE           = "https://flexstudent.nu.edu.pk"
LOGIN_URL      = BASE + "/Login"
CHECK_MINUTES  = 2
TRANSCRIPT_URL = BASE + "/Student/Transcript?dump=%2FQfkdZh%2B%2BnVSJhyh58YS%2FQ%3D%3D"
DASHBOARD_PORT = 5000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger()

#Notification Storage 
def load_notifications():
    if NOTIF_FILE.exists():
        try:
            return json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_notification(title, lines):
    notifs = load_notifications()
    notifs.insert(0, {
        "title": title,
        "lines": lines,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    notifs = notifs[:200]  # keep last 200
    NOTIF_FILE.write_text(json.dumps(notifs, indent=2), encoding="utf-8")

def notify(title, lines):
    msg = "\n".join(lines)
    log.info(f"NOTIFY | {title} | {lines}")
    save_notification(title, lines)
    try:
        if _IS_WINDOWS:
            toast = Notification(
                app_id="Flex Watcher",
                title=title,
                msg=msg,
                duration="long",
            )
            toast.set_audio(_wino_audio.Default, loop=False)
            toast.show()
        elif _platform.system() == "Darwin":
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_msg   = msg.replace('"', '\\"').replace("'", "\\'")
            os.system(f'osascript -e \'display notification "{safe_msg}" with title "{safe_title}"\'  &')
        else:
            safe_title = title.replace('"', '\\"')
            safe_msg   = msg.replace('"', '\\"')
            os.system(f'notify-send "{safe_title}" "{safe_msg}" 2>/dev/null &')
    except Exception as e:
        log.warning(f"Notification failed: {e}")

#Config 
def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_credentials():
    cfg = load_config()
    if cfg.get("username") and cfg.get("password"):
        return cfg["username"], cfg["password"]

    #Try terminal input first (works in all backgrounds)
    # Check if we have a real TTY to read from
    if sys.stdin and sys.stdin.isatty():
        import getpass
        print("\n=== Flex Watcher: Credentials Required ===")
        username = input("Enter your Flex username: ").strip()
        password = getpass.getpass("Enter your Flex password: ").strip()
        if username and password:
            save_config({"username": username, "password": password})
            log.info("Credentials saved.")
            return username, password
        log.error("No credentials provided.")
        sys.exit(1)

    #Fallback: GUI dialog (Mac/Linux/Windows)
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        # Force window to appear on macOS
        if _platform.system() == "Darwin":
            os.system("osascript -e 'tell application \"System Events\" to set frontmost of process \"Python\" to true' 2>/dev/null &")
        root.after(100, lambda: root.focus_force())
        root.update()

        username = simpledialog.askstring("Flex Watcher", "Enter your Flex username:", parent=root)
        password = simpledialog.askstring("Flex Watcher", "Enter your Flex password:", show="*", parent=root)
        root.destroy()

        if username and password:
            save_config({"username": username.strip(), "password": password.strip()})
            log.info("Credentials saved.")
            return username.strip(), password.strip()
    except Exception as e:
        log.warning(f"GUI dialog failed: {e}")

    #Last resort: open a terminal for the user to type in
    log.error("Could not prompt for credentials. Please create the config manually.")
    config_path = CONFIG_FILE
    example = json.dumps({"username": "your_flex_id", "password": "your_password"}, indent=2)
    log.error(f"Create this file:\n  {config_path}\nWith content:\n{example}")
    # Write a placeholder so the user knows where to put it
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(example, encoding="utf-8")
        log.error(f"A template has been written to:\n  {config_path}\nFill in your credentials, then restart Flex Watcher.")
    sys.exit(1)

#ChromeDriver resolver (no network needed) 
def _find_chromedriver():
    import shutil, glob, subprocess

    # 1. Try webdriver_manager quickly
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as _Svc
        import requests as _req
        _orig_get = _req.get
        def _get_timeout(*a, **kw):
            kw.setdefault("timeout", 10)
            return _orig_get(*a, **kw)
        _req.get = _get_timeout
        path = ChromeDriverManager().install()
        _req.get = _orig_get
        log.info(f"ChromeDriver via webdriver_manager: {path}")
        return path
    except Exception as e:
        log.warning(f"webdriver_manager failed ({e}), trying local fallback...")

    # 2. Common local locations on Windows
    candidates = []
    p = shutil.which("chromedriver") or shutil.which("chromedriver.exe")
    if p:
        candidates.append(p)
    for pattern in [
        r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
        r"C:\chromedriver\chromedriver.exe",
        r"C:\chromedriver.exe",
        os.path.expanduser(r"~\.wdm\drivers\chromedriver\win64\*\chromedriver-win32\chromedriver.exe"),
        os.path.expanduser(r"~\.wdm\drivers\chromedriver\win64\*\chromedriver.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\chromedriver.exe"),
    ]:
        matches = glob.glob(pattern)
        if matches:
            candidates.extend(matches)
        elif os.path.exists(pattern):
            candidates.append(pattern)

    if candidates:
        log.info(f"ChromeDriver found locally: {candidates[0]}")
        return candidates[0]

    log.info("No local chromedriver found — letting Selenium auto-detect.")
    return None

#Auto Login via Selenium 
def auto_login(username, password):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.chrome.service import Service
        import random
    except ImportError:
        log.error("Selenium not installed.")
        return None

    log.info("Auto-login starting (minimized browser)...")
    notify("🔄 Flex Watcher", ["Session expired. Logging in automatically...", "A small Chrome window will open briefly and close on its own."])

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    import tempfile
    tmp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={tmp_profile}")
    # Never use headless — reCAPTCHA is completely broken in headless mode.
    # On Windows: push window off-screen with --window-position.
    # On Mac/Linux: start normally, then immediately move off-screen via
    # set_window_position() after driver launches (Selenium call works on Mac).
    _use_headless = False
    if _platform.system() == "Windows":
        options.add_argument("--window-position=-32000,-32000")
    options.add_argument("--window-size=1280,900")

    driver = None
    try:
        driver_path = _find_chromedriver()
        if driver_path:
            driver = webdriver.Chrome(service=Service(driver_path), options=options)
        else:
            driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # On Mac/Linux move window off-screen immediately after launch
        if _platform.system() != "Windows":
            try:
                driver.set_window_position(-2000, 0)
            except Exception:
                pass
        _wait_sec = 30 if _platform.system() == "Windows" else 90
        wait = WebDriverWait(driver, _wait_sec)

        driver.get(LOGIN_URL)
        time.sleep(2)

        user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_field.clear()
        for ch in username:
            user_field.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.15))

        time.sleep(0.5)

        pass_field = driver.find_element(By.ID, "pass")
        pass_field.clear()
        for ch in password:
            pass_field.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.15))

        time.sleep(0.5)

        log.info("Handling reCAPTCHA...")
        try:
            recaptcha_frame = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "iframe[src*='recaptcha'][title*='reCAPTCHA']")
            ))
            driver.switch_to.frame(recaptcha_frame)
            checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
            actions = ActionChains(driver)
            actions.move_to_element(checkbox)
            actions.pause(random.uniform(0.3, 0.8))
            actions.click()
            actions.perform()
            time.sleep(2)
            driver.switch_to.default_content()
        except Exception as e:
            log.warning(f"reCAPTCHA checkbox issue: {e}")
            driver.switch_to.default_content()

        challenge_appeared = False
        try:
            selectors = [
                "iframe[title*='challenge'][src*='recaptcha']",
                "iframe[src*='recaptcha/api2/bframe']",
                "iframe[src*='recaptcha'][src*='bframe']",
            ]
            for sel in selectors:
                frames = driver.find_elements(By.CSS_SELECTOR, sel)
                for f in frames:
                    if f.is_displayed() and f.size.get("height", 0) > 100:
                        challenge_appeared = True
                        break
                if challenge_appeared:
                    break
        except Exception:
            pass

        if challenge_appeared:
            # bring Chrome to front so user can solve
            log.info("reCAPTCHA challenge — bringing Chrome to front for user to solve...")
            try:
                driver.maximize_window()
            except Exception:
                pass
            notify("⚠️ Solve reCAPTCHA",
                   ["A reCAPTCHA puzzle appeared in Chrome.",
                    "Please solve it — login happens automatically once done."])

            # wait for challenge to disappear OR page to navigate away on its own
            for _ in range(360):
                time.sleep(0.5)
                # check if the page already navigated away (form auto-submitted after captcha)
                try:
                    cur = driver.current_url
                    if "Login" not in cur and cur != LOGIN_URL:
                        log.info("Page navigated away during captcha wait — login succeeded.")
                        break
                except Exception:
                    pass
                still_visible = False
                try:
                    for sel in selectors:
                        frames = driver.find_elements(By.CSS_SELECTOR, sel)
                        for f in frames:
                            if f.is_displayed() and f.size.get("height", 0) > 100:
                                still_visible = True
                                break
                        if still_visible:
                            break
                except Exception:
                    pass
                if not still_visible:
                    break

            # move window off-screen again after solving
            if _platform.system() != "Windows":
                try:
                    driver.set_window_position(-2000, 0)
                except Exception:
                    pass
            else:
                try:
                    driver.set_window_position(-32000, -32000)
                except Exception:
                    pass

        # check if we already left the login page (auto-submit after captcha)
        already_done = False
        try:
            cur = driver.current_url
            if "Login" not in cur and cur != LOGIN_URL:
                already_done = True
                log.info("Already past login page — skipping sign-in click.")
        except Exception:
            pass

        if not already_done:
            # wait a moment for captcha token to propagate before clicking
            time.sleep(3)
            try:
                sign_in = driver.find_element(By.ID, "m_login_signin_submit")
                driver.execute_script("arguments[0].click();", sign_in)
            except Exception as e:
                log.warning(f"sign_in click failed ({e}) — page may have already submitted")

        # fresh wait object so timeout isn't partially consumed
        post_wait = WebDriverWait(driver, 60)
        try:
            post_wait.until(lambda d: "Login" not in d.current_url and d.current_url != LOGIN_URL)
        except Exception:
            # last chance: maybe already past login, check cookies anyway
            log.warning("post-login URL wait timed out — checking cookies anyway")

        time.sleep(2)

        cookies = driver.get_cookies()
        cookie = next((c for c in cookies if c["name"] == "ASP.NET_SessionId"), None)

        if cookie:
            value = cookie["value"]
            COOKIE_FILE.write_text(value, encoding="utf-8")
            notify("✅ Auto-Login Successful", ["Flex session renewed automatically.", "Monitoring resumed."])
            return value
        else:
            log.error("Login seemed to work but no session cookie found.")
            return None

    except Exception as e:
        log.error(f"Auto-login failed: {e}", exc_info=True)
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

LOCK_FILE = LOCK_FILE_PATH
if LOCK_FILE.exists():
    LOCK_FILE.unlink()

def get_cookie(username, password):
    if COOKIE_FILE.exists():
        value = COOKIE_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    if LOCK_FILE.exists():
        log.info("Login already in progress — waiting...")
        for _ in range(60):
            time.sleep(1)
            if not LOCK_FILE.exists() and COOKIE_FILE.exists():
                return COOKIE_FILE.read_text(encoding="utf-8").strip()
        return None
    try:
        LOCK_FILE.write_text("locked")
        return auto_login(username, password)
    finally:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()

def build_session(cookie_value):
    s = requests.Session()
    s.cookies.set("ASP.NET_SessionId", cookie_value, domain="flexstudent.nu.edu.pk", path="/")
    if _platform.system() == "Darwin":
        _ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    elif _platform.system() == "Linux":
        _ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    else:
        _ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    s.headers.update({
        "User-Agent": _ua,
        "Referer": BASE,
    })
    return s

#State ───────────────
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

#HTTP
def fetch(sess, url, post_data=None, json_data=False):
    try:
        if post_data:
            if json_data:
                r = sess.post(url, data=post_data,
                              headers={"Content-Type": "application/json"},
                              timeout=20, allow_redirects=True)
            else:
                r = sess.post(url, data=post_data, timeout=20, allow_redirects=True)
        else:
            r = sess.get(url, timeout=20, allow_redirects=True)
        return r.text, r.url
    except Exception as e:
        log.warning(f"Fetch error {url}: {e}")
        return None, "network_error"

def is_logged_in(html, final_url):
    if not html: return False
    if final_url == "network_error": return False
    return "Login" not in (final_url or "")

def is_network_error(html, final_url):
    return html is None and final_url == "network_error"

#HTML Utilities ──────
def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"&nbsp;", " ", re.sub(r"<[^>]+>", "", html))).strip()

def clean_for_hash(html):
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    html = re.sub(r"<input[^>]*>", "", html, flags=re.I)
    html = re.sub(r'nonce="[^"]*"', "", html)
    html = re.sub(r"Last Login:.*?(<|\n)", "", html, flags=re.I)
    html = re.sub(r"\d{1,2}:\d{2}:\d{2}", "", html)
    return re.sub(r"\s+", " ", html).strip()

def page_hash(html):
    return hashlib.md5(clean_for_hash(html).encode()).hexdigest()

#Parsers ─────────────
def extract_course_names(html):
    names = {}
    for m in re.finditer(r'<h5>([A-Z]{2,3}\d{3,4})-([^<(]+)', html, re.I):
        code = m.group(1).strip()
        name = m.group(2).strip().rstrip('-').strip()
        if name: names[code] = name
    return names

def parse_marks(html, course_names=None):
    if course_names is None: course_names = {}
    course_ids = re.findall(r'href="#([A-Z]{2,3}\d{3,4})"', html)
    snapshot = {}
    for cid in course_ids:
        start = html.find(f'id="{cid}"')
        if start == -1: continue
        end = len(html)
        for other in course_ids:
            if other == cid: continue
            p = html.find(f'id="{other}"', start + 1)
            if 0 < p < end: end = p
        course_html = html[start:end]
        cname = course_names.get(cid)
        clabel = f"{cid} ({cname})" if cname else cid
        entries = {}      # marks only — for notifications
        class_rows = []   # (weightage, avg, min, max) per row for course-level stats
        sec_class_rows = {}  # section_label -> list of row dicts (for best-off capping)
        sec_total_w = {}     # section_label -> section total weightage
        for tbl in re.finditer(r"<table[\s\S]*?</table>", course_html, re.I):
            thtml = tbl.group(0)
            headers = [strip_tags(m) for m in re.findall(r"<th[^>]*>([\s\S]*?)</th>", thtml, re.I)]
            if not headers: continue
            obtained_idx = next((i for i, h in enumerate(headers) if "Obtained" in h), None)
            total_idx    = next((i for i, h in enumerate(headers) if re.search(r"Total\s*Marks|^Total$|Out\s*of", h, re.I)), None)
            weight_idx   = next((i for i, h in enumerate(headers) if "Weightage" in h or "Weight" in h), None)
            type_idx = next((i for i, h in enumerate(headers) if re.search(r"#\s*$", h)), None)
            if type_idx is None:
                type_idx = next((i for i, h in enumerate(headers) if re.search(
                    r"lab work|assignment|quiz|sessional|presentation|initial draft|"
                    r"project|participation|mid|final|exam|viva|oral|practical|"
                    r"homework|task|activity|test|term|report|paper", h, re.I)), None)
            if obtained_idx is None: continue
            if type_idx is None: continue
            sec_label = re.sub(r"\s*#\s*$", "", headers[type_idx]).strip()
            tbody = re.search(r"<tbody[^>]*>([\s\S]*?)</tbody>", thtml, re.I)
            body = tbody.group(1) if tbody else thtml
            for tr in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", body, re.I):
                cells = [strip_tags(td) for td in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr.group(1), re.I)]
                if len(cells) <= obtained_idx: continue
                row_num  = cells[0].strip()
                obtained = cells[obtained_idx].strip()
                if not obtained or obtained in ("-", ""): continue

                # class stats per row — extracted from CSS classes (already in HTML)
                avg_m = re.search(r'class="[^"]*AverageMarks[^"]*"[^>]*>\s*([0-9.]+)', tr.group(1), re.I)
                min_m = re.search(r'class="[^"]*MinMarks[^"]*"[^>]*>\s*([0-9.]+)', tr.group(1), re.I)
                max_m = re.search(r'class="[^"]*MaxMarks[^"]*"[^>]*>\s*([0-9.]+)', tr.group(1), re.I)

                if row_num.lower() in ("total", "grand total", "subtotal"):
                    total_possible = ""
                    if total_idx is not None and total_idx < len(cells):
                        total_possible = cells[total_idx].strip()
                    if weight_idx is not None and weight_idx < len(cells):
                        tw = cells[weight_idx].strip()
                        if tw and tw != obtained:
                            entries[f"{sec_label} Total"] = f"Marks: {obtained} | Weightage total: {tw}"
                            try: sec_total_w[sec_label] = float(tw)
                            except ValueError: pass
                        elif obtained:
                            entries[f"{sec_label} Total"] = f"Marks total: {obtained}" + (f"/{total_possible}" if total_possible else "")
                    elif obtained:
                        entries[f"{sec_label} Total"] = f"Marks total: {obtained}" + (f"/{total_possible}" if total_possible else "")
                    continue

                total     = cells[total_idx].strip() if total_idx is not None and total_idx < len(cells) else ""
                weightage = cells[weight_idx].strip() if weight_idx is not None and weight_idx < len(cells) else ""

                # marks string — clean, no avg/min/max (those go to class_stats only)
                val = f"Marks: {obtained}/{total}" if total else f"Marks: {obtained}"
                if weightage: val += f" | Weightage: {weightage}"
                entries[f"{sec_label} {row_num}"] = val

                # collect class stats for this row, grouped by section for best-off capping
                try:
                    w = float(weightage) if weightage else 0.0
                    a = float(avg_m.group(1)) if avg_m else None
                    mn = float(min_m.group(1)) if min_m else None
                    mx = float(max_m.group(1)) if max_m else None
                    tot = float(total) if total else None
                    if w > 0 and a is not None and mn is not None and mx is not None and tot and tot > 0:
                        if sec_label not in sec_class_rows:
                            sec_class_rows[sec_label] = []
                        sec_class_rows[sec_label].append({
                            "w": w,
                            "avg_pts": round(a / tot * w, 4),
                            "min_pts": round(mn / tot * w, 4),
                            "max_pts": round(mx / tot * w, 4),
                            "obt": float(obtained) if obtained else 0.0,
                            "item": f"{sec_label} {row_num}",
                        })
                except (ValueError, TypeError):
                    pass

        if entries:
            snapshot[clabel] = entries

        # compute obtained_total_w using section totals (same logic as calc_sem_summary)
        # This gives the same "out of" denominator as the Weight: X/Y display
        _sec_totals = {}
        _has_total = set()
        _individual_w = {}
        for item, val in entries.items():
            if not isinstance(val, str): continue
            is_tot = bool(re.search(r'\bTotal\b', item, re.I))
            sec = re.sub(r'\s+(Total|\d+)$', '', item, flags=re.I).strip()
            if is_tot:
                _has_total.add(sec)
                mt = re.search(r'Weightage\s+total:\s*([\d.]+)', val)
                mo = re.search(r'Marks(?:\s+total)?:\s*([\d.]+)', val)
                if mo:
                    obt = float(mo.group(1))
                    tot = float(mt.group(1)) if mt else obt
                    if obt > 0:
                        _sec_totals[sec] = tot
            else:
                mw = re.search(r'Weightage:\s*([\d.]+)', val)
                mm = re.search(r'Marks:\s*[\d.]+', val)
                if mw and mm:
                    if sec not in _individual_w: _individual_w[sec] = 0.0
                    try: _individual_w[sec] += float(mw.group(1))
                    except ValueError: pass
        _obtained_total_w = 0.0
        for sec, tot in _sec_totals.items():
            _obtained_total_w += tot
        for sec, wt in _individual_w.items():
            if sec not in _has_total:
                _obtained_total_w += wt

        # Apply best-off capping per section: if individual rows sum > section total weightage,
        # only take top rows by obtained marks until we fill the section weightage cap.
        # This matches the portal's own best-off logic.
        for sec, rows in sec_class_rows.items():
            cap = sec_total_w.get(sec)
            if cap is None:
                # No section total found — use all rows as-is
                class_rows.extend(rows)
                continue
            # Sort by obtained descending (best-off picks highest scores)
            rows_sorted = sorted(rows, key=lambda r: r["obt"], reverse=True)
            accumulated_w = 0.0
            for r in rows_sorted:
                if accumulated_w >= cap:
                    break
                remaining = cap - accumulated_w
                if r["w"] <= remaining:
                    class_rows.append(r)
                    accumulated_w += r["w"]
                else:
                    # Partial row: scale down to fit remaining cap
                    scale = remaining / r["w"]
                    class_rows.append({
                        "w": round(remaining, 4),
                        "avg_pts": round(r["avg_pts"] * scale, 4),
                        "min_pts": round(r["min_pts"] * scale, 4),
                        "max_pts": round(r["max_pts"] * scale, 4),
                        "obt": r["obt"],
                        "item": r["item"],
                    })
                    accumulated_w += remaining

        # compute correct course-level class avg/min/max using weighted sum
        if class_rows:
            total_w = sum(r["w"] for r in class_rows)
            if total_w > 0:
                c_avg = round(sum(r["avg_pts"] for r in class_rows), 2)
                c_min = round(sum(r["min_pts"] for r in class_rows), 2)
                c_max = round(sum(r["max_pts"] for r in class_rows), 2)
                if clabel in snapshot:
                    snapshot[clabel]["__class_stats__"] = {
                        "avg": c_avg, "min": c_min, "max": c_max,
                        "total_weight": round(total_w, 2),
                        "obtained_total_w": round(_obtained_total_w, 2),
                        "rows": len(class_rows)
                    }
    return snapshot

def diff_marks(old, new):
    changes = []
    for course, entries in new.items():
        old_e = old.get(course, {})
        for item, nv in entries.items():
            if item == "__class_stats__": continue  # never notify on class stats
            if not nv or nv in ("-", ""): continue
            ov = old_e.get(item)
            if ov is None:
                changes.append(f"{course} › {item}: new → {nv}")
            elif ov != nv:
                changes.append(f"{course} › {item}: {ov} → {nv}")
    return changes

def parse_attendance(html):
    snap = {}
    for section in re.finditer(r'<div[^>]+id="(\d+)"[^>]*>([\s\S]*?)(?=<div[^>]+(?:id="\d+"|class="m-scroll)|$)', html, re.I):
        sec_html = section.group(2)
        h5 = re.search(r"<h5>([A-Z]{2,3}\d{3,4})-([^<(]+)", sec_html, re.I)
        if not h5: continue
        code  = h5.group(1).strip()
        name  = h5.group(2).strip().rstrip('-').strip()
        label = f"{code} ({name})" if name else code
        lectures = {}
        for tr in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", sec_html, re.I):
            cells = [strip_tags(td) for td in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr.group(1), re.I)]
            if len(cells) < 4: continue
            date   = cells[1].strip()
            status = cells[3].strip().upper()
            if date and status in ("P", "A", "L"):
                lectures[date] = status
        if lectures:
            snap[label] = lectures
    return snap

def diff_attendance(old, new):
    changes = []
    for course, lectures in new.items():
        old_lectures = old.get(course, {})
        for date, status in lectures.items():
            if date not in old_lectures:
                icon = "ABSENT ⚠️" if status in ("A", "L") else "Present ✅"
                changes.append(f"{course}: {date} → {status} ({icon})")
            elif old_lectures[date] != status:
                changes.append(f"{course}: {date} changed {old_lectures[date]} → {status}")
    return changes

def parse_student_info(html):
    info = {}

    # strategy 1: <span class="m--font-boldest">Label: </span><span>Value</span>
    # covers Roll No, Section, Degree, Campus, Batch, Status, Name, Gender etc
    for m in re.finditer(
        r'<span[^>]*m--font-boldest[^>]*>\s*([^<:]{1,30}):\s*</span>\s*<span[^>]*>\s*([^<]{1,80}?)\s*</span>',
        html, re.I
    ):
        lbl = m.group(1).strip().lower()
        val = m.group(2).strip().rstrip(".,").strip()
        if not val or len(val) < 1: continue
        if "roll" in lbl and "roll_no" not in info:      info["roll_no"] = val
        elif lbl == "name" and "name" not in info:        info["name"] = val
        elif "batch" in lbl and "batch" not in info:      info["batch"] = val
        elif "degree" in lbl and "program" not in info:   info["program"] = val
        elif "campus" in lbl and "campus" not in info:    info["campus"] = val
        elif "section" in lbl and "section" not in info:  info["section"] = val
        elif "status" in lbl and "status" not in info:    info["status"] = val
        elif "arn" in lbl and "arn" not in info:          info["arn"] = val

    # strategy 2: topbar username — most reliable name source
    # <span class="m-topbar__username ..."><span class="m-link">Haris Zahid Abbasi</span>
    m = re.search(r'm-topbar__username[^"]*"[^>]*>.*?<span[^>]*m-link[^>]*>\s*([^<]{2,60}?)\s*</span>', html, re.I | re.DOTALL)
    if m and "name" not in info:
        info["name"] = m.group(1).strip()

    # strategy 3: transcript page header row
    # <div class="col-md-2"><span class="m--font-boldest">ARN: </span><span>2443142</span></div>
    for m in re.finditer(
        r'<span[^>]*m--font-boldest[^>]*>\s*(ARN|Roll No|Name|Batch)\s*:\s*</span>\s*<span[^>]*>\s*([^<]{1,80}?)\s*</span>',
        html, re.I
    ):
        lbl = m.group(1).strip().lower()
        val = m.group(2).strip().rstrip(".,").strip()
        if not val: continue
        if lbl == "arn" and "arn" not in info:            info["arn"] = val
        elif "roll" in lbl and "roll_no" not in info:     info["roll_no"] = val
        elif lbl == "name" and "name" not in info:        info["name"] = val
        elif lbl == "batch" and "batch" not in info:      info["batch"] = val

    return info

def parse_transcript(html):
    """
    Parse NU transcript page chronologically by Semester blocks to avoid cross-table mixups.
    Ensures EVERY course (including non-credit/current courses) is systematically preserved inside 
    its true academic semester node.
    Returns { semester_name: { course_code: {grade, name, credit_hours, type} } }
    """
    snap = {}
    
    # 1. Break the HTML page down by separate distinct semester headers or table container fragments
    # Flex wraps individual blocks inside custom components, class structures, or sequential standalone tables
    semester_blocks = []
    
    # Locate section headings (e.g., "Fall 2024", "Spring 2025") inside the raw response
    headings = list(re.finditer(r'<(?:h3|h4|h5|th|div)[^>]*?>\s*((?:Spring|Fall|Summer)\s*\d{4})\s*</', html, re.I))
    
    if headings:
        for i in range(len(headings)):
            sem_title = headings[i].group(1).strip()
            start_pos = headings[i].end()
            end_pos = headings[i+1].start() if i + 1 < len(headings) else len(html)
            semester_blocks.append((sem_title, html[start_pos:end_pos]))
    else:
        # Fallback tracking counter if precise section strings are missing
        for i, tbl in enumerate(re.finditer(r"<table[^>]*?>([\s\S]*?)</table>", html, re.I)):
            semester_blocks.append((f"Semester {i+1}", tbl.group(0)))

    for sem_title, sem_html in semester_blocks:
        sem_courses = {}
        
        for table in re.finditer(r"<table[^>]*?>([\s\S]*?)</table>", sem_html, re.I):
            thtml = table.group(1)
            header_row = re.search(r"<tr[^>]*?>([\s\S]*?)</tr>", thtml, re.I)
            if not header_row:
                continue
                
            headers = [strip_tags(th).strip().lower() for th in re.findall(r"<t[hd][^>]*?>([\s\S]*?)</t[hd]>", header_row.group(1), re.I)]
            
            def col(keywords):
                for idx, h in enumerate(headers):
                    if any(k in h for k in keywords): return idx
                return None

            code_col   = col(["code"])
            name_col   = col(["course name", "course title", "name"])
            crdhrs_col = col(["crdhrs", "crd", "credit", "ch"])
            grade_col  = col(["grade"])
            type_col   = col(["type"]) # tracking elective/core/non-credit tags

            for row in re.finditer(r"<tr[^>]*?>([\s\S]*?)</tr>", thtml, re.I):
                cells = [strip_tags(td).strip() for td in re.findall(r"<td[^>]*?>([\s\S]*?)</td>", row.group(1), re.I)]
                if len(cells) < 3:
                    continue

                code = None
                if code_col is not None and code_col < len(cells):
                    candidate = cells[code_col].strip()
                    if re.match(r"^[A-Z]{2,3}\d{3,4}$", candidate):
                        code = candidate
                if not code:
                    code = next((c for c in cells if re.match(r"^[A-Z]{2,3}\d{3,4}$", c.strip())), None)
                if not code:
                    continue

                # Credit Hours extraction
                credit_hours = 3
                if crdhrs_col is not None and crdhrs_col < len(cells):
                    ch_str = cells[crdhrs_col].strip()
                    m = re.match(r"^([0-6])(?:\.0)?$", ch_str) # Support 0 CH for non-credit courses
                    if m:
                        credit_hours = int(m.group(1))

                # Course Name extraction
                name = ""
                if name_col is not None and name_col < len(cells):
                    name = cells[name_col].strip()
                else:
                    start = (code_col or 0) + 1
                    for cell in cells[start:]:
                        if len(cell) > 5 and not re.match(r"^[A-Z]{2,3}\d", cell):
                            name = cell
                            break

                # Grade Extraction supporting regular letter grades, non-credit tags, or ongoing status indicators
                grade = "I" # Default to 'In-Progress/Incomplete' for current semesters
                if grade_col is not None and grade_col < len(cells):
                    candidate = cells[grade_col].strip()
                    # Capture letters (A-F), special statuses (W, I, S, U) or standard non-credit outcomes (Pass/Fail)
                    if re.match(r"^[A-F][+-]?$", candidate) or candidate in ("W", "I", "S", "U", "P", "F", "Pass", "Fail"):
                        grade = candidate
                if grade == "I":
                    fallback_grade = next((c.strip() for c in cells if re.match(r"^[A-F][+-]?$", c.strip())), None)
                    if fallback_grade:
                        grade = fallback_grade

                course_type = "Core"
                if type_col is not None and type_col < len(cells):
                    course_type = cells[type_col].strip()

                # Ensure even 0 credit or unfinished courses are logged natively
                sem_courses[code] = {
                    "grade": grade, 
                    "name": name,
                    "credit_hours": credit_hours,
                    "type": course_type
                }
                
        if sem_courses:
            snap[sem_title] = sem_courses

    return snap

def parse_transcript_v1(html):
    """Fallback: simple flattened {code: grade} mapping for total backwards compat."""
    result = parse_transcript(html)
    flattened = {}
    for sem_title, courses in result.items():
        for code, info in courses.items():
            flattened[code] = info["grade"]
    return flattened

def extract_course_numeric_ids(html):
    ids = {}
    # primary: onclick="ftn_calculateMarks('1427')" inside a tab-pane id="AI2002"
    for pane in re.finditer(r'<div[^>]+class="tab-pane[^"]*"[^>]+id="([A-Z]{2,3}\d{3,4})"[^>]*>([\s\S]*?)(?=<div[^>]+class="tab-pane|$)', html, re.I):
        code = pane.group(1)
        pane_html = pane.group(2)
        m = re.search(r"ftn_calculateMarks\(['\"](\d+)['\"]\)", pane_html)
        if m:
            ids[code] = int(m.group(1))
    # fallback: scan all ftn_calculateMarks calls paired with nearby course code
    if not ids:
        for m in re.finditer(r'id="([A-Z]{2,3}\d{3,4})-Grand_Total[^"]*"[\s\S]{1,300}?ftn_calculateMarks\([\'"](\d+)[\'"]\)', html, re.I):
            ids[m.group(1)] = int(m.group(2))
    # fallback2: original JSON-based approach
    for m in re.finditer(r'"CourseId"\s*:\s*(\d+).*?"Code"\s*:\s*"([A-Z]{2,3}\d{3,4})"', html, re.I | re.DOTALL):
        if m.group(2) not in ids:
            ids[m.group(2)] = int(m.group(1))
    return ids

def fetch_class_stats(sess, course_numeric_ids, sem_id):
    if not course_numeric_ids or not sem_id:
        return {}
    stats = {}
    for code, cid in course_numeric_ids.items():
        try:
            payload = json.dumps({"CourseId": cid, "SemID": str(sem_id)})
            html, _ = fetch(sess, BASE + "/Student/GetClassAvg", post_data=payload, json_data=True)
            if not html:
                continue
            data = json.loads(html)
            if data and len(data) > 0:
                d = data[0]
                stats[code] = {
                    "avg": round(float(d.get("CLASS_AVG", 0)), 2),
                    "min": round(float(d.get("CLASS_MIN", 0)), 2),
                    "max": round(float(d.get("CLASS_MAX", 0)), 2),
                    "std": round(float(d.get("CLASS_STD", 0)), 2),
                    "total_weight": round(float(d.get("TOT_WEIGHT", 0)), 2),
                }
        except Exception as e:
            log.debug(f"Class stats for {code}: {e}")
    return stats

def diff_transcript(old, new):
    changes = []
    # Support structural check if deep comparison is parsed, otherwise transparent drop back
    old_flat = {}
    if any(isinstance(v, dict) and "grade" not in v for v in old.values()):
        for s, courses in old.items():
            for c, info in courses.items(): old_flat[c] = info.get("grade") if isinstance(info, dict) else info
    else:
        for c, v in old.items(): old_flat[c] = v.get("grade") if isinstance(v, dict) else v

    new_flat = {}
    if any(isinstance(v, dict) and "grade" not in v for v in new.values()):
        for s, courses in new.items():
            for c, info in courses.items(): new_flat[c] = info.get("grade") if isinstance(info, dict) else info
    else:
        for c, v in new.items(): new_flat[c] = v.get("grade") if isinstance(v, dict) else v

    for c, new_grade in new_flat.items():
        old_grade = old_flat.get(c)
        if old_grade is None:
            changes.append(f"{c}: new grade → {new_grade}")
        elif old_grade != new_grade:
            changes.append(f"{c}: {old_grade} → {new_grade}")
    return changes

#Dashboard Helpers ───
GRADE_POINTS = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0,
}

def calc_gpa(transcript):
    """Calculate cumulative GPA handling nested structured data sheets."""
    total_points = 0.0
    total_credits = 0
    
    # Extract nested dictionary loop if structural block configuration is running
    is_structured = any(isinstance(v, dict) and "grade" not in v for v in transcript.values())
    
    if is_structured:
        for sem, courses in transcript.items():
            for code, info in courses.items():
                g = info.get("grade")
                ch = info.get("credit_hours", 3)
                if g in GRADE_POINTS and ch > 0: # Ensure non-credit courses (0 CH) are omitted from calculation
                    total_points += GRADE_POINTS[g] * ch
                    total_credits += ch
    else:
        for v in transcript.values():
            g = v["grade"] if isinstance(v, dict) else v
            ch = v["credit_hours"] if isinstance(v, dict) else 3
            if g in GRADE_POINTS and ch > 0:
                total_points += GRADE_POINTS[g] * ch
                total_credits += ch
                
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)

def calc_attendance_summary(attendance):
    summary = {}
    for course, lectures in attendance.items():
        total = len(lectures)
        present = sum(1 for s in lectures.values() if s == "P")
        pct = round(present / total * 100, 1) if total else 0
        summary[course] = {"present": present, "total": total, "pct": pct}
    return summary

def required_grade_for_target(current_gpa, current_courses, target_gpa):
    needed = target_gpa * (current_courses + 1) - current_gpa * current_courses
    for grade, pts in sorted(GRADE_POINTS.items(), key=lambda x: -x[1]):
        if pts >= needed:
            min_grade = grade
    for grade, pts in sorted(GRADE_POINTS.items(), key=lambda x: x[1]):
        if pts >= needed:
            return grade, round(needed, 2)
    return None, round(needed, 2)

#Flask Dashboard ─────
def start_dashboard():
    try:
        from flask import Flask, jsonify, request, render_template_string
    except ImportError:
        log.warning("Flask not installed — dashboard unavailable. Run: pip install flask")
        return

    app = Flask(__name__)
    app.logger.disabled = True
    import logging as _logging
    _logging.getLogger("werkzeug").setLevel(_logging.ERROR)

    # HTML string template block omitted inside markdown view to maintain clarity 
    # and match your original template source layout exactly.
    HTML = r""""""

    @app.route("/")
    def index():
        return render_template_string(HTML)

    @app.route("/api/data")
    def api_data():
        state = load_state()
        snaps = state.get("snapshots", {})
        att_summary = calc_attendance_summary(snaps.get("attendance", {}))
        transcript = snaps.get("transcript", {})
        gpa = calc_gpa(transcript) if transcript else None
        notifs = load_notifications()
        return jsonify({
            "snapshots": snaps,
            "att_summary": att_summary,
            "gpa": gpa,
            "notifications": notifs,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    @app.route("/api/gpa_calc")
    def api_gpa_calc():
        try:
            target = float(request.args.get("target", 3.5))
            courses_arg = int(request.args.get("courses", 0))
            state = load_state()
            transcript = state.get("snapshots", {}).get("transcript", {})
            
            is_structured = any(isinstance(v, dict) and "grade" not in v for v in transcript.values())
            flat_count = 0
            if is_structured:
                for s, c in transcript.items(): flat_count += len(c)
            else:
                flat_count = len(transcript)
                
            cur_courses = courses_arg if courses_arg else flat_count
            cur_gpa = calc_gpa(transcript) or 0.0

            if cur_courses == 0:
                needed_pts = target
                grade_map = sorted(GRADE_POINTS.items(), key=lambda x: x[1])
                grade_needed = next((g for g, p in grade_map if p >= needed_pts), None)
                msg = (f"<b>Target GPA:</b> {target}<br>"
                       f"<b>Current courses:</b> 0 (first course)<br>"
                       f"<b>You need:</b> {'<span style=color:var(--green)>' + grade_needed + '</span>' if grade_needed else 'Not achievable'} in your next course")
            else:
                needed = target * (cur_courses + 1) - cur_gpa * cur_courses
                grade_map = sorted(GRADE_POINTS.items(), key=lambda x: x[1])
                grade_needed = next((g for g, p in grade_map if p >= needed), None)
                achievable = needed <= 4.0
                color = "var(--green)" if achievable else "var(--red)"
                msg = (f"<b>Current GPA:</b> {cur_gpa:.2f} over {cur_courses} courses<br>"
                       f"<b>Target GPA:</b> {target}<br>"
                       f"<b>Points needed:</b> {needed:.2f}<br>"
                       f"<b>Minimum grade needed:</b> <span style='color:{color};font-size:1.2rem;font-weight:700'>"
                       f"{'Not achievable — max is 4.0 (A)' if not achievable else grade_needed}</span>")
            return jsonify({"message": msg})
        except Exception as e:
            return jsonify({"message": f"Error: {e}"})

    @app.route("/api/notifications/delete", methods=["POST"])
    def api_delete_notification():
        try:
            idx = request.json.get("index")
            notifs = load_notifications()
            if idx is not None and 0 <= idx < len(notifs):
                notifs.pop(idx)
                NOTIF_FILE.write_text(json.dumps(notifs, indent=2), encoding="utf-8")
                return jsonify({"ok": True, "remaining": len(notifs)})
            return jsonify({"ok": False, "error": "Invalid index"}), 400
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/notifications/delete_before", methods=["POST"])
    def api_delete_before():
        try:
            from datetime import datetime as _dt
            cutoff_str = request.json.get("cutoff")  # ISO string e.g. "2026-05-01 00:00:00"
            cutoff = _dt.strptime(cutoff_str, "%Y-%m-%d %H:%M:%S")
            notifs = load_notifications()
            kept = [n for n in notifs if _dt.strptime(n["time"], "%Y-%m-%d %H:%M:%S") >= cutoff]
            NOTIF_FILE.write_text(json.dumps(kept, indent=2), encoding="utf-8")
            removed = len(notifs) - len(kept)
            return jsonify({"ok": True, "removed": removed, "remaining": len(kept)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    def run_server():
        app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False, use_reloader=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    log.info(f"FlexHub Dashboard started at http://localhost:{DASHBOARD_PORT}")

    def open_browser():
        time.sleep(2)
        try: webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")
        except Exception: pass
    threading.Thread(target=open_browser, daemon=True).start()

#One check cycle ─────
def get_current_sem_id(sess, cached_urls):
    cached = cached_urls.get("sem_id")
    html, final_url = fetch(sess, BASE + "/Student/StudentMarks")
    if not is_logged_in(html, final_url) or not html:
        return cached, html, final_url

    m = re.search(r'<option[^>]+value=["\'](\d{5,6})["\'][^>]*selected', html, re.I)
    if not m:
        m = re.search(r'selected[^>]*value=["\'](\d{5,6})["\']', html, re.I)
    if not m:
        all_ids = re.findall(r'<option[^>]+value=["\'](\d{5,6})["\']', html, re.I)
        if all_ids:
            sem_id = max(all_ids)
            log.info(f"SemId auto-detected (latest): {sem_id}")
            return sem_id, html, final_url

    if m:
        sem_id = m.group(1)
        log.info(f"SemId auto-detected (selected): {sem_id}")
        return sem_id, html, final_url

    fallback = cached or "0"
    log.warning(f"Could not detect SemId — using cached/fallback: {fallback}")
    return fallback, html, final_url

def run_check(sess):
    state  = load_state()
    hashes = state.get("hashes", {})
    snaps  = state.get("snapshots", {})
    urls   = state.get("urls", {})
    new_h, new_s, new_u = dict(hashes), dict(snaps), dict(urls)

    sem_id, html, final_url = get_current_sem_id(sess, urls)
    new_u["sem_id"] = sem_id

    has_marks = html and is_logged_in(html, final_url) and bool(
        re.search(r'href="#[A-Z]{2,3}\d{3,4}"', html or "", re.I))

    if not has_marks and sem_id and sem_id != "0":
        html, final_url = fetch(sess, BASE + "/Student/StudentMarks", post_data={"SemId": sem_id})

    if is_network_error(html, final_url):
        log.warning("Network error — skipping check, will retry next cycle.")
        return "ok"

    if not is_logged_in(html, final_url):
        log.warning("Session expired.")
        return "expired"

    m = re.search(r"StudentAttendance\?semid=(\d+)", html, re.I)
    if m: new_u["attendance"] = BASE + f"/Student/StudentAttendance?semid={m.group(1)}"
    m = re.search(r"/Student/Transcript\?dump=([^\"'\s&]+)", html, re.I)
    if m: new_u["transcript"] = BASE + f"/Student/Transcript?dump={m.group(1)}"

    course_names = extract_course_names(html)
    new_s["course_names"] = {**new_s.get("course_names", {}), **course_names}

    h = page_hash(html)
    # Also force re-parse if cached marks are missing obtained_total_w (old cache format)
    _cached_marks = snaps.get("marks", {})
    _needs_reparse = any(
        isinstance(v, dict) and "__class_stats__" in v and "obtained_total_w" not in v["__class_stats__"]
        for v in _cached_marks.values()
    )
    if "marks" not in hashes or _needs_reparse:
        new_s["marks"] = parse_marks(html, course_names); new_h["marks"] = h
        log.info("Marks: seeded." if "marks" not in hashes else "Marks: re-parsed (cache upgrade).")
    elif h != hashes["marks"]:
        ns = parse_marks(html, course_names)
        changes = diff_marks(snaps.get("marks", {}), ns)
        if changes: notify("📝 Marks Updated!", changes)
        new_s["marks"] = ns; new_h["marks"] = h
    else:
        log.info("Marks: no changes.")

    try:
        numeric_ids = extract_course_numeric_ids(html)
        if numeric_ids:
            class_stats = fetch_class_stats(sess, numeric_ids, sem_id)
            if class_stats:
                existing = new_s.get("class_stats", {})
                existing.update(class_stats)
                new_s["class_stats"] = existing
                log.info(f"Class stats fetched for {len(class_stats)} courses.")
    except Exception as e:
        log.debug(f"Class stats fetch error: {e}")

    att_url = new_u.get("attendance") or urls.get("attendance") or BASE + "/Student/StudentAttendance"
    html, final_url = fetch(sess, att_url)
    if is_logged_in(html, final_url):
        h = page_hash(html)
        if "attendance" not in hashes:
            new_s["attendance"] = parse_attendance(html); new_h["attendance"] = h
            log.info("Attendance: seeded.")
        elif h != hashes["attendance"]:
            ns = parse_attendance(html)
            changes = diff_attendance(snaps.get("attendance", {}), ns)
            if changes: notify("📅 Attendance Updated!", changes)
            new_s["attendance"] = ns; new_h["attendance"] = h
        else:
            log.info("Attendance: no changes.")

    tr_url = new_u.get("transcript") or urls.get("transcript") or TRANSCRIPT_URL
    html, final_url = fetch(sess, tr_url)
    if is_logged_in(html, final_url):
        h = page_hash(html)
        student_info = parse_student_info(html)
        # also fetch home page to get Degree/Campus (only on home, not transcript)
        try:
            home_html, home_url = fetch(sess, BASE + "/")
            if is_logged_in(home_html, home_url):
                home_info = parse_student_info(home_html)
                # merge: home_info fills gaps, transcript_info wins for ARN/Roll/Name/Batch
                merged = {**home_info, **student_info}
                student_info = merged
        except Exception as e:
            log.debug(f"Home page student info fetch: {e}")
        if student_info:
            new_s["student_info"] = student_info
            log.info(f"Student info: {list(student_info.keys())}")
        if "transcript" not in hashes:
            parsed = parse_transcript(html)
            new_s["transcript"] = parsed; new_h["transcript"] = h
            log.info("Transcript: seeded.")
        elif h != hashes["transcript"]:
            ns = parse_transcript(html)
            changes = diff_transcript(snaps.get("transcript", {}), ns)
            if changes: notify("🎓 Grades Updated!", changes)
            new_s["transcript"] = ns; new_h["transcript"] = h
        else:
            log.info("Transcript: no changes.")

    save_state({"hashes": new_h, "snapshots": new_s, "urls": new_u})
    log.info(f"Check done at {datetime.now().strftime('%H:%M:%S')}")

    try:
        gen = SYSTEM_DIR / "generate_dashboard.py" if (SYSTEM_DIR := Path(__file__).parent).exists() else DIR / "generate_dashboard.py"
    except:
        gen = DIR.parent / "_system" / "generate_dashboard.py"
    try:
        import subprocess as _sp
        if gen.exists():
            _sp.Popen([sys.executable, str(gen), "--no-open"], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        (DATA_DIR / "last_update.txt").write_text(str(int(__import__('time').time())), encoding="utf-8")
    except Exception as e:
        log.debug(f"Dashboard regen: {e}")

    return "ok"

#Main
def start_file_server():
    import http.server, socketserver, threading as _th, urllib.parse

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(DIR), **kw)
        def log_message(self, *a): pass

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length else {}
                path = self.path.split("?")[0]

                if path == "/api/notifications/delete":
                    idx = body.get("index")
                    notifs = load_notifications()
                    if idx is not None and 0 <= int(idx) < len(notifs):
                        notifs.pop(int(idx))
                        NOTIF_FILE.write_text(json.dumps(notifs, indent=2), encoding="utf-8")
                        # Regenerate dashboard so indices stay fresh
                        try:
                            import subprocess
                            subprocess.Popen([sys.executable, str(SYSTEM_DIR / 'generate_dashboard.py'), '--no-open'],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception: pass
                        self._json({"ok": True, "remaining": len(notifs)})
                    else:
                        # Index out of range — page is stale, tell client to refresh
                        self._json({"ok": False, "error": f"Index {idx} out of range (only {len(notifs)} notifications). Please refresh the page."}, 400)

                elif path == "/api/notifications/delete_before":
                    from datetime import datetime as _dt
                    cutoff_str = body.get("cutoff")
                    cutoff = _dt.strptime(cutoff_str, "%Y-%m-%d %H:%M:%S")
                    notifs = load_notifications()
                    kept = [n for n in notifs if _dt.strptime(n["time"], "%Y-%m-%d %H:%M:%S") >= cutoff]
                    removed = len(notifs) - len(kept)
                    if removed > 0:
                        NOTIF_FILE.write_text(json.dumps(kept, indent=2), encoding="utf-8")
                        try:
                            import subprocess
                            subprocess.Popen([sys.executable, str(SYSTEM_DIR / 'generate_dashboard.py'), '--no-open'],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception: pass
                    self._json({"ok": True, "removed": removed, "remaining": len(kept)})

                else:
                    self._json({"ok": False, "error": "Not found"}, 404)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)

        def _json(self, data, code=200):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

    def run():
        try:
            with socketserver.TCPServer(("127.0.0.1", DASHBOARD_PORT), Handler) as httpd:
                httpd.allow_reuse_address = True
                log.info(f"Dashboard server: http://localhost:{DASHBOARD_PORT}/dashboard.html")
                httpd.serve_forever()
        except OSError:
            log.debug(f"Port {DASHBOARD_PORT} already in use — skipping file server.")

    _th.Thread(target=run, daemon=True).start()

def main():
    # Prevent duplicate instances (launchd/systemd + manual run both starting)
    _instance_lock_path = DATA_DIR / "instance.lock"
    _instance_lock_fd = None
    try:
        if _platform.system() == "Windows":
            # On Windows use a PID file — msvcrt.locking is unreliable cross-version
            if _instance_lock_path.exists():
                try:
                    old_pid = int(_instance_lock_path.read_text().strip())
                    import ctypes
                    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, old_pid)
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        print("Another instance of Flex Watcher is already running. Exiting.")
                        sys.exit(0)
                except Exception:
                    pass  # PID file stale — continue
            _instance_lock_path.write_text(str(os.getpid()))
        else:
            import fcntl
            _instance_lock_fd = open(_instance_lock_path, "w")
            fcntl.flock(_instance_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        print("Another instance of Flex Watcher is already running. Exiting.")
        sys.exit(0)

    log.info("=" * 50)
    log.info("Flex Watcher started.")
    log.info(f"Checking every {CHECK_MINUTES} minutes.")
    log.info("=" * 50)

    username, password = get_credentials()
    start_file_server()

    while True:
        cookie = get_cookie(username, password)
        if not cookie:
            log.warning("Could not get cookie — retrying in 60 seconds.")
            time.sleep(60)
            continue

        sess = build_session(cookie)
        notify("✅ Flex Watcher Running",
               [f"Monitoring Flex every {CHECK_MINUTES} minutes.",
                f"Dashboard: http://localhost:{DASHBOARD_PORT}",
                "You will be notified of any changes."])

        while True:
            try:
                result = run_check(sess)
                if result == "expired":
                    log.info("Session may have expired — waiting 30s and retrying once...")
                    time.sleep(30)
                    retry = run_check(sess)
                    if retry != "expired":
                        log.info("Session was fine — was just a network glitch.")
                        time.sleep(CHECK_MINUTES * 60)
                        continue
                    if COOKIE_FILE.exists():
                        COOKIE_FILE.unlink()
                    log.info("Re-authenticating with fresh cookie...")
                    break  # breaks inner loop → outer loop calls get_cookie → auto_login
                time.sleep(CHECK_MINUTES * 60)
            except Exception as e:
                log.error(f"Error: {e}", exc_info=True)
                time.sleep(60)

if __name__ == "__main__":
    main()