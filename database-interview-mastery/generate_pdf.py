#!/usr/bin/env python3
"""Build SQL_NoSQL_Interview_Mastery.pdf from the README + module markdown files."""

import glob
import os

import markdown
from weasyprint import HTML

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "SQL_NoSQL_Interview_Mastery.pdf")

FILES = [os.path.join(BASE, "README.md")] + sorted(
    glob.glob(os.path.join(BASE, "modules", "module-*.md"))
)

CSS = """
@page {
  size: A4;
  margin: 1.6cm 1.5cm 1.8cm 1.5cm;
  @bottom-center {
    content: "SQL & NoSQL Interview Mastery  —  page " counter(page);
    font-size: 8pt; color: #888;
    font-family: Helvetica, Arial, sans-serif;
  }
}
body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9.5pt; line-height: 1.45; color: #1c2733;
}
h1 {
  color: #0f3d5c; font-size: 19pt; border-bottom: 3px solid #0f3d5c;
  padding-bottom: 4px; margin: 0 0 12px 0;
  page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
h2 {
  color: #14608f; font-size: 14pt; margin: 20px 0 6px 0;
  border-bottom: 1px solid #b9d4e6; padding-bottom: 2px;
  page-break-after: avoid;
}
h3 { color: #1d7ab5; font-size: 11pt; margin: 14px 0 4px 0; page-break-after: avoid; }
h4 { color: #333; font-size: 10pt; margin: 10px 0 3px 0; }
p { margin: 4px 0; }
ul, ol { margin: 4px 0 4px 18px; padding: 0; }
li { margin: 2px 0; }
blockquote {
  border-left: 4px solid #c8960c; background: #fef9e7;
  margin: 8px 0; padding: 6px 10px; color: #5a4a12;
}
code {
  font-family: "DejaVu Sans Mono", monospace; font-size: 8pt;
  background: #eef2f5; padding: 0 2px; border-radius: 2px;
}
pre {
  background: #f4f7f9; border: 1px solid #d6dee5; border-radius: 4px;
  padding: 7px 9px; margin: 6px 0;
  font-size: 7.6pt; line-height: 1.32;
  white-space: pre-wrap; word-wrap: break-word;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: 7.6pt; }
table {
  border-collapse: collapse; margin: 8px 0; width: 100%;
  font-size: 8.4pt; page-break-inside: avoid;
}
th {
  background: #0f3d5c; color: #fff; padding: 4px 6px;
  text-align: left; font-size: 8.4pt;
}
td { border: 1px solid #c9d4dc; padding: 3px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f2f6f9; }
hr { border: none; border-top: 1px solid #ccd6de; margin: 14px 0; }
a { color: #14608f; text-decoration: none; }
strong { color: #0f3d5c; }
"""

COVER = """
<div style="text-align:center; margin-top:180px;">
  <div style="font-size:30pt; color:#0f3d5c; font-weight:bold;">
    SQL &amp; NoSQL Interview Mastery
  </div>
  <div style="font-size:14pt; color:#14608f; margin-top:14px;">
    Senior Software Engineer Edition
  </div>
  <div style="font-size:10pt; color:#555; margin-top:40px; line-height:1.9;">
    11 modules &middot; PostgreSQL-first &middot; MySQL / MongoDB / Redis / Cassandra / DynamoDB comparisons<br/>
    Core concepts &middot; Internals &middot; Production scenarios &middot; FAANG-style questions<br/>
    165 practice problems (5 easy / 5 medium / 5 hard per module)
  </div>
  <div style="font-size:9pt; color:#999; margin-top:60px;">
    Interview patterns: Google &middot; Meta &middot; Amazon &middot; Microsoft &middot; Uber &middot; Netflix &middot; Stripe &middot; LinkedIn
  </div>
</div>
"""


def build() -> None:
    md = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists"])
    sections = []
    for path in FILES:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        sections.append(md.convert(text))
        md.reset()

    html = (
        "<html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>"
        + COVER
        + "".join(sections)
        + "</body></html>"
    )
    HTML(string=html).write_pdf(OUT)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")


if __name__ == "__main__":
    build()
