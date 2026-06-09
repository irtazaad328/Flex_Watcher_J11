"""
Flex Watcher_J11 — Dashboard Generator
Cross-platform (Windows/Mac/Linux). Generic String Normalization Profile Engine.
Run: python generate_dashboard.py
"""
import json, sys, re, webbrowser
from pathlib import Path
from datetime import datetime

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "_data"
STATE_FILE = DATA_DIR / "flex_state.json"
NOTIF_FILE = DATA_DIR / "flex_notifications.json"
OUT_FILE   = ROOT / "dashboard.html"

GRADE_TABLE = [
    (90,101,"A+",4.00),(86,90,"A",4.00),(82,86,"A-",3.67),
    (78,82,"B+",3.33),(74,78,"B",3.00),(70,74,"B-",2.67),
    (66,70,"C+",2.33),(62,66,"C",2.00),(58,62,"C-",1.67),
    (54,58,"D+",1.33),(50,54,"D",1.00),(0,50,"F",0.00),
]
GRADE_POINTS = {r[2]:r[3] for r in GRADE_TABLE}

def pct_to_grade(p):
    import math
    # NU rounds 0.5 up: 75.5 -> 76, not 75
    p = math.floor(p + 0.5)
    for lo,hi,l,_ in GRADE_TABLE:
        if lo<=p<hi: return l
    return "F"

def load_json(p):
    try:
        if Path(p).exists(): return json.loads(Path(p).read_text(encoding="utf-8"))
    except: pass
    return None

def calc_cgpa_weighted(transcript):
    total_pts=0.0; total_ch=0.0
    for v in transcript.values():
        if isinstance(v,dict) and v.get("is_replaced"):
            continue  # old repeat attempt — replaced by newer one
        if isinstance(v,dict) and v.get("is_pending_repeat"):
            continue  # repeat in progress, grade not uploaded yet
        g  = v.get("grade","F") if isinstance(v,dict) else v
        if g in ("I","S","U","W"):  # skip incomplete, non-credit, and withdrawn
            continue
        ch = int(v.get("credit_hours",3)) if isinstance(v,dict) else 3
        ch = max(1, min(ch, 6))
        if g in GRADE_POINTS:
            total_pts += GRADE_POINTS[g]*ch
            total_ch  += ch
    return round(total_pts/total_ch,3) if total_ch>0 else None

def calc_sem_summary(marks):
    results={}
    for course,entries in marks.items():
        sec_totals={}; individual={}; has_total=set()
        for item,val in entries.items():
            if item == "__class_stats__": continue
            if not isinstance(val, str): continue
            is_tot=bool(re.search(r'\bTotal\b',item,re.I))
            sec=re.sub(r'\s+(Total|\d+)$','',item,flags=re.I).strip()
            if is_tot:
                has_total.add(sec)
                mo=re.search(r'Marks(?:\s+total)?:\s*([\d.]+)',val)
                mt=re.search(r'Weightage\s+total:\s*([\d.]+)',val)
                obt=float(mo.group(1)) if mo else 0.0
                tot=float(mt.group(1)) if mt else obt
                sec_totals[sec]=(obt,tot)
            else:
                if sec not in individual: individual[sec]=[]
                mm=re.search(r'Marks:\s*([\d.]+)\s*/\s*([\d.]+)',val)
                mw=re.search(r'Weightage:\s*([\d.]+)',val)
                if mm and mw:
                    individual[sec].append((float(mm.group(1)),float(mm.group(2)),float(mw.group(1))))
        tot_obt=0.0; tot_wt=0.0
        for sec,(o,t) in sec_totals.items():
            if o > 0:  # only count sections where marks have actually been entered
                tot_obt+=o; tot_wt+=t
        for sec,items in individual.items():
            if sec in has_total: continue
            for mo,mt,wt in items:
                if mt>0 and wt>0:
                    tot_obt+=(mo/mt)*wt; tot_wt+=wt
        if tot_wt<=0: continue
        pct=round(tot_obt/tot_wt*100,1)
        rem=round(max(0.0,100.0-tot_wt),2)
        g=pct_to_grade(pct)
        results[course]={"obt":round(tot_obt,2),"tot":round(tot_wt,2),"rem":rem,
                         "pct":pct,"grade":g,"gp":GRADE_POINTS[g]}
    return results

def calc_att(attendance):
    s={}
    for c,lecs in attendance.items():
        tot=len(lecs); pres=sum(1 for x in lecs.values() if x=="P")
        s[c]={"present":pres,"total":tot,"pct":round(pres/tot*100,1) if tot else 0}
    return s

def guess_ch(course_label, tr=None, current_sem_ch=None):
    code = course_label.split()[0] if course_label else ""
    name = course_label.lower()
    if current_sem_ch and code in current_sem_ch:
        return int(current_sem_ch[code])
    if tr:
        for tcode, tv in tr.items():
            if tcode == code or course_label.startswith(tcode):
                return int(tv.get("credit_hours", 3))
    if len(code) >= 2 and code[1] == 'L' and code[0].isalpha():
        return 1
    if "lab" in name:
        return 1
    return 3

