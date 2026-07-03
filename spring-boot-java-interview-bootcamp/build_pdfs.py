#!/usr/bin/env python3
"""Build per-module PDFs and a cumulative Master PDF for the
Spring Boot + Core Java + Collections Interview Bootcamp.

Usage:
    pip install weasyprint markdown
    python3 spring-boot-java-interview-bootcamp/build_pdfs.py

Reads:  spring-boot-java-interview-bootcamp/src/module-*.md
Writes: spring-boot-java-interview-bootcamp/pdf/SpringBoot_Java_Module_XX_<name>.pdf
        spring-boot-java-interview-bootcamp/pdf/SpringBoot_Java_Interview_Master.pdf
Also copies every generated PDF into the repository-root docs/ directory.
"""

import datetime
import re
import shutil
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "pdf"
DOCS = ROOT.parent / "docs"

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "smarty", "toc"]

CSS = """
@page {
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
    @top-center {
        content: string(doctitle);
        font-size: 8pt;
        color: #888;
        font-family: Helvetica, Arial, sans-serif;
    }
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #888;
        font-family: Helvetica, Arial, sans-serif;
    }
    @bottom-left {
        content: "Spring Boot + Core Java Interview Bootcamp";
        font-size: 8pt;
        color: #888;
        font-family: Helvetica, Arial, sans-serif;
    }
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.45;
    color: #1a1a2e;
}
h1 {
    string-set: doctitle content();
    font-size: 19pt;
    color: #1b5e20;
    border-bottom: 3px solid #f57c00;
    padding-bottom: 6px;
    margin-top: 0;
    page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
h2 {
    font-size: 13.5pt;
    color: #0d3b16;
    background: #eef6ef;
    padding: 5px 8px;
    border-left: 5px solid #1b5e20;
    margin-top: 18px;
    page-break-after: avoid;
}
h3 {
    font-size: 10.8pt;
    color: #e65100;
    margin-bottom: 3px;
    margin-top: 12px;
    page-break-after: avoid;
}
h4 {
    font-size: 9.8pt;
    color: #33691e;
    margin-bottom: 2px;
    margin-top: 8px;
    page-break-after: avoid;
}
p { margin: 4px 0; }
em { color: #444; }
strong { color: #1b5e20; }
ul, ol { margin: 4px 0 4px 0; padding-left: 20px; }
li { margin: 2px 0; }
pre {
    background: #1b2b1e;
    color: #e6e6e6;
    font-family: "DejaVu Sans Mono", "Courier New", monospace;
    font-size: 7.6pt;
    line-height: 1.3;
    padding: 8px 10px;
    border-radius: 4px;
    white-space: pre-wrap;
    word-wrap: break-word;
    page-break-inside: avoid;
}
code {
    font-family: "DejaVu Sans Mono", "Courier New", monospace;
    font-size: 8.4pt;
    background: #eef1f6;
    color: #b3123f;
    padding: 0 2px;
    border-radius: 2px;
}
pre code { background: none; color: inherit; padding: 0; font-size: inherit; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    font-size: 8.6pt;
    page-break-inside: avoid;
}
th {
    background: #1b5e20;
    color: #fff;
    padding: 4px 6px;
    text-align: left;
}
td {
    border: 1px solid #c5d6c7;
    padding: 3px 6px;
    vertical-align: top;
}
tr:nth-child(even) td { background: #f3f8f3; }
hr { border: none; border-top: 1px solid #cdd8ce; margin: 14px 0; }
blockquote {
    border-left: 4px solid #f57c00;
    margin: 6px 0;
    padding: 2px 10px;
    color: #444;
    background: #fff6ec;
}
.cover {
    page-break-after: always;
    text-align: center;
    padding-top: 140px;
}
.cover h1 {
    border: none;
    font-size: 30pt;
    page-break-before: avoid;
    string-set: doctitle "Spring Boot + Core Java Interview Bootcamp";
}
.cover .subtitle { font-size: 14pt; color: #0d3b16; margin-top: 10px; }
.cover .meta { font-size: 10pt; color: #888; margin-top: 60px; }
.cover .companies { font-size: 9pt; color: #666; margin-top: 20px; }
.toc { page-break-after: always; }
.toc h1 { page-break-before: avoid; }
.toc ul { list-style: none; padding-left: 0; font-size: 11pt; line-height: 2; }
"""


def module_files() -> list[Path]:
    return sorted(SRC.glob("module-*.md"))


def md_to_html_body(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=MD_EXTENSIONS)


def wrap_html(body: str) -> str:
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def module_title(md_text: str) -> str:
    m = re.search(r"^# (.+)$", md_text, re.MULTILINE)
    return m.group(1).strip() if m else "Untitled"


def build_module_pdfs() -> list[tuple[str, str]]:
    OUT.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    titles = []
    for path in module_files():
        md_text = path.read_text(encoding="utf-8")
        title = module_title(md_text)
        num = re.search(r"module-(\d+)", path.name).group(1)
        clean = re.sub(r"^Module\s*\d+\s*[—:-]\s*", "", title)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", clean).strip("_")
        out_name = f"SpringBoot_Java_Module_{num}_{slug}.pdf"
        html = wrap_html(md_to_html_body(md_text))
        HTML(string=html).write_pdf(OUT / out_name)
        shutil.copy(OUT / out_name, DOCS / out_name)
        titles.append((title, out_name))
        print(f"built {out_name}")
    return titles


def build_master_pdf(titles: list[tuple[str, str]]) -> None:
    today = datetime.date.today().strftime("%B %d, %Y")
    cover = f"""
    <div class="cover">
      <h1>Spring Boot + Core Java<br/>Interview Bootcamp</h1>
      <div class="subtitle">5-Day Crash Course for the Java Microservices Developer Interview<br/>
      Complete Master Edition &mdash; Modules 1&ndash;11</div>
      <div class="companies">Targeting interviews at Google &middot; Amazon &middot; Microsoft &middot;
      Uber &middot; Stripe &middot; Netflix &middot; Oracle &middot; VMware &middot; TCS &middot; Infosys &middot;
      Cognizant &middot; Accenture &middot; Capgemini &middot; IBM &middot; Deloitte &middot; EY &middot; Wipro &middot; LTIMindtree</div>
      <div class="meta">Every topic: why it's asked &middot; internals &middot; ASCII memory diagrams &middot;
      production examples &middot; traps &middot; best answers &middot; code &middot; follow-ups &middot; cheat sheets<br/><br/>Generated {today}</div>
    </div>
    <div class="toc">
      <h1>Contents</h1>
      <ul>{''.join(f'<li>{t}</li>' for t, _ in titles)}</ul>
    </div>
    """
    bodies = [md_to_html_body(p.read_text(encoding="utf-8")) for p in module_files()]
    html = wrap_html(cover + "".join(bodies))
    master = "SpringBoot_Java_Interview_Master.pdf"
    HTML(string=html).write_pdf(OUT / master)
    shutil.copy(OUT / master, DOCS / master)
    print(f"built {master}")


if __name__ == "__main__":
    build_master_pdf(build_module_pdfs())
