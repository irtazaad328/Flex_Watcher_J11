"""
Flex Watcher_J11 — Professional Transcript PDF Generator
Generates a university-style official transcript PDF dynamically locked to a single page.
Requires: pip install reportlab
"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "_data"
STATE_FILE = DATA_DIR / "flex_state.json"
OUT_DIR    = ROOT / "_data"

GRADE_TABLE = [
    (90,101,"A+",4.00),(86,90,"A",4.00),(82,86,"A-",3.67),
    (78,82,"B+",3.33),(74,78,"B",3.00),(70,74,"B-",2.67),
    (66,70,"C+",2.33),(62,66,"C",2.00),(58,62,"C-",1.67),
    (54,58,"D+",1.33),(50,54,"D",1.00),(0,50,"F",0.00),
]
GRADE_POINTS = {r[2]:r[3] for r in GRADE_TABLE}

def ensure_reportlab():
    try:
        import reportlab
        return True
    except ImportError:
        print("Installing reportlab...")
        subprocess.run([sys.executable,"-m","pip","install","reportlab","--quiet"], check=True)
        return True

def load_json(p):
    try:
        if Path(p).exists(): return json.loads(Path(p).read_text(encoding="utf-8"))
    except: pass
    return None

def calc_cgpa(transcript):
    total_pts=total_ch=0.0
    for v in transcript.values():
        g=v["grade"] if isinstance(v,dict) else v
        ch=v.get("credit_hours",3) if isinstance(v,dict) else 3
        if g in GRADE_POINTS:
            total_pts+=GRADE_POINTS[g]*ch; total_ch+=ch
    return (round(total_pts/total_ch,3),total_ch) if total_ch>0 else (None,0)

def generate_pdf(student_name="", student_id="", program="BS Computer Science", campus="Islamabad"):
    ensure_reportlab()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable)
    from reportlab.lib.enums import TA_CENTER

    state = load_json(STATE_FILE)
    if not state:
        print("No flex_state.json found. Run the watcher first.")
        return

    transcript   = state.get("snapshots",{}).get("transcript",{})
    student_info = state.get("snapshots",{}).get("student_info",{})
    if not transcript:
        print("No transcript data found.")
        return

    if not student_name: student_name = student_info.get("name","")
    if not student_id:   student_id   = student_info.get("roll_no","") or student_info.get("arn","")
    batch   = student_info.get("batch","")

    cgpa, total_ch = calc_cgpa(transcript)
    now = datetime.now()
    out_path = OUT_DIR / f"Transcript_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    OUT_DIR.mkdir(exist_ok=True)

    # Colors
    NU_GREEN   = colors.HexColor("#006633")
    NU_GOLD    = colors.HexColor("#C8A951")
    NU_DARK    = colors.HexColor("#1a2235")
    LIGHT_GRAY = colors.HexColor("#f5f5f5")
    MED_GRAY   = colors.HexColor("#666666")
    TABLE_HDR  = colors.HexColor("#00441f")
    ALT_ROW    = colors.HexColor("#f0f7f3")

    # Dynamic Layout Scaling (The One-Page Guarantee) 
    num_courses = len(transcript)
    font_size = 7.5
    row_padding = 2.2
    spacer_mult = 1.0
    
    if num_courses > 25:
        font_size = 6.5
        row_padding = 1.2
        spacer_mult = 0.4
    elif num_courses > 20:
        font_size = 7.0
        row_padding = 1.6
        spacer_mult = 0.7

    # Aggressive structural margins
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        rightMargin=1.0*cm, leftMargin=1.0*cm,
        topMargin=0.8*cm, bottomMargin=0.8*cm
    )
    W, H = A4
    content_w = W - 2.0*cm

    styles = getSampleStyleSheet()

    s_uni_addr = ParagraphStyle("uni_addr", parent=styles["Normal"], alignment=TA_CENTER,
                                fontSize=font_size, textColor=MED_GRAY)
    s_footer   = ParagraphStyle("footer",   parent=styles["Normal"], alignment=TA_CENTER,
                                fontSize=6.5, textColor=MED_GRAY)
    s_watermark= ParagraphStyle("wm",       parent=styles["Normal"], alignment=TA_CENTER,
                                fontSize=6.5, textColor=colors.HexColor("#aaaaaa"), fontName="Helvetica-Oblique")

    elems = []

    # Header 
    header_data = [
        ["NATIONAL UNIVERSITY OF COMPUTER AND EMERGING SCIENCES"],
        ["FAST — Foundation for Advancement of Science and Technology  |  Chartered University"]
    ]
    header_tbl = Table(header_data, colWidths=[content_w])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), NU_GREEN),
        ("TEXTCOLOR",     (0,0),(0,0), colors.white),
        ("FONTNAME",      (0,0),(0,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(0,0), 11),
        ("TOPPADDING",    (0,0),(0,0), 6 * spacer_mult),
        ("BOTTOMPADDING", (0,0),(0,0), 6 * spacer_mult),
        ("ALIGN",         (0,0),(0,0), "CENTER"),
        
        ("BACKGROUND",    (0,1),(0,1), NU_GOLD),
        ("TEXTCOLOR",     (0,1),(0,1), colors.white),
        ("FONTNAME",      (0,1),(0,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1),(0,1), font_size),
        ("TOPPADDING",    (0,1),(0,1), 3 * spacer_mult),
        ("BOTTOMPADDING", (0,1),(0,1), 3 * spacer_mult),
        ("ALIGN",         (0,1),(0,1), "CENTER"),
    ]))
    elems.append(header_tbl)
    elems.append(Spacer(1, 3 * spacer_mult))

    elems.append(Paragraph(f"Campus: {campus}  |  HQ: A.K Brohi Road, H-11/4, Islamabad, Pakistan | www.nu.edu.pk", s_uni_addr))
    elems.append(Spacer(1, 3 * spacer_mult))

    title_data = [["OFFICIAL ACADEMIC TRANSCRIPT"]]
    title_tbl  = Table(title_data, colWidths=[content_w])
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), NU_DARK),
        ("TEXTCOLOR",     (0,0),(0,0), colors.white),
        ("FONTNAME",      (0,0),(0,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(0,0), font_size + 1.5),
        ("TOPPADDING",    (0,0),(0,0), 4 * spacer_mult),
        ("BOTTOMPADDING", (0,0),(0,0), 4 * spacer_mult),
        ("ALIGN",         (0,0),(0,0), "CENTER"),
    ]))
    elems.append(title_tbl)
    elems.append(Spacer(1, 4 * spacer_mult))

    # Student Info 
    info_rows = [
        ["Student Name:",   student_name or "—",       "Program:",      program],
        ["Student ID:",     student_id or "—",          "Campus:",       campus],
        ["Print Date:",     now.strftime("%B %d, %Y"),  "Status:",       "Enrolled"],
        ["Batch:",          batch or "—",               "Roll No:",      student_id or "—"],
    ]
    info_tbl = Table(info_rows, colWidths=[2.8*cm, 6.7*cm, 2.3*cm, content_w-11.8*cm])
    info_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0),(-1,-1), font_size),
        ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0),(2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0),(0,-1), NU_GREEN),
        ("TEXTCOLOR", (2,0),(2,-1), NU_GREEN),
        ("TOPPADDING",(0,0),(-1,-1), 2.5 * spacer_mult),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2.5 * spacer_mult),
        ("LINEBELOW", (0,-1),(-1,-1), 0.5, NU_GOLD),
        ("BACKGROUND",(0,0),(-1,-1), LIGHT_GRAY),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LIGHT_GRAY, colors.white]),
    ]))
    elems.append(info_tbl)
    elems.append(Spacer(1, 4 * spacer_mult))

    # Transcript Table 
    def section_header(text):
        d = [[text]]
        t = Table(d, colWidths=[content_w])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,0), TABLE_HDR),
            ("TEXTCOLOR",     (0,0),(0,0), colors.white),
            ("FONTNAME",      (0,0),(0,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(0,0), font_size + 0.5),
            ("TOPPADDING",    (0,0),(0,0), 3 * spacer_mult),
            ("BOTTOMPADDING", (0,0),(0,0), 3 * spacer_mult),
            ("LEFTPADDING",   (0,0),(0,0), 6),
        ]))
        return t

    elems.append(section_header("COURSE GRADES"))
    elems.append(Spacer(1, 2))

    col_ws = [2.0*cm, 9.0*cm, 1.6*cm, 1.6*cm, 1.6*cm, content_w-15.8*cm]
    hdr = [["Course Code","Course Title","Credit Hrs","Grade","Grade Pts","Remarks"]]
    hdr_tbl = Table(hdr, colWidths=col_ws)
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), NU_GREEN),
        ("TEXTCOLOR",     (0,0),(-1,0), colors.white),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0), font_size),
        ("ALIGN",         (2,0),(-1,0), "CENTER"),
        ("TOPPADDING",    (0,0),(-1,0), 3),
        ("BOTTOMPADDING", (0,0),(-1,0), 3),
    ]))
    elems.append(hdr_tbl)

    rows = []
    total_pts = total_ch_sum = 0.0
    for code, val in transcript.items():
        g  = val["grade"] if isinstance(val,dict) else val
        nm = val.get("name","") if isinstance(val,dict) else ""
        ch = val.get("credit_hours",3) if isinstance(val,dict) else 3
        is_nc = g in ("S","U","NC")
        gp = GRADE_POINTS.get(g, 0.0)
        if not is_nc:
            total_pts    += gp * ch
            total_ch_sum += ch
        remark = "Non-Credit" if is_nc else ("Pass" if gp >= 1.0 else "Fail")
        gp_str = "—" if is_nc else f"{gp:.2f}"
        rows.append([code, nm[:55] if nm else code, str(ch), g, gp_str, remark])

    data_tbl = Table(rows, colWidths=col_ws, repeatRows=0)
    row_styles = [
        ("FONTNAME",       (0,0),(-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0),(-1,-1), font_size),
        ("ALIGN",          (2,0),(-1,-1), "CENTER"),
        ("TOPPADDING",     (0,0),(-1,-1), row_padding),
        ("BOTTOMPADDING",  (0,0),(-1,-1), row_padding),
        ("LINEBELOW",      (0,-1),(-1,-1), 0.4, NU_GOLD),
        ("GRID",           (0,0),(-1,-1), 0.2, colors.HexColor("#dddddd")),
    ]
    
    for i in range(len(rows)):
        bg = ALT_ROW if i%2==0 else colors.white
        row_styles.append(("BACKGROUND",(0,i),(-1,i),bg))
        g = rows[i][3]
        gp_val = GRADE_POINTS.get(g,0)
        if g in ("S","U","NC"): gc=colors.HexColor("#555555")
        elif gp_val>=3.67:   gc=colors.HexColor("#006400")
        elif gp_val>=3.0:  gc=colors.HexColor("#1a5276")
        elif gp_val>=2.0:  gc=colors.HexColor("#784212")
        else:              gc=colors.HexColor("#7b241c")
        row_styles.append(("TEXTCOLOR",(3,i),(3,i),gc))
        row_styles.append(("FONTNAME", (3,i),(3,i),"Helvetica-Bold"))

    data_tbl.setStyle(TableStyle(row_styles))
    elems.append(data_tbl)
    elems.append(Spacer(1, 5 * spacer_mult))

    # Summary Box 
    cgpa_val = round(total_pts/total_ch_sum,3) if total_ch_sum>0 else 0

    summary_data = [
        ["ACADEMIC SUMMARY", "", "", ""],
        ["Total Courses:", str(len(transcript)), "Total Credit Hours:", f"{total_ch_sum:.0f}"],
        ["Total Quality Points:", f"{total_pts:.2f}", "CGPA:", f"{cgpa_val:.3f}"],
        ["Standing:", "Good Standing" if cgpa_val>=2.0 else "Academic Probation", "Scale:", "0.000 – 4.000"],
    ]
    sum_tbl = Table(summary_data, colWidths=[3.5*cm, 3.5*cm, 4.0*cm, content_w-11.0*cm])
    sum_tbl.setStyle(TableStyle([
        ("SPAN",         (0,0),(-1,0)),
        ("BACKGROUND",   (0,0),(-1,0), NU_DARK),
        ("TEXTCOLOR",    (0,0),(-1,0), colors.white),
        ("FONTNAME",     (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,0), font_size + 0.5),
        ("ALIGN",        (0,0),(-1,0), "CENTER"),
        ("TOPPADDING",   (0,0),(-1,-1), 3 * spacer_mult),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3 * spacer_mult),
        ("FONTNAME",     (0,1),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,1),(2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0,1),(0,-1), NU_GREEN),
        ("TEXTCOLOR",    (2,1),(2,-1), NU_GREEN),
        ("FONTSIZE",     (0,1),(-1,-1), font_size),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LIGHT_GRAY, colors.white]),
        ("BOX",          (0,0),(-1,-1), 1, NU_GREEN),
        ("FONTNAME",     (3,2),(3,2), "Helvetica-Bold"),
        ("FONTSIZE",     (3,2),(3,2), font_size + 3),
        ("TEXTCOLOR",    (3,2),(3,2), NU_GREEN),
    ]))
    elems.append(sum_tbl)
    elems.append(Spacer(1, 5 * spacer_mult))

    # Footer 
    elems.append(HRFlowable(width=content_w, thickness=0.7, color=NU_GOLD))
    elems.append(Spacer(1, 3 * spacer_mult))
    elems.append(Paragraph(
        "This is an unofficial transcript generated by Flex Watcher_J11. "
        "For official transcripts, contact the Registrar's Office, NUCES.",
        s_watermark))
    elems.append(Spacer(1, 1.5))
    elems.append(Paragraph(
        f"Generated: {now.strftime('%B %d, %Y at %I:%M %p')} | "
        "NUCES — National University of Computer and Emerging Sciences (FAST-NU)",
        s_footer))

    doc.build(elems)
    print(f"✅ Transcript PDF saved: {out_path}")

    import os
    if sys.platform == "win32":
        os.startfile(str(out_path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(out_path)])
    else:
        subprocess.run(["xdg-open", str(out_path)], stderr=subprocess.DEVNULL)

    return out_path

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate Transcript PDF")
    p.add_argument("--name",    default="", help="Student name")
    p.add_argument("--id",      default="", help="Student ID")
    p.add_argument("--program", default="BS Computer Science")
    p.add_argument("--campus",  default="Islamabad")
    args = p.parse_args()
    generate_pdf(args.name, args.id, args.program, args.campus)