def generate(open_browser=True):
    state  = load_json(STATE_FILE) or {}
    notifs = load_json(NOTIF_FILE) or []
    # Count only today's notifications for the badge number
    from datetime import datetime as _dt
    _today = _dt.now().strftime("%Y-%m-%d")
    n_today = sum(1 for n in notifs if n.get("time", "").startswith(_today))
    snaps  = state.get("snapshots",{})
    marks       = snaps.get("marks",{})
    attendance  = snaps.get("attendance",{})
    transcript  = snaps.get("transcript",{})
    cmap        = snaps.get("course_names",{})
    class_stats    = snaps.get("class_stats",{})
    student_info   = snaps.get("student_info",{})
    current_sem_ch = snaps.get("current_sem_ch",{})
    now        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    att_sum = calc_att(attendance)
    sem_sum = calc_sem_summary(marks)

    tr={}
    # detect structure: nested (sem->courses) vs flat (code->info)
    first_val = next(iter(transcript.values()),None) if transcript else None
    nested = isinstance(first_val,dict) and any(isinstance(v,dict) for v in first_val.values())
    if nested:
        _seen = {}
        for sem_name,courses in transcript.items():
            if not isinstance(courses,dict): continue
            for code,val in courses.items():
                if isinstance(val,dict):
                    entry = dict(val)
                    entry["semester"] = sem_name
                else:
                    entry = {"grade":val,"name":cmap.get(code,""),"credit_hours":3,"semester":sem_name}
                if code not in _seen:
                    _seen[code] = 1
                    entry["repeat_attempt"] = 0
                    tr[code] = entry
                else:
                    attempt = _seen[code]
                    prev_entry = dict(tr[code])
                    prev_grade = prev_entry.get("grade","F")
                    # only archive as replaced if the NEW attempt has a real grade
                    # if new grade is still "I" (not uploaded), old grade must keep counting
                    new_grade = entry.get("grade","I")
                    if new_grade not in ("I",) and new_grade in GRADE_POINTS:
                        # real grade uploaded — archive old attempt
                        if attempt == 1:
                            tr[f"{code}_R0"] = prev_entry
                            tr[f"{code}_R0"]["is_replaced"] = True
                        _seen[code] += 1
                        entry["repeat_attempt"] = _seen[code] - 1
                        entry["is_repeat"] = True
                        tr[code] = entry
                    else:
                        # new attempt grade not yet uploaded — keep old entry active, just mark current sem as pending
                        if attempt == 1:
                            tr[f"{code}_pending"] = entry
                            tr[f"{code}_pending"]["is_pending_repeat"] = True
                            tr[f"{code}_pending"]["is_repeat"] = True
                        _seen[code] += 1
    else:
        for code,val in transcript.items():
            if isinstance(val,dict): tr[code]=val
            else: tr[code]={"grade":val,"name":cmap.get(code,""),"credit_hours":3}

    # Collect course codes that are Withdrawn (grade W) in the transcript.
    # Excluded from marks portal, sem summary, SGPA, what-if, and planner.
    # Transcript keys are compact e.g. "DS201"; marks/sem keys may be "DS 201" or "DS201"
    # Normalize by removing spaces for comparison.
    withdrawn_codes = {
        code.replace(" ", "").upper() for code, v in tr.items()
        if (v.get("grade") if isinstance(v, dict) else v) == "W"
    }
    def _norm(course_label):
        return course_label.split()[0].replace(" ", "").upper() if " " not in course_label.split()[0]                else course_label.replace(" ", "").upper().split()[0]
    def _is_withdrawn(course_label):
        # strip spaces from the course code portion and compare
        raw = course_label.split()
        # marks keys look like "DS 201 Theory" or "DS201" — normalize first token+second if numeric
        code = raw[0]
        if len(raw) > 1 and raw[1].isdigit():
            code = raw[0] + raw[1]
        return code.replace(" ", "").upper() in withdrawn_codes

    # Filter sem_sum — removes W courses from SGPA, semester summary, what-if, planner
    sem_sum = {
        course: data for course, data in sem_sum.items()
        if not _is_withdrawn(course)
    }
    # Filter marks portal — W courses still scraped but not displayed
    marks = {
        course: entries for course, entries in marks.items()
        if not _is_withdrawn(course)
    }

    cgpa     = calc_cgpa_weighted(tr)
    sem_qp = sum(v["gp"] * guess_ch(c, tr, current_sem_ch) for c,v in sem_sum.items())
    sem_ch = sum(guess_ch(c, tr, current_sem_ch) for c in sem_sum)
    sgpa   = round(sem_qp/sem_ch, 2) if sem_ch > 0 else None

    cgpa_val = f"{cgpa:.2f}" if cgpa else "—"
    sgpa_val = f"{sgpa:.2f}" if sgpa else "—"
    pcts     = [a["pct"] for a in att_sum.values()]
    avg_att  = f"{sum(pcts)/len(pcts):.1f}%" if pcts else "—"

    def col3(pct):
        return "#8fb87a" if pct>=82 else "#c8922a" if pct>=66 else "#d4614a"

    low=[(c,a) for c,a in att_sum.items() if a["pct"]<80]
    warn_html=""
    if low:
        items="".join(f'<div class="warn-item">⚠ <b>{c}</b>: {a["pct"]}% ({a["present"]}/{a["total"]})</div>' for c,a in low)
        warn_html=f'<div class="warn-box"><div class="warn-ttl">⚠ Low Attendance Summary</div>{items}</div>'

    if notifs:
        rch="".join(f'<div class="chg-item"><span class="chg-t">{n["time"]}</span><b>{n["title"]}</b><br><span class="mut">{" · ".join((n.get("lines") or [])[:3])}</span></div>' for n in notifs[:25])
    else:
        rch='<div class="empty">✨ System state fully synchronized</div>'

    if marks:
        mb=[]
        for course,entries in marks.items():
            cs   = sem_sum.get(course)
            code = course.split()[0]
            # Always prefer inline __class_stats__ (built from assessed rows only,
            # already correctly scaled to weightage points).
            # Fall back to API class_stats only if inline is missing.
            inline_cs = entries.get("__class_stats__")
            cst = inline_cs if inline_cs else class_stats.get(code, {})
            ch   = guess_ch(course, tr, current_sem_ch)
            if cs:
                c3=col3(cs["pct"])
                stats_bar = ""
                # Only show class stats if inline_cs exists — it is built row-by-row
                # from assessed components only, so avg/min/max are meaningful.
                # API fallback (GetClassAvg) covers the full course total and cannot
                # be reliably interpreted mid-semester, so we skip it.
                if inline_cs:
                    avg = inline_cs.get("avg", 0)
                    mn  = inline_cs.get("min", 0)
                    mx  = inline_cs.get("max", 0)
                    tw_display = inline_cs.get("obtained_total_w", cs["tot"])
                    stats_bar=(f'<div class="class-stats-bar">'
                               f'<span class="cs-lbl">Class (out of {tw_display} pts):</span>'
                               f'<span class="cs-item" style="color:#c8922a">⌀ ≈Avg {avg}</span>'
                               f'<span class="cs-sep">·</span>'
                               f'<span class="cs-item" style="color:#f87171">↓ ≈Min {mn}</span>'
                               f'<span class="cs-sep">·</span>'
                               f'<span class="cs-item" style="color:#8fb87a">↑ ≈Max {mx}</span>'
                               f'</div>')
                prog=(f'<div class="cprog">'
                      f'<div class="cprog-meta">'
                      f'<span>Weight: {cs["obt"]}/{cs["tot"]} · Remaining: {cs["rem"]} · <b style="color:#c8922a">{ch} Credit Hours</b></span>'
                      f'<span style="color:{c3}">{cs["pct"]}% → <b>{cs["grade"]}</b></span></div>'
                      f'<div style="display:flex;align-items:center;gap:6px">'
                      f'<div class="pbar"><div class="pfill" style="width:{min(cs["pct"],100)}%;background:{c3}"></div></div></div>'
                      f'{stats_bar}</div>')
            else:
                prog=(f'<div class="cprog">'
                      f'<div class="cprog-meta"><span style="color:#c8922a"><b>{ch} Credit Hours</b></span></div>'
                      f'</div>')

            rows="".join(
                f'<div class="mrow"><span class="mut sm">{k}</span><span class="mval">{v}</span></div>'
                for k,v in entries.items()
                if k != "__class_stats__" and isinstance(v, str)
            )
            real_count = sum(1 for k in entries if k != "__class_stats__")
            mb.append(f'<div class="cblock"><div class="chdr" onclick="this.parentElement.classList.toggle(\'open\')">'
                      f'<span class="cname">{course}</span>'
                      f'<div style="display:flex;align-items:center;gap:8px"><span class="badge">{real_count} Items</span><span class="chev">▼</span></div></div>'
                      f'{prog}<div class="mbody">{rows}</div></div>')
        marks_html="".join(mb)
    else:
        marks_html='<div class="empty"><span class="bi">📝</span><b>No marks tracked.</b></div>'

    if sem_sum:
        rows=""
        for c,v in sem_sum.items():
            c3=col3(v["pct"])
            gc=v["grade"][0] if v["grade"] else "F"
            # Use inline_cs only — built row-by-row from rows where student obtained marks
            # AND weightage are both present. This ensures total_weight, avg, min, max
            # are all over the exact same graded base — no phantom scaling.
            inline_cs = marks.get(c, {}).get("__class_stats__") if marks else None
            if inline_cs:
                tot_w  = inline_cs.get("obtained_total_w", v["tot"])
                cs_avg = inline_cs.get("avg", "—")
                cs_min = inline_cs.get("min", "—")
                cs_max = inline_cs.get("max", "—")
                cs_cell=(f'<td>{tot_w}</td>'
                         f'<td>{v["obt"]}</td>'
                         f'<td>{cs_avg}</td>'
                         f'<td>{cs_min}</td>'
                         f'<td>{cs_max}</td>'
                         f'<td>—</td>')
            else:
                cs_cell='<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>'
            rows+=(f'<tr><td><b>{c}</b></td>{cs_cell}'
                   f'<td><div class="bar-cell"><div class="pbar sm"><div class="pfill" style="width:{min(v["pct"],100)}%;background:{c3}"></div></div>'
                   f'<span style="color:{c3}">{v["pct"]}%</span></div></td>'
                   f'<td><span class="gc gc-{gc}">{v["grade"]}</span></td>'
                   f'<td>{v["gp"]}</td></tr>')
        sem_html=(f'<div class="sgpa-banner">Current Semester SGPA: <b>{sgpa_val}</b></div>'
                  f'<div class="tbl-wrap"><table class="dtbl"><thead><tr>'
                  f'<th>Course</th><th>Total Marks</th><th>Obtained Marks</th><th>Class Average</th><th>Min</th><th>Max</th><th>Std Dev</th>'
                  f'<th>Percentage</th><th>Grade</th><th>Grade Points</th>'
                  f'</tr></thead><tbody>{rows}</tbody></table></div>')
    else:
        sem_html='<div class="empty"><span class="bi">📊</span><b>No current evaluation profiles.</b></div>'

    if att_sum:
        rows=""
        for c,a in att_sum.items():
            c3="#8fb87a" if a["pct"]>=80 else ("#c8922a" if a["pct"]>=70 else "#d4614a")
            bk='badge-ok' if a["pct"]>=80 else 'badge-warn'
            rows+=(f'<tr><td><b>{c}</b></td><td>{a["present"]}</td><td>{a["total"]}</td>'
                   f'<td><div class="bar-cell"><div class="pbar" style="width:140px"><div class="pfill" style="width:{a["pct"]}%;background:{c3}"></div></div>'
                   f'<span style="color:{c3};font-weight:700">{a["pct"]} %</span></div></td>'
                   f'<td><span class="{bk}">{"✓ OK" if a["pct"]>=80 else "⚠ Short"}</span></td></tr>')
        att_html=(f'<div class="tbl-wrap"><table class="dtbl"><thead><tr>'
                  f'<th>Course Title</th><th>Attended</th><th>Total Lectures</th><th>Percentage</th><th>Status</th>'
                  f'</tr></thead><tbody>{rows}</tbody></table></div>')
    else:
        att_html='<div class="empty"><span class="bi">📅</span><b>No attendance entries parsed.</b></div>'

    def gcls(g): return {"A":"gr-A","B":"gr-B","C":"gr-C"}.get(g[0] if g else "","gr-D")

    def sem_sort_key(name):
        # handles "Fall 2024"->2024.1, "Spring 2025"->2025.0, "Semester 1"->1
        m_yr = re.search(r'(Fall|Spring|Summer)\s+(\d{4})', name, re.I)
        if m_yr:
            yr = int(m_yr.group(2))
            sub = {"spring":0,"summer":0.5,"fall":1}.get(m_yr.group(1).lower(),0)
            return yr*10 + sub
        m = re.search(r'(\d+)', name)
        if m: return int(m.group(1))
        return 9999

    NON_CREDIT_GRADES = {"S","U","NC"}  # satisfactory/unsatisfactory/non-credit

    if tr:
        n_done = len([k for k,v in tr.items() if v.get("grade") not in ("I","S","U","NC","W") and not v.get("is_replaced") and not v.get("is_pending_repeat")])
        cgcard = (f'<div class="stat-card ac" style="max-width:260px;margin-bottom:24px">'
                  f'<div class="sc-lbl">Cumulative CGPA</div><div class="sc-val">{cgpa_val}</div>'
                  f'<div class="sc-sub">{n_done} Courses Completed</div></div>') if cgpa else ""

        sem_groups = {}
        for code, v in tr.items():
            g = v.get("grade","F")
            if g == "I": continue  # current sem incomplete - hide entirely
            s_name = v.get("semester","Unassigned")
            if s_name not in sem_groups:
                sem_groups[s_name] = []
            sem_groups[s_name].append((code,v))

        tr_blocks = ""
        sem_num = 0
        for s_name in sorted(sem_groups.keys(), key=sem_sort_key):
            courses = sem_groups[s_name]
            if not courses: continue
            sem_num += 1
            sub_qp = 0.0
            sub_ch = 0  # only credit-bearing
            rows = ""
            for i,(code,v) in enumerate(courses):
                g = v.get("grade","F")
                ch = int(v.get("credit_hours",3))
                is_nc = g in NON_CREDIT_GRADES
                is_replaced = v.get("is_replaced", False)  # old repeat attempt
                is_repeat   = v.get("is_repeat", False)    # newest repeat attempt
                is_withdrawn = (g == "W")
                gp = GRADE_POINTS.get(g,0.0) if not is_nc and not is_withdrawn else 0.0
                # is_replaced only affects CGPA — it still counts in the sem it was taken
                if not is_nc and not is_withdrawn:
                    sub_qp += gp*ch
                    sub_ch += ch
                gc = gcls(g)
                # build display code — strip _R0/_R1 suffix for display
                display_code = code.split("_R")[0] if "_R" in code else code
                if is_replaced:
                    status_html = '<span style="color:var(--mut);font-size:.75rem">Later Repeated ↗</span>'
                    gp_display = f"{gp:.2f}"
                    grade_cell = f'<span class="gc {gc}" style="opacity:0.6">{g}</span>'
                    row_style = ' style="opacity:0.55;"' 
                elif is_nc:
                    status_html = '<span style="color:var(--mut);font-size:.75rem">Non-Credit</span>'
                    gp_display = "—"
                    grade_cell = f'<span class="gc" style="background:rgba(100,116,139,.15);color:var(--mut)">{g}</span>'
                    row_style = ""
                elif g == "W":
                    status_html = '<span style="color:var(--yel);font-size:.75rem">Withdrawn</span>'
                    gp_display = "—"
                    grade_cell = '<span class="gc" style="background:rgba(200,146,42,.12);color:var(--yel)">W</span>'
                    row_style = ' style="opacity:0.65;"'
                else:
                    repeat_tag = ' <span style="color:#a98fd4;font-size:.68rem;background:rgba(169,143,212,.12);padding:1px 5px;border-radius:4px">Repeat</span>' if is_repeat else ""
                    status_html = f'<span style="color:{"var(--grn)" if gp>=1.0 else "var(--red)"};font-weight:600">{"Pass" if gp>=1.0 else "Fail"}</span>{repeat_tag}'
                    gp_display = f"{gp:.2f}"
                    grade_cell = f'<span class="gc {gc}">{g}</span>'
                    row_style = ""
                rows += (
                    f'<tr{row_style}>'
                    f'<td style="color:var(--mut);text-align:center">{i+1}</td>'
                    f'<td style="font-weight:700;color:var(--blu)">{display_code}</td>'
                    f'<td style="color:var(--txt)">{v.get("name","")}</td>'
                    f'<td style="text-align:center;color:var(--mut)">{ch}</td>'
                    f'<td style="text-align:center">{grade_cell}</td>'
                    f'<td style="text-align:center;font-weight:600">{gp_display}</td>'
                    f'<td style="text-align:center">{status_html}</td>'
                    f'</tr>'
                )
            sub_sgpa = f"{sub_qp/sub_ch:.2f}" if sub_ch>0 else "0.00"
            sub_qp_fmt = f"{sub_qp:.2f}"
            tr_blocks += (
                f'<div class="tr-sem-block">'
                f'<div class="tr-sem-hdr">'
                f'<div class="tr-sem-title">Semester {sem_num} &nbsp;<span class="tr-sem-label">{s_name}</span></div>'
                f'<div class="tr-sem-badges">'
                f'<span class="tr-badge-sgpa">SGPA: {sub_sgpa}</span>'
                f'<span class="tr-badge-ch">{sub_ch} Credit Hours</span>'
                f'</div>'
                f'</div>'
                f'<div class="tbl-wrap" style="margin-bottom:0">'
                f'<table class="dtbl">'
                f'<thead><tr>'
                f'<th style="width:40px;text-align:center">#</th>'
                f'<th>Course Code</th>'
                f'<th>Course Title</th>'
                f'<th style="text-align:center">CH</th>'
                f'<th style="text-align:center">Grade</th>'
                f'<th style="text-align:center">Grade Points</th>'
                f'<th style="text-align:center">Status</th>'
                f'</tr></thead>'
                f'<tbody>{rows}</tbody>'
                f'<tfoot><tr>'
                f'<td colspan="3" style="text-align:right;font-size:.78rem;color:var(--mut);padding:10px 20px">Semester Total</td>'
                f'<td style="text-align:center;font-weight:700">{sub_ch} CH</td>'
                f'<td></td>'
                f'<td style="text-align:center;font-weight:700">{sub_qp_fmt}</td>'
                f'<td style="text-align:center"><span style="color:var(--grn);font-weight:700">SGPA {sub_sgpa}</span></td>'
                f'</tr></tfoot>'
                f'</table></div>'
                f'</div>'
            )

        if tr_blocks:
            tr_html = cgcard + tr_blocks
        else:
            tr_html = '<div class="empty"><span class="bi">🎓</span><b>No completed courses yet.</b></div>'
    else:
        tr_html = '<div class="empty"><span class="bi">🎓</span><b>Historical registry clean.</b></div>'

    if notifs:
        notif_cards = ""
        for i, n in enumerate(notifs):
            lines = n.get("lines") or []
            preview_html = "".join(f'<div class="notif-ln">{l}</div>' for l in lines[:6])
            extra_html   = "".join(f'<div class="notif-ln">{l}</div>' for l in lines[6:])
            toggle = (
                f'<div class="notif-extra" id="notif-extra-{i}" style="display:none">{extra_html}</div>'
                f'<button class="notif-toggle" onclick="toggleNotif({i})" id="notif-tog-{i}">▼ Show more ({len(lines)-6})</button>'
            ) if extra_html else ""
            notif_cards += (
                f'<div class="notif-card" id="notif-{i}" data-notif-idx="{i}">'
                f'<div class="notif-card-hdr">'
                f'<div class="notif-ttl">{n["title"]}</div>'
                f'<div style="display:flex;align-items:center;gap:10px">'
                f'<span class="notif-t">{n["time"]}</span>'
                
                f'</div></div>'
                f'<div class="notif-body">{preview_html}{toggle}</div>'
                f'</div>'
            )
        notif_html = notif_cards
    else:
        notif_html='<div class="empty"><span class="bi">🔔</span>No active event logs.</div>'

    whatif_rows = ""
    for course in sem_sum.keys():
        ch   = guess_ch(course, tr, current_sem_ch)
        opts = "".join(
            f'<option value="{gp}">{g}</option>'
            for g,gp in [("A+",4.0),("A",4.0),("A-",3.67),("B+",3.33),("B",3.0),
                         ("B-",2.67),("C+",2.33),("C",2.0),("C-",1.67),
                         ("D+",1.33),("D",1.0),("F",0.0),("I","I"),("S","S"),("U","U"),("NC","NC")])
        whatif_rows += (
            f'<tr>'
            f'<td><b>{course}</b></td>'
            f'<td style="text-align:center">{ch} CH</td>'
            f'<td><select class="wi-sel" data-course="{course}" data-code="{course.split()[0]}" data-ch="{ch}" onchange="calcWhatIf()">'
            f'<option value="">-- Assign Grade Target --</option>{opts}</select></td>'
            f'</tr>'
        )
    if whatif_rows:
        whatif_html = (
            f'<div class="tbl-wrap"><table class="dtbl">'
            f'<thead><tr><th>Course</th>'
            f'<th style="text-align:center">Credit Hours</th>'
            f'<th>Hypothetical Grade</th></tr></thead>'
            f'<tbody>{whatif_rows}</tbody></table></div>'
            f'<div id="wi-result" class="wi-res-box" style="display:none"></div>'
        )
    else:
        whatif_html = '<div class="empty"><span class="bi">🎯</span>Semester definitions uninitialized.</div>'

    n_done   = len([k for k,v in tr.items() if v.get("grade") not in ("I","W")])
    n_sem    = len(sem_sum)
    cgpa_now = cgpa or 0.0
    sgpa_now = sgpa or 0.0
    gp_js    = json.dumps(GRADE_POINTS)
    thr_js   = json.dumps([[r[0],r[2],r[3]] for r in GRADE_TABLE])
    sem_js   = json.dumps({c:{"obt":v["obt"],"tot":v["tot"],"rem":v["rem"],
                               "pct":v["pct"],"grade":v["grade"],"gp":v["gp"],
                               "ch":guess_ch(c, tr, current_sem_ch)} for c,v in sem_sum.items()})
    tr_js    = json.dumps({code:{"name":v.get("name",""),"grade":v.get("grade","F"),
                                  "gp":GRADE_POINTS.get(v.get("grade","F"),0.0),
                                  "ch":int(v.get("credit_hours",3)), "semester":v.get("semester","")} for code,v in tr.items()})
    cs_js    = json.dumps(class_stats)
    si_js    = json.dumps(student_info)

    html = _build_html(
        now=now, cgpa_val=cgpa_val, sgpa_val=sgpa_val, avg_att=avg_att,
        n_notifs=n_today, warn_html=warn_html, rch=rch,
        marks_html=marks_html, sem_html=sem_html, att_html=att_html,
        tr_html=tr_html, notif_html=notif_html,
        n_done=n_done, n_sem=n_sem, cgpa_now=cgpa_now, sgpa_now=sgpa_now,
        gp_js=gp_js, thr_js=thr_js, sem_js=sem_js, tr_js=tr_js, cs_js=cs_js,
        whatif_html=whatif_html, student_info=student_info, si_js=si_js,
        cur_ch_js=json.dumps(current_sem_ch)
    )

    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ dashboard.html generated → {OUT_FILE}")
    if open_browser:
        import webbrowser as wb
        wb.open(OUT_FILE.as_uri())

