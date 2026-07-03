#!/usr/bin/env python3
"""Build per-module PDFs and a cumulative Master PDF for the Spring Boot &
Microservices interview notes.

Usage:
    pip install weasyprint markdown
    python3 docs/springboot-interview-prep/build_pdfs.py

Reads:  docs/springboot-interview-prep/src/module-*.md
Writes: docs/SpringBoot_Interview_Module_XX_<name>.pdf   (one per module)
        docs/SpringBoot_Interview_Master.pdf             (cover + TOC + all modules)
"""

import datetime
import re
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent          # docs/springboot-interview-prep
SRC = ROOT / "src"
OUT = ROOT.parent                                # docs/  (all PDFs live here)

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
        content: "Spring Boot & Microservices Interview Mastery — Senior SWE Track";
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
    color: #14532d;
    border-bottom: 3px solid #6db33f;
    padding-bottom: 6px;
    margin-top: 0;
    page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
h2 {
    font-size: 13.5pt;
    color: #0f3d24;
    background: #eef6ea;
    padding: 5px 8px;
    border-left: 5px solid #6db33f;
    margin-top: 18px;
    page-break-after: avoid;
}
h3 {
    font-size: 10.5pt;
    color: #b5551d;
    margin-bottom: 3px;
    margin-top: 12px;
    page-break-after: avoid;
}
h4 { font-size: 9.8pt; color: #14532d; margin: 8px 0 2px; page-break-after: avoid; }
p { margin: 4px 0; }
em { color: #444; }
strong { color: #14532d; }
ul, ol { margin: 4px 0 4px 0; padding-left: 20px; }
li { margin: 2px 0; }
pre {
    background: #12261b;
    color: #e6e6e6;
    font-family: "DejaVu Sans Mono", "Courier New", monospace;
    font-size: 7.6pt;
    line-height: 1.3;
    padding: 8px 10px;
    border-radius: 4px;
    white-space: pre;
    overflow: hidden;
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
    background: #14532d;
    color: #fff;
    padding: 4px 6px;
    text-align: left;
}
td {
    border: 1px solid #c5d6c0;
    padding: 3px 6px;
    vertical-align: top;
}
tr:nth-child(even) td { background: #f3f8f1; }
hr { border: none; border-top: 1px solid #cdd9c8; margin: 14px 0; }
blockquote {
    border-left: 4px solid #6db33f;
    margin: 6px 0;
    padding: 2px 10px;
    color: #444;
    background: #f4faf0;
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
    string-set: doctitle "Spring Boot & Microservices Interview Mastery";
}
.cover .subtitle { font-size: 14pt; color: #0f3d24; margin-top: 10px; }
.cover .meta { font-size: 10pt; color: #888; margin-top: 55px; }
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
    titles = []
    for path in module_files():
        md_text = path.read_text(encoding="utf-8")
        title = module_title(md_text)
        num = re.search(r"module-(\d+)", path.name).group(1)
        tail = title.split("—")[-1]
        slug = re.sub(r"[^A-Za-z0-9]+", "_", tail).strip("_")
        out_name = f"SpringBoot_Interview_Module_{num}_{slug}.pdf"
        html = wrap_html(md_to_html_body(md_text))
        HTML(string=html).write_pdf(OUT / out_name)
        titles.append((title, out_name))
        print(f"built {out_name}")
    return titles


def build_master_pdf(titles: list[tuple[str, str]]) -> None:
    today = datetime.date.today().strftime("%B %d, %Y")
    cover = f"""
    <div class="cover">
      <h1>Spring Boot &amp;<br/>Microservices<br/>Interview Mastery</h1>
      <div class="subtitle">The Senior Software Engineer Track<br/>
      Complete Master Edition — Modules 1&ndash;15</div>
      <div class="companies">Targeting interviews at Google &middot; Amazon &middot; Microsoft &middot;
      Uber &middot; Netflix &middot; LinkedIn &middot; VMware &middot; Broadcom &middot; Oracle &middot;
      JPMorgan &middot; Goldman Sachs &middot; Walmart Global Tech &middot; Adobe &middot; Atlassian</div>
      <div class="meta">For engineers moving from Node.js / MERN to Java &amp; Spring Boot.<br/>
      Each topic: why it's asked &middot; internals &middot; lifecycle &middot; ASCII diagrams &middot;
      production examples &middot; trade-offs &middot; traps &middot; debugging &middot; follow-ups &middot; exercises<br/><br/>
      Generated {today}</div>
    </div>
    <div class="toc">
      <h1>Contents</h1>
      <ul>{''.join(f'<li>{t}</li>' for t, _ in titles)}</ul>
    </div>
    """
    bodies = [md_to_html_body(p.read_text(encoding="utf-8")) for p in module_files()]
    html = wrap_html(cover + "".join(bodies))
    HTML(string=html).write_pdf(OUT / "SpringBoot_Interview_Master.pdf")
    print("built SpringBoot_Interview_Master.pdf")


if __name__ == "__main__":
    build_master_pdf(build_module_pdfs())
