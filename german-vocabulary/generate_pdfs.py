#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
German Vocabulary PDF Generator
Generates one PDF per CEFR level + one combined master PDF.
"""

import os
import subprocess
import sys
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "PDFs")
os.makedirs(PDF_DIR, exist_ok=True)

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
LEVEL_TITLES = {
    "A1": "Beginner — Survival German",
    "A2": "Elementary — Everyday German",
    "B1": "Intermediate — Independent German",
    "B2": "Upper-Intermediate — Advanced German",
    "C1": "Advanced — Near-Native German",
}
LEVEL_COLORS = {
    "A1": ("#2e7d32", "#e8f5e9"),
    "A2": ("#1565c0", "#e3f2fd"),
    "B1": ("#e65100", "#fff3e0"),
    "B2": ("#880e4f", "#fce4ec"),
    "C1": ("#4a148c", "#f3e5f5"),
}

CSS = """<style>
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 9pt; color: #222; margin: 0; padding: 0; }
h1 { font-size: 17pt; color: #1a3a5c; border-bottom: 3px solid #2980b9; padding-bottom: 5px; margin: 18px 0 8px; }
h2 { font-size: 12pt; color: #2980b9; border-bottom: 1px solid #aed6f1; padding-bottom: 3px; margin: 14px 0 6px; }
h3 { font-size: 10.5pt; color: #148; margin: 10px 0 4px; }
p { margin: 3px 0; }
blockquote { background: #f0f7ff; border-left: 4px solid #2980b9; margin: 5px 0 8px; padding: 4px 10px; font-style: italic; color: #444; font-size: 8.5pt; }
hr { border: none; border-top: 1px solid #ccc; margin: 8px 0; }
table { border-collapse: collapse; width: 100%; margin: 5px 0 12px; font-size: 7.5pt; }
th { background: #2471a3; color: #fff; padding: 4px 5px; text-align: left; font-weight: bold; white-space: nowrap; }
td { border: 1px solid #d0d7de; padding: 3px 5px; vertical-align: top; word-break: break-word; }
tr:nth-child(even) td { background: #f0f6fb; }
tr:nth-child(odd) td { background: #fff; }
.cover { text-align: center; padding: 50px 30px; }
.cover h1 { font-size: 22pt; border: none; color: #1a3a5c; }
.cover .sub { font-size: 14pt; color: #2980b9; margin: 5px 0 20px; }
.cover .desc { font-size: 9.5pt; color: #555; line-height: 1.7; max-width: 500px; margin: 0 auto; }
.cover .footer { margin-top: 30px; font-size: 8pt; color: #aaa; }
.level-sep { text-align: center; padding: 50px 30px; page-break-before: always; }
</style>"""

def get_files(level):
    d = os.path.join(BASE_DIR, level)
    return sorted(glob.glob(os.path.join(d, "*.md")))

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def md_to_html(md_text):
    """Convert markdown to HTML using pandoc with GFM tables."""
    r = subprocess.run(
        ["pandoc", "--from=gfm", "--to=html5"],
        input=md_text.encode("utf-8"),
        capture_output=True, timeout=180
    )
    return r.stdout.decode("utf-8")

def make_html_doc(body_html, title="German Vocabulary"):
    return f"""<!DOCTYPE html>
<html lang="de"><head>
<meta charset="UTF-8">
<title>{title}</title>
{CSS}
</head><body>
{body_html}
</body></html>"""

def pdf_from_html(html_str, out_path, title="German Vocabulary"):
    tmp = out_path + ".tmp.html"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_str)

    cmd = [
        "wkhtmltopdf",
        "--page-size", "A4",
        "--margin-top", "13mm", "--margin-bottom", "13mm",
        "--margin-left", "12mm", "--margin-right", "12mm",
        "--encoding", "UTF-8",
        "--title", title,
        "--header-line",
        "--header-center", "German Vocabulary System — CEFR A1 to C1",
        "--header-font-size", "7",
        "--footer-line",
        "--footer-left", title,
        "--footer-center", "Page [page] of [topage]",
        "--footer-right", "german-vocabulary",
        "--footer-font-size", "7",
        "--outline", "--outline-depth", "3",
        "--quiet",
        tmp, out_path
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    if os.path.exists(tmp):
        os.remove(tmp)

    if r.returncode != 0 or not os.path.exists(out_path):
        print(f"  [ERROR] wkhtmltopdf: {r.stderr.decode()[:200]}")
        return False

    kb = os.path.getsize(out_path) / 1024
    pages_hint = "" 
    print(f"  Created: {os.path.basename(out_path)} ({kb:.0f} KB)")
    return True

def cover_html(title, subtitle, description):
    return f"""
<div class="cover">
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>
  <hr style="width:50%; margin:15px auto; border-top:2px solid #2980b9;">
  <div class="desc">{description}</div>
  <div class="footer">Complete German Vocabulary Learning System &bull; CEFR Aligned</div>
</div>
<div style="page-break-after:always;"></div>
"""

def level_sep_html(level, title, color, entries_count, file_count):
    hc, bc = color
    return f"""
<div class="level-sep" style="background:{bc}; border: 3px solid {hc};">
  <div style="font-size:38pt; font-weight:bold; color:{hc};">{level}</div>
  <div style="font-size:16pt; color:#333; margin-top:6px;">{title}</div>
  <hr style="width:35%; margin:10px auto; border-top:2px solid {hc};">
  <div style="font-size:9.5pt; color:#555;">{file_count} categories &bull; ~{entries_count} vocabulary entries</div>
</div>
<div style="page-break-after:always;"></div>
"""

def count_entries(text):
    return sum(1 for l in text.split("\n") if l.startswith("| ") and len(l)>4 and l[2].isdigit())

# ----- Generate per-level PDFs -----
def gen_level_pdf(level):
    print(f"\n[{level}] Generating...")
    files = get_files(level)
    title = LEVEL_TITLES[level]
    color = LEVEL_COLORS[level]

    all_md = ""
    total = 0
    for fp in files:
        content = read(fp)
        all_md += content + "\n\n---\n\n"
        total += count_entries(content)

    print(f"  {len(files)} files, ~{total} entries — converting to HTML...")
    body = md_to_html(all_md)

    cover = cover_html(
        f"German Vocabulary: {level}",
        title,
        f"<strong>{len(files)} topic categories &bull; ~{total} vocabulary entries</strong><br><br>"
        "Every entry: German word &bull; English meaning &bull; Pronunciation guide &bull; "
        "Article &bull; Part of speech &bull; Example sentences &bull; "
        "Collocations &bull; Synonyms &bull; Opposites"
    )

    sep = level_sep_html(level, title, color, total, len(files))
    full_html = make_html_doc(cover + sep + body, f"German Vocabulary {level}")

    safe = title.split("—")[0].strip().replace(" ", "_")
    out = os.path.join(PDF_DIR, f"German_Vocabulary_{level}_{safe}.pdf")
    return pdf_from_html(full_html, out, f"German Vocabulary {level} — {title}")

# ----- Generate combined PDF -----
def gen_combined_pdf():
    print("\n[COMBINED] Generating master PDF...")

    parts = []

    # Master cover
    total_files = sum(len(get_files(lv)) for lv in LEVELS)
    parts.append(cover_html(
        "Complete German Vocabulary System",
        "CEFR A1 to C1",
        f"<strong>5 CEFR Levels &bull; {total_files} Topic Categories &bull; ~5,300 Entries</strong><br><br>"
        "Daily Life &bull; Greetings &bull; Numbers &bull; Family &bull; Food &bull; Travel &bull; "
        "Shopping &bull; Banking &bull; Renting &bull; Transport &bull; Weather &bull; Health &bull; "
        "Work &amp; Office &bull; Technology &bull; Cloud &amp; DevOps &bull; AI &amp; Software Engineering &bull; "
        "Business &bull; Economics &bull; Law &bull; Politics &bull; Society &bull; Environment &bull; "
        "Education &bull; Fitness &bull; Swimming &bull; Hiking &bull; Media &bull; Idioms &amp; more"
    ))

    # Table of contents
    toc = '<h1>Table of Contents</h1>\n<table>\n'
    toc += '<tr><th>Level</th><th>Category</th><th style="text-align:right;">Entries</th></tr>\n'
    for level in LEVELS:
        hc, bc = LEVEL_COLORS[level]
        toc += f'<tr><td colspan="3" style="background:{hc};color:white;padding:5px 8px;font-weight:bold;">{level} — {LEVEL_TITLES[level]}</td></tr>\n'
        for fp in get_files(level):
            fname = os.path.basename(fp)[3:].replace(".md","").replace("_"," ").title()
            ec = count_entries(read(fp))
            toc += f'<tr style="background:{bc};"><td></td><td style="padding:2px 8px;">{fname}</td><td style="text-align:right;padding:2px 8px;">{ec}</td></tr>\n'
    toc += "</table>\n<div style='page-break-after:always;'></div>\n"
    parts.append(toc)

    # Level content
    for level in LEVELS:
        print(f"  Converting {level}...")
        files = get_files(level)
        color = LEVEL_COLORS[level]

        total = sum(count_entries(read(fp)) for fp in files)
        parts.append(level_sep_html(level, LEVEL_TITLES[level], color, total, len(files)))

        for fp in files:
            md = read(fp)
            parts.append(md_to_html(md))
            parts.append('<div style="page-break-after:always;"></div>\n')

    full_html = make_html_doc("\n".join(parts), "German Vocabulary — Complete A1 to C1")
    out = os.path.join(PDF_DIR, "German_Vocabulary_COMPLETE_A1_to_C1.pdf")
    return pdf_from_html(full_html, out, "German Vocabulary — Complete A1 to C1")

def main():
    print("=" * 58)
    print("German Vocabulary PDF Generator")
    print("=" * 58)

    ok = 0
    for level in LEVELS:
        if gen_level_pdf(level):
            ok += 1

    if gen_combined_pdf():
        ok += 1

    print(f"\n{'='*58}")
    print(f"Done: {ok}/6 PDFs generated in {PDF_DIR}")
    for f in sorted(os.listdir(PDF_DIR)):
        if f.endswith(".pdf"):
            kb = os.path.getsize(os.path.join(PDF_DIR, f)) / 1024
            print(f"  {f}  ({kb:.0f} KB)")

    return 0 if ok == 6 else 1

if __name__ == "__main__":
    sys.exit(main())