def _build_html(**d):
    css = """
:root{
  --bg:#0e0a07;--s1:#13100c;--s2:#1a1510;--s3:#221b13;--s4:#2a2118;
  --acc:#c8922a;--ac2:#e07b3a;--ac3:#8fb87a;
  --grn:#8fb87a;--red:#d4614a;--yel:#c8922a;--blu:#7aa8c4;--pur:#a98fd4;
  --txt:#ede0cc;--mut:#7a6a52;--bdr:rgba(200,146,42,.09);
  --r:16px;--r2:10px;
  --glow-acc:0 4px 32px rgba(200,146,42,.08);
}
*{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;}

body::before{
  content:'';position:fixed;inset:0;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 0%,rgba(200,146,42,.04),transparent),
    radial-gradient(ellipse 60% 40% at 80% 100%,rgba(224,123,58,.03),transparent);
  pointer-events:none;z-index:0;
}

.app{display:flex;min-height:100vh;position:relative;z-index:1;}

.sidebar{
  width:260px;
  background:linear-gradient(180deg,#13100c 0%,#0f0d09 100%);
  border-right:1px solid rgba(200,146,42,.1);
  display:flex;flex-direction:column;
  position:fixed;top:0;left:0;height:100vh;z-index:100;
  box-shadow:4px 0 40px rgba(0,0,0,.5);
}
.sb-logo{
  padding:32px 24px 24px;
  border-bottom:1px solid rgba(200,146,42,.08);
  background:linear-gradient(135deg,rgba(200,146,42,.06),transparent);
  position:sticky;top:0;z-index:102;
}
.sb-logo h1{
  font-size:1.25rem;font-weight:800;letter-spacing:-.02em;
  background:linear-gradient(135deg,#e8c97a 0%,#c8922a 60%,#e07b3a 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
.sb-logo small{color:var(--mut);font-size:.65rem;display:block;margin-top:4px;}
.sb-logo .version{
  display:inline-block;margin-top:8px;
  background:rgba(200,146,42,.1);color:#c8922a;
  font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  padding:3px 10px;border-radius:20px;border:1px solid rgba(200,146,42,.18);
}

.sb-scrollable-nav{flex:1;overflow-y:auto;z-index:101;padding-bottom:20px;}

.nav-group{padding:14px 0 4px;}
.nav-label{font-size:.62rem;font-weight:700;color:var(--mut);text-transform:uppercase;
  letter-spacing:.12em;padding:0 24px 8px;}
.nav-item{
  display:flex;align-items:center;gap:14px;
  padding:12px 24px;cursor:pointer;color:var(--mut);
  font-size:.9rem;border-left:3px solid transparent;
  transition:all .2s cubic-bezier(.4,0,.2,1);user-select:none;
}
.nav-item:hover{background:rgba(200,146,42,.04);color:var(--txt);}
.nav-item.active{
  background:linear-gradient(90deg,rgba(200,146,42,.12),rgba(200,146,42,.02));
  color:#e8c97a;border-left-color:#c8922a;font-weight:600;
}
.nav-item.active .nav-icon{
  background:rgba(200,146,42,.18);
  box-shadow:0 0 12px rgba(200,146,42,.15);
}
.nav-icon{
  width:28px;height:28px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:.95rem;background:rgba(255,255,255,.02);
  transition:all .2s;flex-shrink:0;
}
.sb-footer{
  padding:20px 24px;border-top:1px solid rgba(200,146,42,.08);
  font-size:.75rem;color:var(--mut);
  display:flex;align-items:center;gap:10px;
  background:#0f0d09;z-index:102;
}
.dot{width:8px;height:8px;border-radius:50%;background:#8fb87a;
  box-shadow:0 0 8px rgba(143,184,122,.4);animation:pulse 2s infinite;flex-shrink:0;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}

.main{margin-left:260px;padding:40px 48px;flex:1;min-width:0;}
.page{display:none;animation:fadeIn .25s ease;width:100%;}
.page.active{display:block;}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.pg-title{
  font-size:1.75rem;font-weight:800;margin-bottom:6px;letter-spacing:-.02em;
  color:var(--txt);
}
.pg-sub{font-size:.78rem;color:var(--mut);margin-bottom:28px;}

.cards-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:32px;}
.stat-card{
  background:linear-gradient(135deg,var(--s2) 0%,var(--s3) 100%);
  border:1px solid var(--bdr);border-radius:var(--r);padding:24px;
  position:relative;overflow:hidden;
  transition:transform .2s,box-shadow .2s;
}
.stat-card::before{
  content:'';position:absolute;top:0;right:0;
  width:80px;height:80px;border-radius:0 var(--r) 0 80px;
  background:rgba(200,146,42,.04);
}
.stat-card:hover{transform:translateY(-2px);box-shadow:var(--glow-acc);}
.stat-card.ac{border-color:rgba(200,146,42,.2);}
.stat-card.gn{border-color:rgba(143,184,122,.2);}
.sc-lbl{font-size:.7rem;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;font-weight:600;}
.sc-val{font-size:2.4rem;font-weight:800;line-height:1;letter-spacing:-.03em;}
.sc-sub{font-size:.75rem;color:var(--mut);margin-top:8px;}

.warn-box{
  background:linear-gradient(135deg,rgba(212,97,74,.06),rgba(212,97,74,.02));
  border:1px solid rgba(212,97,74,.18);border-radius:var(--r);
  padding:18px 24px;margin-bottom:24px;
}
.warn-ttl{color:var(--red);font-size:.9rem;font-weight:700;margin-bottom:8px;}
.warn-item{font-size:.85rem;padding:4px 0;color:var(--txt);}

.sec-ttl{font-size:.75rem;font-weight:700;color:var(--mut);
  text-transform:uppercase;letter-spacing:.1em;margin:32px 0 16px;
  display:flex;align-items:center;gap:12px;}
.sec-ttl::after{content:'';flex:1;height:1px;background:var(--bdr);}

.chg-item{
  background:var(--s2);border:1px solid var(--bdr);border-radius:var(--r2);
  padding:16px 20px;margin-bottom:10px;font-size:.9rem;
}
.chg-t{color:var(--mut);font-size:.75rem;float:right;}
.mut{color:var(--mut);}.sm{font-size:.82rem;}
.empty{text-align:center;color:var(--mut);padding:64px 20px;}
.bi{font-size:2.5rem;display:block;margin-bottom:12px;}

.cblock{
  background:linear-gradient(135deg,var(--s2),var(--s3));
  border:1px solid var(--bdr);border-radius:var(--r);
  margin-bottom:12px;overflow:hidden;border-bottom:1px solid var(--bdr);
}
.cblock.open{border-color:rgba(200,146,42,.22);box-shadow:var(--glow-acc);}
.chdr{
  padding:18px 24px;cursor:pointer;
  display:flex;justify-content:space-between;align-items:center;
}
.chdr:hover{background:rgba(200,146,42,.03);}
.cname{font-weight:600;font-size:.95rem;}
.badge{background:rgba(200,146,42,.12);color:#c8922a;border-radius:20px;padding:3px 10px;font-size:.75rem;font-weight:600;}
.chev{color:var(--mut);transition:transform .2s;font-size:.8rem;}
.cblock.open .chev{transform:rotate(180deg);}
.mbody{display:none;border-top:1px solid var(--bdr);background:rgba(0,0,0,.12);}
.cblock.open .mbody{display:block;}
.mrow{display:flex;justify-content:space-between;padding:10px 24px;border-bottom:1px solid rgba(255,255,255,.02);font-size:.86rem;}
.mrow:last-child{border-bottom:none;}
.mval{font-weight:500;}
.cprog{padding:12px 24px 14px;background:rgba(200,146,42,.03);border-top:1px solid rgba(200,146,42,.06);}
.cprog-meta{display:flex;justify-content:space-between;font-size:.75rem;color:var(--mut);margin-bottom:8px;}
.pbar{background:rgba(255,255,255,.05);border-radius:20px;height:6px;overflow:hidden;flex:1;}
.pbar.sm{width:100px;height:5px;}
.pfill{height:100%;border-radius:20px;transition:width .4s ease;}
.bar-cell{display:flex;align-items:center;gap:10px;}

.tbl-wrap{overflow-x:auto;border-radius:var(--r);border:1px solid var(--bdr);margin-bottom:24px;background:var(--s2);}
.dtbl{width:100%;border-collapse:collapse;text-align:left;}
.dtbl th{background:var(--s3);padding:14px 20px;
  font-size:.75rem;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;
  border-bottom:1px solid var(--bdr);}
.dtbl td{padding:14px 20px;border-top:1px solid rgba(255,255,255,.02);
  font-size:.88rem;vertical-align:middle;}
.dtbl tr:hover td{background:rgba(200,146,42,.02);}
.badge-ok{background:rgba(143,184,122,.1);color:var(--grn);border-radius:20px;padding:4px 12px;font-size:.75rem;font-weight:700;}
.badge-warn{background:rgba(212,97,74,.1);color:var(--red);border-radius:20px;padding:4px 12px;font-size:.75rem;font-weight:700;}

.gc{border-radius:6px;padding:4px 10px;font-size:.82rem;font-weight:700;display:inline-block;}
.gc-A{background:rgba(143,184,122,.12);color:var(--grn);}
.gc-B{background:rgba(122,168,196,.12);color:var(--blu);}
.gc-C{background:rgba(200,146,42,.12);color:var(--yel);}
.gc-D,.gc-F{background:rgba(212,97,74,.12);color:var(--red);}

.sgpa-banner{
  background:linear-gradient(135deg,rgba(200,146,42,.08),rgba(200,146,42,.03));
  border:1px solid rgba(200,146,42,.15);border-radius:var(--r);
  padding:16px 24px;margin-bottom:20px;font-size:.95rem;
}

.tr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:16px;}
.grade-card{
  background:linear-gradient(135deg,var(--s2),var(--s3));
  border:1px solid var(--bdr);border-radius:var(--r);padding:20px;text-align:center;
}
.gr-code{font-size:.78rem;color:var(--mut);font-weight:700;margin-bottom:4px;}
.gr-name{font-size:.7rem;color:var(--mut);margin-bottom:12px;min-height:32px;line-height:1.3;}
.gr-letter{font-size:2.2rem;font-weight:800;line-height:1;}
.gr-sub{font-size:.72rem;color:var(--mut);margin-top:8px;}
.gr-A{color:var(--grn);} .gr-B{color:var(--blu);} .gr-C{color:var(--yel);} .gr-D{color:var(--red);}

.tr-sem-block{margin-bottom:28px;border-radius:var(--r);overflow:hidden;border:1px solid var(--bdr);}
.tr-sem-hdr{
  display:flex;justify-content:space-between;align-items:center;
  padding:14px 20px;
  background:linear-gradient(90deg,rgba(200,146,42,.08),rgba(224,123,58,.04));
  border-bottom:1px solid var(--bdr);
}
.tr-sem-title{font-size:1rem;font-weight:800;color:var(--txt);}
.tr-sem-label{font-size:.78rem;font-weight:400;color:var(--mut);margin-left:4px;}
.tr-sem-badges{display:flex;gap:8px;align-items:center;}
.tr-badge-sgpa{
  background:rgba(143,184,122,.1);color:var(--grn);
  border:1px solid rgba(143,184,122,.18);
  border-radius:20px;padding:4px 12px;font-size:.78rem;font-weight:700;
}
.tr-badge-ch{
  background:rgba(200,146,42,.1);color:#c8922a;
  border:1px solid rgba(200,146,42,.18);
  border-radius:20px;padding:4px 12px;font-size:.78rem;font-weight:600;
}
.dtbl tfoot td{
  background:rgba(200,146,42,.04);
  border-top:1px solid rgba(200,146,42,.12);
  font-size:.82rem;
}

.calc-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start;}
@media(max-width:960px){.calc-grid{grid-template-columns:1fr;}}
.calc-box{
  background:linear-gradient(135deg,var(--s2),var(--s3));
  border:1px solid var(--bdr);border-radius:var(--r);padding:28px;
}
.calc-box h3{font-size:1.1rem;font-weight:700;margin-bottom:6px;}
.calc-box .calc-desc{font-size:.78rem;color:var(--mut);margin-bottom:20px;line-height:1.4;}
.calc-box label{display:block;font-size:.8rem;color:var(--mut);margin-bottom:6px;font-weight:500;}
.calc-box input{
  width:100%;background:rgba(200,146,42,.03);
  border:1px solid rgba(200,146,42,.12);border-radius:8px;
  padding:10px 14px;color:var(--txt);font-size:.95rem;
  margin-bottom:16px;outline:none;
}
.calc-box input:focus{border-color:rgba(200,146,42,.4);background:rgba(200,146,42,.06);}
.calc-btn{
  background:linear-gradient(135deg,#c8922a,#a8721a);
  color:#fdf3dc;border:none;border-radius:8px;
  padding:12px 24px;font-size:.92rem;font-weight:700;
  cursor:pointer;width:100%;transition:opacity .15s;
}
.calc-btn:hover{opacity:.88;}
.calc-res{
  margin-top:20px;
  background:rgba(200,146,42,.05);border:1px solid rgba(200,146,42,.14);
  border-radius:10px;padding:18px;font-size:.9rem;line-height:1.6;
}
.res-top{margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--bdr);line-height:1.7;}
.calc-tbl{width:100%;border-collapse:collapse;margin-top:10px;}
.calc-tbl th{background:rgba(0,0,0,0.2);padding:10px 14px;color:var(--mut);font-size:.72rem;text-transform:uppercase;}
.calc-tbl td{padding:10px 14px;border-top:1px solid rgba(255,255,255,.03);font-size:.84rem;}

.wi-sel{background:var(--s4);border:1px solid rgba(200,146,42,.12);border-radius:6px;
  color:var(--txt);padding:6px 10px;font-size:.88rem;width:100%;outline:none;}
.wi-res-box{background:rgba(200,146,42,.05);border:1px solid rgba(200,146,42,.14);
  border-radius:var(--r);padding:18px 24px;margin-top:24px;font-size:.92rem;line-height:1.7;}
.class-stats-bar{display:flex;align-items:center;gap:12px;margin-top:8px;
  padding-top:8px;border-top:1px solid rgba(255,255,255,.04);}
.cs-lbl{font-size:.7rem;color:var(--mut);font-weight:700;text-transform:uppercase;}
.cs-item{font-size:.78rem;}
.cs-sep{color:var(--mut);font-size:.7rem;}

.notif-card{
  background:linear-gradient(135deg,var(--s2),var(--s3));
  border:1px solid var(--bdr);border-radius:var(--r);
  margin-bottom:10px;overflow:hidden;transition:opacity .2s;
}
.notif-card-hdr{
  display:flex;justify-content:space-between;align-items:center;
  padding:14px 20px;border-bottom:1px solid rgba(255,255,255,.03);
}
.notif-ttl{font-weight:700;font-size:.95rem;color:var(--txt);}
.notif-t{font-size:.75rem;color:var(--mut);white-space:nowrap;}
.notif-body{padding:12px 20px;font-size:.85rem;color:var(--mut);line-height:1.7;}
.notif-ln{padding:2px 0;}
.notif-toggle{
  background:none;border:none;color:var(--acc);
  font-size:.78rem;font-weight:600;cursor:pointer;
  padding:6px 0 0;display:block;transition:color .15s;
}
.notif-toggle:hover{color:#e8c97a;}
.notif-extra{margin-top:4px;}

@media(max-width:768px){
  .sidebar{width:70px;}
  .sb-logo,.nav-item span,.sb-footer span:not(.dot),.nav-label{display:none;}
  .nav-item{padding:16px;justify-content:center;}
  .main{margin-left:70px;padding:24px;}
  .cards-row{grid-template-columns:1fr;}
  .dtbl th,.dtbl td{padding:10px 12px;font-size:.8rem;}
}
"""

    js = r"""
//  Notification management 
const API = '';


function toggleNotif(idx){
  const extra = document.getElementById('notif-extra-'+idx);
  const btn   = document.getElementById('notif-tog-'+idx);
  if(!extra || !btn) return;
  const open = extra.style.display !== 'none';
  extra.style.display = open ? 'none' : 'block';
  // preserve the "(N)" count in the button label
  const count = btn.textContent.match(/\((\d+)\)/);
  const countStr = count ? ' ('+count[1]+')' : '';
  btn.textContent = open ? ('▼ Show more'+countStr) : '▲ Show less';
}

function updateNotifCount(n){
  const el = document.querySelector('#page-notifications .pg-sub');
  if(el) el.textContent = n+' notifications recorded';
}

function showPage(id,el){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  const targetPage = document.getElementById('page-'+id);
  if(targetPage) targetPage.classList.add('active');
  if(el) el.classList.add('active');
  localStorage.setItem('activeDashboardTab', id);
}

function minGradeForGP(targetGP){
  let best=THR[0];
  for(const r of THR) if(r[2]>=targetGP) best=r;
  return {lo:best[0],letter:best[1],gp:best[2]};
}

function normalizeString(str) {
  if (!str) return '';
  return str.toLowerCase()
    .replace(/^([a-z]{2,4}\s*\d{3,4}[a-z]?)/g, '')
    .replace(/\b(lab|theory|section|sec|spring|fall|summer|semester)\b/gi, '')
    .replace(/[^a-z]/g, '')
    .trim();
}

function genPdf(){
  const name   = STUDENT_INFO.name || 'Student';
  const sid    = STUDENT_INFO.roll_no || '—';
  const batch  = STUDENT_INFO.batch || '—';
  const prog   = STUDENT_INFO.program || STUDENT_INFO.degree || '—';
  const campus = STUDENT_INFO.campus || '—';
  const now    = new Date().toLocaleString('en-GB',{dateStyle:'long',timeStyle:'short'});

  const GP_MAP={'A+':4.0,'A':4.0,'A-':3.67,'B+':3.33,'B':3.0,'B-':2.67,
    'C+':2.33,'C':2.0,'C-':1.67,'D+':1.33,'D':1.0,'F':0.0,'W':0.0};
  const GRADE_COLOR={
    'A+':'#0d47a1','A':'#0d47a1','A-':'#1565c0',
    'B+':'#1976d2','B':'#1976d2','B-':'#1e88e5',
    'C+':'#b45309','C':'#b45309','C-':'#d97706',
    'D+':'#b91c1c','D':'#b91c1c','F':'#991b1b','I':'#6b7280'
  };

  // group by semester preserving order
  const semMap = {};
  const semOrder = [];
  Object.entries(TR_DATA).forEach(([code, v]) => {
    if(v.grade === 'I') return;
    if(v.is_pending_repeat) return;
    const sem = v.semester || 'Unknown';
    if(!semMap[sem]){ semMap[sem] = []; semOrder.push(sem); }
    semMap[sem].push([code, v]);
  });

  // sort semesters chronologically
  function semSort(a){
    const sub = {'spring':1,'summer':2,'fall':3};
    const m = a.match(/(spring|summer|fall)\s*(\d{4})/i);
    if(m) return parseInt(m[2])*10 + (sub[m[1].toLowerCase()]||0);
    const n = a.match(/(\d+)/); return n ? parseInt(n[1]) : 9999;
  }
  semOrder.sort((a,b) => semSort(a) - semSort(b));

  // decide font size based on total course count
  const totalCourses = Object.values(TR_DATA).filter(v => v.grade !== 'I' && !v.is_pending_repeat).length;
  const tblFont = totalCourses > 35 ? '6.5pt' : totalCourses > 25 ? '7.5pt' : totalCourses > 18 ? '8pt' : '9pt';
  const rowPad  = totalCourses > 35 ? '3px 7px' : totalCourses > 25 ? '4px 8px' : '5px 10px';

  let totalQP = 0, totalCH = 0;
  let semBlocksHtml = '';
  let rowNum = 0;

  semOrder.forEach(sem => {
    const entries = semMap[sem];
    if(!entries || !entries.length) return;
    let semQP = 0, semCH = 0, semRows = '';
    entries.forEach(([code, v]) => {
      const displayCode = code.includes('_R') ? code.split('_R')[0] : code;
      const gp = GP_MAP[v.grade] ?? 0;
      const ch = v.ch || 3;
      const gc = GRADE_COLOR[v.grade] || '#111';
      const isReplaced = !!v.is_replaced;
      const isNC = v.grade==='S'||v.grade==='U'||v.grade==='NC';
      if(!isReplaced&&!isNC){ semQP+=gp*ch; semCH+=ch; totalQP+=gp*ch; totalCH+=ch; }
      rowNum++;
      const bg = rowNum%2===0 ? '#eef3fb' : '#ffffff';
      const opacity = isReplaced ? 'opacity:0.5;' : '';
      const strikeStyle = isReplaced ? 'text-decoration:line-through;' : '';
      const repeatedTag = isReplaced ? ' <span style="font-size:6pt;background:#dbeafe;color:#1e40af;padding:1px 4px;border-radius:3px">Repeated</span>' : (v.is_repeat ? ' <span style="font-size:6pt;background:#dbeafe;color:#1e40af;padding:1px 4px;border-radius:3px">Repeat</span>' : '');
      const gpCell = isReplaced ? '—' : isNC ? '—' : gp.toFixed(2);
      const remarkCell = isReplaced ? 'Replaced' : isNC ? 'Non-Credit' : v.grade==='W' ? 'Withdrawn' : gp>=1 ? 'Pass' : 'Fail';
      const remarkColor = isReplaced ? '#64748b' : isNC ? '#64748b' : gp>=1 ? '#155e8a' : '#991b1b';
      const gradeColor = isNC ? '#64748b' : gc;
      semRows += `<tr style="background:${bg};${opacity}">
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;${strikeStyle}">${displayCode}${repeatedTag}</td>
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;${strikeStyle}">${v.name||displayCode}</td>
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;text-align:center">${ch}</td>
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;text-align:center;font-weight:700;color:${gradeColor}">${v.grade}</td>
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;text-align:center">${gpCell}</td>
        <td style="padding:${rowPad};border-bottom:1px solid #dde6f5;text-align:center;color:${remarkColor}">${remarkCell}</td>
      </tr>`;
    });
    const semSgpa = semCH > 0 ? (semQP/semCH).toFixed(2) : '—';
    semBlocksHtml += `
      <tr>
        <td colspan="6" style="background:#1a56b0;-webkit-print-color-adjust:exact;print-color-adjust:exact;color:#fff;font-weight:bold;font-size:${tblFont};padding:4px 10px;letter-spacing:.03em">
          ${sem} &nbsp;·&nbsp; SGPA: ${semSgpa} &nbsp;·&nbsp; ${semCH} Credit Hours
        </td>
      </tr>
      ${semRows}`;
  });

  const cgpa = totalCH > 0 ? (totalQP/totalCH).toFixed(3) : '—';
  const standing = parseFloat(cgpa) >= 2.0 ? 'Good Standing' : 'Academic Probation';
  const standingColor = parseFloat(cgpa) >= 2.0 ? '#155e8a' : '#991b1b';

  const html = `<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><title>Transcript — ${name}</title>
<style>
  @page{size:A4 portrait;margin:1.2cm 1.5cm;}
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Segoe UI',Arial,sans-serif;font-size:${tblFont};color:#111;background:#fff;
    -webkit-print-color-adjust:exact;print-color-adjust:exact;}
  @media screen{
    body{background:#c9d6e3;padding:20px;}
    .page{background:#fff;max-width:21cm;margin:0 auto;padding:1.2cm 1.5cm;box-shadow:0 4px 24px rgba(0,0,0,.25);}
    .no-print{display:block;text-align:center;margin-bottom:16px;}
    .print-btn{background:#1a56b0;color:#fff;border:none;padding:10px 28px;font-size:13px;
      font-weight:bold;border-radius:6px;cursor:pointer;margin-right:8px;}
    .print-btn:hover{background:#1141a0;}
    .close-btn{background:#374151;color:#fff;border:none;padding:10px 28px;font-size:13px;
      font-weight:bold;border-radius:6px;cursor:pointer;}
  }
  @media print{.no-print{display:none!important;} .page{padding:0;}}
  .top-bar{background:#003087;-webkit-print-color-adjust:exact;print-color-adjust:exact;
    color:#fff;padding:11px 16px;text-align:center;font-size:11pt;font-weight:bold;letter-spacing:.03em;}
  .sub-bar{background:#1a56b0;-webkit-print-color-adjust:exact;print-color-adjust:exact;
    color:#e0eaff;padding:4px 16px;text-align:center;font-size:7.5pt;}
  .header-info{text-align:center;padding:5px 0 4px;font-size:7.5pt;color:#555;}
  .doc-title{background:#1a56b0;-webkit-print-color-adjust:exact;print-color-adjust:exact;
    color:#fff;text-align:center;padding:7px;font-size:9.5pt;font-weight:bold;
    letter-spacing:.06em;margin:8px 0;}
  .info-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#c5d8f0;
    border:1px solid #c5d8f0;margin-bottom:10px;}
  .info-cell{background:#f0f6ff;padding:5px 10px;font-size:8pt;}
  .info-cell b{color:#1a56b0;}
  table{width:100%;border-collapse:collapse;}
  th{background:#1a56b0;-webkit-print-color-adjust:exact;print-color-adjust:exact;
    color:#fff;padding:6px 10px;font-size:${tblFont};text-align:left;}
  th.c{text-align:center;}
  .summary-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;
    background:#c5d8f0;border:1px solid #c5d8f0;margin-top:10px;}
  .sum-cell{background:#f0f6ff;padding:7px 12px;font-size:8.5pt;}
  .sum-cell b{color:#1a56b0;}
  .cgpa-box{background:#dbeafe;-webkit-print-color-adjust:exact;print-color-adjust:exact;
    border:2px solid #1a56b0;text-align:center;padding:8px;grid-column:span 1;}
  .cgpa-num{font-size:20pt;font-weight:bold;color:#003087;}
  .cgpa-lbl{font-size:7pt;color:#555;}
  .footer-hr{border:none;border-top:1.5px solid #1a56b0;margin:12px 0 6px;}
  .footer{text-align:center;font-size:7pt;color:#888;font-style:italic;}
</style>
</head><body>
<div class="no-print">
  <button class="print-btn" onclick="window.print()">🖨 Print / Save as PDF</button>
  <button class="close-btn" onclick="window.close()">✕ Close</button>
</div>
<div class="page">
  <div class="top-bar">NATIONAL UNIVERSITY OF COMPUTER AND EMERGING SCIENCES</div>
  <div class="sub-bar">FAST — Foundation for Advancement of Science &amp; Technology | Academic Registry</div>
  <div class="header-info">A.K Brohi Road, H-11/4, Islamabad &nbsp;|&nbsp; www.nu.edu.pk &nbsp;|&nbsp; Campus: ${campus}</div>
  <div class="doc-title">STUDENT ACADEMIC TRANSCRIPT</div>
  <div class="info-grid">
    <div class="info-cell"><b>Student Name:</b> ${name}</div>
    <div class="info-cell"><b>Program:</b> ${prog}</div>
    <div class="info-cell"><b>Roll Number:</b> ${sid}</div>
    <div class="info-cell"><b>Campus:</b> ${campus}</div>
    <div class="info-cell"><b>Batch:</b> ${batch}</div>
    <div class="info-cell"><b>Generated:</b> ${now}</div>
  </div>
  <table>
    <thead><tr>
      <th>Course Code</th>
      <th>Course Title</th>
      <th class="c">CH</th>
      <th class="c">Grade</th>
      <th class="c">Grade Points</th>
      <th class="c">Remarks</th>
    </tr></thead>
    <tbody>${semBlocksHtml}</tbody>
  </table>
  <div class="summary-grid">
    <div class="sum-cell"><b>Total Courses:</b> ${rowNum}</div>
    <div class="sum-cell"><b>Credit Hours:</b> ${totalCH}</div>
    <div class="sum-cell"><b>Quality Points:</b> ${totalQP.toFixed(2)}</div>
    <div class="cgpa-box" style="grid-column:span 1">
      <div class="cgpa-num">${cgpa}</div>
      <div class="cgpa-lbl">Cumulative GPA</div>
    </div>
    <div class="sum-cell"><b>Academic Standing:</b>
      <span style="color:${standingColor};font-weight:bold"> ${standing}</span>
    </div>
    <div class="sum-cell"><b>GPA Scale:</b> 0.000 – 4.000</div>
  </div>
  <hr class="footer-hr">
  <div class="footer">Generated by Flex Watcher — for personal academic planning use only.</div>
</div>
</body></html>`;

  const win = window.open('','_blank','width=900,height=750');
  win.document.write(html);
  win.document.close();
}

function calcCgpa(){
  const target=parseFloat(document.getElementById('cgpa-target').value);
  const res=document.getElementById('cgpa-res');
  if(isNaN(target)||target<0||target>4){alert('Enter CGPA 0-4');return;}

  const NC_GRADES=new Set(["I","S","U","NC"]);
  let ch_done = 0;
  let total_qp_done = 0;
  for (const code in TR_DATA) {
    if (NC_GRADES.has(TR_DATA[code].grade)) continue;
    if (TR_DATA[code].is_replaced) continue;
    if (TR_DATA[code].is_pending_repeat) continue;
    const ch = TR_DATA[code].ch || 3;
    ch_done += ch;
    total_qp_done += (TR_DATA[code].gp * ch);
  }

  let ch_rem = 0;
  let replaced_historical_qp = 0;
  let replaced_historical_ch = 0;
  
  const courses = Object.keys(SEM);
  
  courses.forEach(cc => {
    if (NC_GRADES.has(SEM[cc].grade)) return;
    const semCourseCode = cc.split(' ')[0];
    const ch = (typeof CUR_CH!=='undefined' && CUR_CH[semCourseCode]) || SEM[cc].ch || 3;
    ch_rem += ch;

    if(TR_DATA[semCourseCode] && !NC_GRADES.has(TR_DATA[semCourseCode].grade)){
      replaced_historical_qp += (TR_DATA[semCourseCode].gp * TR_DATA[semCourseCode].ch);
      replaced_historical_ch += TR_DATA[semCourseCode].ch;
    }
  });

  const ch_total = ch_done + ch_rem - replaced_historical_ch;
  const net_historical_qp = total_qp_done - replaced_historical_qp;
  
  const total_needed_qp = target * ch_total;
  const needed_sem_qp = total_needed_qp - net_historical_qp;
  
  let target_sgpa = ch_rem > 0 ? (needed_sem_qp / ch_rem) : 4.0;
  const achievable = target_sgpa <= 4.0 && target_sgpa >= 0;

  let locked_qp = 0;
  let locked_ch = 0;
  let active_ch = 0;

  courses.forEach(cc => {
    const s = SEM[cc];
    if (s.grade === "I") return;
    const semCourseCode = cc.split(' ')[0];
    const ch = (typeof CUR_CH !== 'undefined' && CUR_CH[semCourseCode]) || s.ch || 3;
    if (s.rem <= 0 || s.gp >= 3.67) {
      locked_qp += s.gp * ch;
      locked_ch += ch;
    } else {
      active_ch += ch;
    }
  });

  const remaining_needed_qp = needed_sem_qp - locked_qp;
  let adjusted_baseline = active_ch > 0 ? (remaining_needed_qp / active_ch) : target_sgpa;
  if (adjusted_baseline < 0) adjusted_baseline = 0;
  if (adjusted_baseline > 4.0) adjusted_baseline = 4.0;

  const color = achievable ? '#8fb87a' : '#d4614a';
  let rows = '';

  courses.forEach(cc => {
    const s = SEM[cc];
    const semCourseCode = cc.split(' ')[0];
    const ch = (typeof CUR_CH !== 'undefined' && CUR_CH[semCourseCode]) || s.ch || 3;
    let status = '';
    let stateColor = '#c8922a';
    let action = '';

    if (NC_GRADES.has(s.grade)) {
        rows += `<tr><td><b>${cc}</b></td><td>—</td><td>${s.grade}</td><td><span style="color:var(--mut)">Non-Credit</span></td><td style="font-size:.78rem;color:#94a3b8">Non-credit course. Excluded from CGPA calculation.</td></tr>`;
        return;
    }
    if (s.grade === "I") {
        rows += `<tr><td><b>${cc}</b></td><td>—</td><td>I</td><td><span style="color:var(--mut)">Incomplete</span></td><td style="font-size:.78rem;color:#94a3b8">Pending grade finalization. Excluded from calculation profile.</td></tr>`;
        return;
    }
    let isRepeat = false;
    if(TR_DATA[semCourseCode] && !NC_GRADES.has(TR_DATA[semCourseCode].grade)){
      isRepeat = true;
    }
    const repeatBadge = isRepeat ? ` <span style="color:#a98fd4; font-size:0.7rem; background:rgba(169,143,212,0.15); padding:2px 6px; border-radius:4px;">R-1</span>` : '';

    if (!achievable) {
      stateColor = '#d4614a';
      status = 'Out of Range';
      action = `Ceiling exceeded. Max reachable with 4.00 SGPA is ` + ((net_historical_qp + (4.0 * ch_rem)) / ch_total).toFixed(3);
    }
    else if (s.gp >= target_sgpa && s.gp >= 3.67) {
      stateColor = '#8fb87a';
      status = `Cushion Creator (${s.grade})`;
      const surplus = ((s.gp - target_sgpa) * ch).toFixed(2);
      action = `Generating +${surplus} points. Overwriting old historical drag value.`;
    } 
    else if (s.rem <= 0) {
      stateColor = '#d4614a';
      status = `Locked (${s.grade})`;
      action = 'Evaluations complete. Baseline tracking updated around this node.';
    } 
    else {
      const optimizedTarget = minGradeForGP(adjusted_baseline);
      if (s.gp >= adjusted_baseline) {
        stateColor = '#7aa8c4';
        status = `Safe Zone (${s.grade})`;
        action = 'Cushion insulation active. Keep pace to hit goal target.';
      } else {
        stateColor = '#c8922a';
        const gap = optimizedTarget.lo - s.pct;
        status = 'Adjusted Target: ' + optimizedTarget.letter;
        action = gap > 0 ? `Secure ` + ((gap / s.rem) * 100).toFixed(0) + `% of outstanding items.` : 'Maintain trend profile.';
      }
    }
    rows += `<tr><td><b>${cc}</b>${repeatBadge}</td><td>${s.pct}%</td><td>${s.grade}</td><td><span style="color:${stateColor}">${status}</span></td><td style="font-size:.78rem;color:#94a3b8">${action}</td></tr>`;
  });

  res.style.display = 'block';
  res.innerHTML = `<div class="res-top"><b>Current Effective History:</b> ` + (ch_done > 0 ? (total_qp_done / ch_done).toFixed(3) : '0.000') + `<br>`
    + `<b>Target Cross-Sem CGPA Destination:</b> ` + target.toFixed(2) + ` (${ch_total} Net Lifecycle CH)<br>`
    + `<b>Implied Target SGPA Requirement:</b> <span style="color:${color}; font-weight:700">` + target_sgpa.toFixed(2) + `</span><br>`
    + `<b>Cushion-Adjusted Flexible Class Target:</b> <span style="color:#c8922a; font-weight:700">` + (achievable ? adjusted_baseline.toFixed(3) : 'Infeasible') + `</span></div>`
    + `<div class="tbl-wrap" style="margin-top:14px"><table class="calc-tbl"><thead><tr><th>Course</th><th>Current %</th><th>Grade</th><th>Smart Analysis Status</th><th>Target Optimization Action</th></tr></thead><tbody>` + rows + `</tbody></table></div>`;
}

function onClickGenPdf() {
  genPdf();
}

function calcSgpa(){
  const target = parseFloat(document.getElementById('sgpa-target').value);
  const res = document.getElementById('sgpa-res');
  if(isNaN(target) || target < 0 || target > 4){ alert('Enter SGPA 0-4'); return; }
  
  const courses = Object.keys(SEM);
  let total_sem_ch = 0;
  let locked_qp = 0;
  let locked_ch = 0;
  let active_ch = 0;
  
  courses.forEach(cc => {
    const s = SEM[cc];
    if (s.grade === "I" || s.grade === "S" || s.grade === "U" || s.grade === "NC") return;
    const semCourseCode = cc.split(' ')[0];
    const ch = (typeof CUR_CH !== 'undefined' && CUR_CH[semCourseCode]) || s.ch || 3;
    total_sem_ch += ch;
    
    if (s.rem <= 0 || s.gp >= 3.67) {
      locked_qp += s.gp * ch;
      locked_ch += ch;
    } else {
      active_ch += ch;
    }
  });
  
  const total_needed_qp = target * total_sem_ch;
  const remaining_needed_qp = total_needed_qp - locked_qp;
  
  let adjusted_baseline = active_ch > 0 ? (remaining_needed_qp / active_ch) : target;
  if (adjusted_baseline < 0) adjusted_baseline = 0;
  if (adjusted_baseline > 4.0) adjusted_baseline = 4.0;
  
  let rows = '';
  courses.forEach(cc => {
    const s = SEM[cc];
    const semCourseCode = cc.split(' ')[0];
    const ch = (typeof CUR_CH !== 'undefined' && CUR_CH[semCourseCode]) || s.ch || 3;
    let status = '';
    let stateColor = '#c8922a';
    let action = '';
    
    if (s.grade === "S" || s.grade === "U" || s.grade === "NC") {
        rows += `<tr><td><b>${cc}</b></td><td>—</td><td>${s.grade}</td><td><span style="color:var(--mut)">Non-Credit</span></td><td style="font-size:.78rem;color:#94a3b8">Non-credit course. Excluded from SGPA calculation.</td></tr>`;
        return;
    }
    if (s.grade === "I") {
        rows += `<tr><td><b>${cc}</b></td><td>—</td><td>I</td><td><span style="color:var(--mut)">Incomplete</span></td><td style="font-size:.78rem;color:#94a3b8">Pending evaluation. Hidden from current semester SGPA matrix.</td></tr>`;
        return;
    }
    
    if (s.gp >= target && s.gp >= 3.67) {
      stateColor = '#8fb87a';
      status = `Cushion Creator (${s.grade})`;
      const surplus = ((s.gp - target) * ch).toFixed(2);
      action = `Offloading +${surplus} surplus points to insulate adjacent risks.`;
    } 
    else if (s.rem <= 0) {
      stateColor = '#d4614a';
      status = `Locked (${s.grade})`;
      action = 'Evaluations finalized. Matrix recalculated dynamically.';
    } 
    else {
      const optimizedTarget = minGradeForGP(adjusted_baseline);
      
      if (s.gp >= adjusted_baseline) {
        stateColor = '#7aa8c4'; 
        status = `Safe Zone (${s.grade})`;
        action = 'Cushion compensation applied. Retain current velocity to secure target.';
      } else {
        stateColor = '#c8922a';
        const gap = optimizedTarget.lo - s.pct;
        status = 'Adjusted Target: ' + optimizedTarget.letter;
        action = gap > 0 ? `Secure ` + ((gap / s.rem) * 100).toFixed(0) + `% of outstanding weight items.` : 'Minor structural adjustment needed.';
      }
    }
    
    rows += `<tr><td><b>${cc}</b></td><td>${s.pct}%</td><td>${s.grade}</td><td><span style="color:${stateColor}">${status}</span></td><td style="font-size:.78rem;color:#94a3b8">${action}</td></tr>`;
  });
  
  res.style.display = 'block';
  res.innerHTML = `<div class="res-top"><b>Target Semester SGPA Matrix:</b> ` + target.toFixed(2) + `<br>` +
    `<b>Current Track Projection:</b> ` + SGPA_NOW.toFixed(2) + `<br>` +
    `<b>Cushion-Adjusted Benchmark for flexible classes:</b> <span style="color:#c8922a; font-weight:700">` + adjusted_baseline.toFixed(3) + `</span></div>` +
    `<div class="tbl-wrap" style="margin-top:14px"><table class="calc-tbl"><thead><tr><th>Course</th><th>Current %</th><th>Grade</th><th>Smart Analysis Status</th><th>Target Optimization Action</th></tr></thead><tbody>` + rows + `</tbody></table></div>`;
}

function calcWhatIf(){
  const NC_GRADES = new Set(["I","S","U","NC"]);
  const sels=document.querySelectorAll('.wi-sel');
  let sem_qp=0,sem_ch=0,filled=0;
  sels.forEach(sel=>{
    if(NC_GRADES.has(sel.value) || sel.value==="") return;
    const gp=parseFloat(sel.value);
    const ch=parseInt(sel.dataset.ch)||3;
    if(!isNaN(gp)){sem_qp+=gp*ch;sem_ch+=ch;filled++;}
  });
  const el=document.getElementById('wi-result');
  if(filled===0){el.style.display='none';return;}
  const sgpa=sem_ch>0?sem_qp/sem_ch:0;

  // build past CGPA base — skip non-credit and incomplete
  let total_tr_qp=0,total_tr_ch=0;
  for(const code in TR_DATA){
    const d=TR_DATA[code];
    if(NC_GRADES.has(d.grade)) continue;
    if(d.is_replaced||d.is_pending_repeat) continue;
    total_tr_qp+=(d.gp*(d.ch||3));
    total_tr_ch+=(d.ch||3);
  }

  // subtract any what-if course that already exists in past transcript (repeat scenario)
  let replaced_ch=0,replaced_qp=0;
  sels.forEach(sel=>{
    if(NC_GRADES.has(sel.value)||sel.value==="") return;
    const code=sel.dataset.code||"";
    if(code && TR_DATA[code] && !NC_GRADES.has(TR_DATA[code].grade)){
      replaced_ch+=(TR_DATA[code].ch||3);
      replaced_qp+=(TR_DATA[code].gp*(TR_DATA[code].ch||3));
    }
  });

  const final_ch=total_tr_ch+sem_ch-replaced_ch;
  const final_qp=total_tr_qp+sem_qp-replaced_qp;
  const cgpa=final_ch>0?(final_qp/final_ch):sgpa;

  const sc=g=>g>=3.5?'#8fb87a':g>=3.0?'#c8922a':g>=2.5?'#c8922a':'#d4614a';
  el.style.display='block';
  el.innerHTML='<b>Simulated Semester SGPA: </b><span style="color:'+sc(sgpa)+';font-size:1.35rem;font-weight:800">'+sgpa.toFixed(2)+'</span> &nbsp;&nbsp;&nbsp;&nbsp;'
    +'<b>Projected Profile CGPA: </b><span style="color:'+sc(cgpa)+';font-size:1.35rem;font-weight:800">'+cgpa.toFixed(3)+'</span><br>'
    +'<span style="color:#64748b;font-size:.78rem">'+filled+' courses assigned · '+sem_ch+' sem CH · based on '+total_tr_ch+' past CH</span>';
}

function initFormValues() {
  const pName = document.getElementById('pdf-name');
  const pId = document.getElementById('pdf-id');
  const pProg = document.getElementById('pdf-prog');
  const pCampus = document.getElementById('pdf-campus');
  
  if (pName) pName.placeholder = STUDENT_INFO.name || 'Dynamic Student';
  if (pId) pId.placeholder = STUDENT_INFO.roll_no || 'Identity Registry';
  if (pProg) pProg.value = STUDENT_INFO.program || STUDENT_INFO.degree || '\u2014';
  if (pCampus) pCampus.value = STUDENT_INFO.campus || 'Dynamic Node Location';

  var cgpaEl = document.getElementById('cgpa-target');
  var sgpaEl = document.getElementById('sgpa-target');
  var sv1 = localStorage.getItem('fw_cgpa_target');
  var sv2 = localStorage.getItem('fw_sgpa_target');
  if (cgpaEl && sv1 !== null) cgpaEl.value = sv1;
  if (sgpaEl && sv2 !== null) sgpaEl.value = sv2;
  if (cgpaEl) cgpaEl.addEventListener('input', function(){ localStorage.setItem('fw_cgpa_target', this.value); });
  if (sgpaEl) sgpaEl.addEventListener('input', function(){ localStorage.setItem('fw_sgpa_target', this.value); });
}
"""

    html = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Flex Watcher_J11</title>"
        f"<style>{css}</style></head><body>"
        "<div class='app'>"
        "<nav class='sidebar'>"
        "<div class='sb-logo'><h1>Flex Watcher_J11</h1>"
        f"<small>Compilation Node: {d['now']}</small>"
        "<span class='version'>Academic Core</span></div>"
        "<div class='sb-scrollable-nav'>"
        "<div class='nav-group'><div class='nav-label'>Main</div>"
        "<div id='nav-dashboard' class='nav-item' onclick='showPage(\"dashboard\",this)'><div class='nav-icon'>🏠</div><span>Dashboard</span></div>"
        "<div id='nav-marks' class='nav-item' onclick='showPage(\"marks\",this)'><div class='nav-icon'>📝</div><span>Marks</span></div>"
        "<div id='nav-semester' class='nav-item' onclick='showPage(\"semester\",this)'><div class='nav-icon'>📊</div><span>Semester Summary</span></div>"
        "</div><div class='nav-group'><div class='nav-label'>Records</div>"
        "<div id='nav-attendance' class='nav-item' onclick='showPage(\"attendance\",this)'><div class='nav-icon'>📅</div><span>Attendance</span></div>"
        "<div id='nav-transcript' class='nav-item' onclick='showPage(\"transcript\",this)'><div class='nav-icon'>🎓</div><span>Transcript</span></div>"
        "</div><div class='nav-group'><div class='nav-label'>Tools</div>"
        "<div id='nav-gpa' class='nav-item' onclick='showPage(\"gpa\",this)'><div class='nav-icon'>🧮</div><span>GPA Calculator</span></div>"
        "<div id='nav-notifications' class='nav-item' onclick='showPage(\"notifications\",this)'><div class='nav-icon'>🔔</div><span>Notifications</span></div>"
        "<div id='nav-whatif' class='nav-item' onclick='showPage(\"whatif\",this)'><div class='nav-icon'>🎯</div><span>What If?</span></div>"
        "</div>"
        "</div>"
        "<div class='sb-footer'><span class='dot'></span><span>Live</span></div>"
        "</nav>"
        "<main class='main'>"
        "<div id='page-dashboard' class='page'>"
        "<div class='app-title' style='display:none'>Flex Watcher</div>"
        "<div class='pg-title'>Dashboard</div>"
        f"<div class='pg-sub'>Last synced: {d['now']}</div>"
        "<div id='student-profile-card' style='"
        "background:linear-gradient(135deg,rgba(200,146,42,.1),rgba(224,123,58,.07));"
        "border:1px solid var(--bdr);border-radius:var(--r);padding:20px 24px;"
        "margin-bottom:24px;display:flex;align-items:center;gap:20px;flex-wrap:wrap'>"
        "<div style='width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#c8922a,#7aa8c4);"
        "display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0'>🎓</div>"
        "<div style='flex:1;min-width:200px'>"
        "<div id='si-name' style='font-size:1.2rem;font-weight:800;color:var(--txt);margin-bottom:4px'>—</div>"
        "<div style='display:flex;gap:16px;flex-wrap:wrap;margin-top:6px'>"
        "<span style='font-size:.8rem;color:var(--mut)'>Roll No: <b id='si-roll' style='color:var(--txt)'>—</b></span>"
        "<span style='font-size:.8rem;color:var(--mut)'>Batch: <b id='si-batch' style='color:var(--txt)'>—</b></span>"
        "<span style='font-size:.8rem;color:var(--mut)'>Program: <b id='si-prog' style='color:var(--blu)'>—</b></span>"
        "<span style='font-size:.8rem;color:var(--mut)'>Campus: <b id='si-campus' style='color:var(--txt)'>—</b></span>"
        "</div></div></div>"
        "<div class='cards-row'>"
        f"<div class='stat-card ac'><div class='sc-lbl'>CURRENT CGPA</div><div class='sc-val'>{d['cgpa_val']}</div><div class='sc-sub'>Overall</div></div>"
        f"<div class='stat-card gn'><div class='sc-lbl'>PREDICTED SGPA</div><div class='sc-val'>{d['sgpa_val']}</div><div class='sc-sub'>This Semester</div></div>"
        f"<div class='stat-card'><div class='sc-lbl'>Attendance</div><div class='sc-val'>{d['avg_att']}</div><div class='sc-sub'>Average</div></div>"
        f"<div class='stat-card'><div class='sc-lbl'>Notifications</div><div class='sc-val'>{d['n_notifs']}</div><div class='sc-sub'>Total Logs Today</div></div>"
        "</div>"
        f"{d['warn_html']}"
        "<div class='sec-ttl'>Recent Changes</div>"
        f"{d['rch']}</div>"
        "<div id='page-marks' class='page'>"
        "<div class='pg-title'>Marks</div>"
        f"<div class='pg-sub'>Click a course to expand · Last updated: {d['now']}</div>"
        f"{d['marks_html']}</div>"
        "<div id='page-semester' class='page'>"
        "<div class='pg-title'>Semester Summary</div>"
        f"<div class='pg-sub'>Based on marks entered so far · Last updated: {d['now']}</div>"
        f"{d['sem_html']}</div>"
        "<div id='page-attendance' class='page'>"
        "<div class='pg-title'>Attendance</div>"
        f"<div class='pg-sub'>Last updated: {d['now']}</div>"
        f"{d['att_html']}</div>"
        "<div id='page-transcript' class='page'>"
        "<div class='pg-title'>Transcript</div>"
        f"<div class='pg-sub'>Cumulative CGPA: {d['cgpa_val']}</div>"
        "<div id='tr-arn-bar' style='display:none;"
        "background:rgba(200,146,42,.08);border:1px solid rgba(200,146,42,.2);"
        "border-radius:10px;padding:10px 18px;margin-bottom:18px;"
        "font-size:.85rem;color:var(--mut)'>"
        "ARN: <b id='tr-arn-val' style='color:var(--txt);font-size:.95rem'>—</b>"
        "</div>"
        "<button class='calc-btn' style='max-width:240px;margin-bottom:20px' onclick='onClickGenPdf()'>📄 Export Report</button>"
        f"{d['tr_html']}</div>"
        "<nav id='page-gpa' class='page'>"
        "<div class='pg-title'>GPA Calculator</div>"
        f"<div class='pg-sub'>CGPA: {d['cgpa_val']} ({d['n_done']} courses) · Semester SGPA: {d['sgpa_val']} ({d['n_sem']} courses)</div>"
        "<div class='calc-grid'>"
        "<div class='calc-box'><h3>🎯 CGPA Target Calculator</h3>"
        "<div class='calc-desc'>Calculates the minimum grade you need in your next course to reach your target CGPA.</div>"
        "<label>Target CGPA (0.00 – 4.00)</label>"
        "<input type='number' id='cgpa-target' min='0' max='4' step='0.01' placeholder='e.g. 3.20'>"
        "<button class='calc-btn' onclick='calcCgpa()'>Calculate</button>"
        "<div class='calc-res' id='cgpa-res'></div></div>"
        "<div class='calc-box'><h3>📈 SGPA Target Calculator</h3>"
        "<div class='calc-desc'>Calculates the minimum grades needed this semester to reach your target SGPA.</div>"
        "<label>Target SGPA (0.00 – 4.00)</label>"
        "<input type='number' id='sgpa-target' min='0' max='4' step='0.01' placeholder='e.g. 3.50'>"
        "<button class='calc-btn' onclick='calcSgpa()'>Calculate</button>"
        "<div class='calc-res' id='sgpa-res'></div></div>"
        "</div></nav>"
        "<div id='page-transcript_pdf' class='page'><div class='pg-title'>Export Transcript PDF</div><div class='pg-sub'>Generate a PDF copy of your transcript</div><div class='calc-box' style='max-width:500px'><h3>📄 Transcript PDF Export</h3><div class='calc-desc'>Downloads a PDF summary of your academic record.</div><label>Student Name</label><input type='text' id='pdf-name' placeholder='' disabled><label>Student ID</label><input type='text' id='pdf-id' placeholder='' disabled><label>Program</label><input type='text' id='pdf-prog' value='' disabled><label>Campus</label><input type='text' id='pdf-campus' value='' disabled><button class='calc-btn' onclick='onClickGenPdf()'>📥 Generate PDF</button><div class='calc-res' id='pdf-res'></div></div></div>"
        "<div id='page-whatif' class='page'>"
        "<div class='pg-title'>🎯 What If? Grade Simulator</div>"
        "<div class='pg-sub'>See how different grades would affect your SGPA this semester.</div>"
        f"{d['whatif_html']}"
        "</div>"
        "<div id='page-notifications' class='page'>"
        "<div class='pg-title'>Notifications</div>"
        f"<div class='pg-sub'>{d['n_notifs']} notifications recorded</div>"
        ""
        f"{d['notif_html']}</div>"
        "</main></div>"
        "<script>"
        f"const CGPA_NOW={d['cgpa_now']};"
        f"const SGPA_NOW={d['sgpa_now']};"
        f"const N_DONE={d['n_done']};"
        f"const N_SEM={d['n_sem']};"
        f"const GP={d['gp_js']};"
        f"const THR={d['thr_js']};"
        f"const SEM={d['sem_js']};"
        f"const TR_DATA={d['tr_js']};"
        f"const CLASS_STATS={d['cs_js']};"
        f"const CUR_CH={d['cur_ch_js']};"
        f"const STUDENT_INFO={d['si_js']};"
        + js +
        f"const _GENERATED='{d['now']}';"
        r"""
(function(){
  const savedTab = localStorage.getItem('activeDashboardTab') || 'dashboard';
  const targetNav = document.getElementById('nav-' + savedTab);
  showPage(savedTab, targetNav);
  initFormValues();

  // populate student profile card
  var si = STUDENT_INFO || {};
  var nameEl   = document.getElementById('si-name');
  var rollEl   = document.getElementById('si-roll');
  var batchEl  = document.getElementById('si-batch');
  var progEl   = document.getElementById('si-prog');
  var campusEl = document.getElementById('si-campus');
  if(nameEl)   nameEl.textContent   = si.name   || '—';
  if(rollEl)   rollEl.textContent   = si.roll_no || '—';
  if(batchEl)  batchEl.textContent  = si.batch   || '—';
  if(progEl)   progEl.textContent   = si.program || si.degree || '—';
  if(campusEl) campusEl.textContent = si.campus  || '—';

  // populate ARN bar on transcript page
  var arnBar = document.getElementById('tr-arn-bar');
  var arnVal = document.getElementById('tr-arn-val');
  if(si.arn && arnBar && arnVal){
    arnVal.textContent = si.arn;
    arnBar.style.display = 'block';
  }

  var CHECK_URL = 'http://localhost:5000/_data/last_update.txt';
  var _lastTs = null;
  function checkUpdate(){
    fetch(CHECK_URL+'?t='+Date.now(),{cache:'no-store'})
      .then(function(r){ return r.text(); })
      .then(function(ts){
        ts = ts.trim();
        if(_lastTs === null){ _lastTs = ts; return; }
        if(ts !== _lastTs){ _lastTs = ts; location.reload(); }
      })
      .catch(function(){});
  }
  setInterval(checkUpdate, 15000);
  checkUpdate();
})();
"""
        "</script></body></html>"
    )
    return html

if __name__=="__main__":
    generate(open_browser="--no-open" not in sys.argv)
