#!/usr/bin/env python3
"""Build the System Design Interview Mastery PDF from the module markdown files."""

import re
from pathlib import Path

import markdown
from weasyprint import HTML

HERE = Path(__file__).parent
OUTPUT = HERE / "System_Design_Interview_Mastery.pdf"

MODULES = [
    "00-introduction.md",
    "01-foundations.md",
    "02-networking.md",
    "03-caching.md",
    "04-database-design.md",
    "05-messaging.md",
    "06-storage.md",
    "07-microservices.md",
    "08-reliability.md",
    "09-security.md",
    "10-performance.md",
    "11-distributed-systems.md",
    "12-observability.md",
    "13a-design-problems-1.md",
    "13b-design-problems-2.md",
    "14-interview-strategy.md",
]

CSS = """
@page {
    size: A4;
    margin: 2.0cm 1.8cm 2.2cm 1.8cm;
    @bottom-center {
        content: "System Design Interview Mastery  \\2022  Page " counter(page);
        font-family: Helvetica, Arial, sans-serif;
        font-size: 8pt;
        color: #8a8a8a;
    }
}
@page cover { @bottom-center { content: none; } }

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.45;
    color: #1c2733;
}

.cover {
    page: cover;
    page-break-after: always;
    background: #12283f;
    color: #ffffff;
    text-align: center;
    padding: 7cm 1.5cm 1cm 1.5cm;
    height: 24.5cm;
}
.cover h1 { font-size: 30pt; margin: 0 0 0.4cm 0; border: none; color: #ffffff; }
.cover .subtitle { font-size: 13pt; color: #a9c6e4; margin-bottom: 1.2cm; }
.cover .meta { font-size: 10pt; color: #7d9cbd; line-height: 1.9; }
.cover .rule { width: 5cm; border-top: 2px solid #d4a017; margin: 0.9cm auto; }

.toc { page-break-after: always; }
.toc h1 { font-size: 18pt; }
.toc ul { list-style: none; padding-left: 0; column-count: 2; column-gap: 1cm; }
.toc li { font-size: 9.5pt; margin-bottom: 0.14cm; }
.toc a { color: #1c2733; text-decoration: none; }
.toc .lvl2 { padding-left: 0.5cm; color: #4a5a6a; font-size: 8.5pt; }

h1 {
    font-size: 17pt; color: #12283f;
    border-bottom: 2.5px solid #d4a017;
    padding-bottom: 0.15cm; margin: 0.2cm 0 0.5cm 0;
    page-break-before: always; page-break-after: avoid;
}
h1.first { page-break-before: avoid; }
h2 {
    font-size: 12.5pt; color: #1d4068;
    margin: 0.55cm 0 0.25cm 0;
    border-bottom: 1px solid #c9d6e2; padding-bottom: 0.08cm;
    page-break-after: avoid;
}
h3 { font-size: 10.5pt; color: #2e5a86; margin: 0.4cm 0 0.15cm 0; page-break-after: avoid; }

p { margin: 0.14cm 0 0.24cm 0; text-align: justify; }
ul, ol { margin: 0.1cm 0 0.3cm 0; padding-left: 0.55cm; }
li { margin-bottom: 0.1cm; text-align: justify; }
strong { color: #12283f; }
hr { border: none; border-top: 1px solid #d7dee5; margin: 0.45cm 0; }

code {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 8.3pt;
    background: #eef2f6;
    padding: 0.4px 3px;
    border-radius: 2px;
    color: #17324d;
}
pre {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 7.6pt;
    line-height: 1.32;
    background: #f4f7fa;
    border: 1px solid #d7dee5;
    border-left: 3px solid #d4a017;
    border-radius: 3px;
    padding: 0.28cm 0.32cm;
    margin: 0.22cm 0 0.34cm 0;
    white-space: pre-wrap;
    overflow-wrap: normal;
}
pre code { background: none; padding: 0; font-size: 7.6pt; }

table {
    border-collapse: collapse;
    margin: 0.25cm 0 0.35cm 0;
    font-size: 8.6pt;
    width: 100%;
}
th {
    background: #12283f; color: #ffffff;
    padding: 3.5px 6px; text-align: left; font-size: 8.6pt;
}
td { border: 0.5px solid #c3cdd7; padding: 3px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f3f6f9; }

blockquote {
    border-left: 3px solid #2e6da4;
    margin: 0.25cm 0; padding: 0.05cm 0.35cm;
    color: #3d4f61; background: #f2f7fc;
}
"""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build() -> None:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )

    body_parts = []
    toc_entries = []  # (level, title, anchor)
    used = set()

    for fname in MODULES:
        text = (HERE / fname).read_text(encoding="utf-8")
        md.reset()
        html = md.convert(text)

        # Anchor h1/h2 headings and collect TOC entries.
        def add_anchor(match):
            level, inner = match.group(1), match.group(2)
            title = re.sub(r"<[^>]+>", "", inner)
            anchor = slugify(title)
            while anchor in used:
                anchor += "-x"
            used.add(anchor)
            if level == "1" or (level == "2" and re.match(r"^\d+\.\d+", title)):
                toc_entries.append((int(level), title, anchor))
            return f'<h{level} id="{anchor}">{inner}</h{level}>'

        html = re.sub(r"<h([12])>(.*?)</h\1>", add_anchor, html, flags=re.S)
        body_parts.append(html)

    toc_items = "\n".join(
        f'<li class="lvl{lvl}"><a href="#{anchor}">{title}</a></li>'
        for lvl, title, anchor in toc_entries
    )

    document = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
<div class="cover">
  <h1>System Design<br/>Interview Mastery</h1>
  <div class="rule"></div>
  <div class="subtitle">A Production-Grade Guide for Senior, Staff &amp; Backend Engineers</div>
  <div class="meta">
    14 Modules &nbsp;\u2022&nbsp; 27 Classic Design Problems &nbsp;\u2022&nbsp; Cheat Sheets &amp; Mock Interviews<br/>
    Foundations \u2022 Networking \u2022 Caching \u2022 Databases \u2022 Messaging \u2022 Storage<br/>
    Microservices \u2022 Reliability \u2022 Security \u2022 Performance \u2022 Distributed Systems<br/>
    Observability \u2022 System Design Problems \u2022 Interview Strategy
  </div>
</div>
<div class="toc"><h1 class="first">Table of Contents</h1><ul>{toc_items}</ul></div>
{"".join(body_parts)}
</body></html>"""

    HTML(string=document).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
