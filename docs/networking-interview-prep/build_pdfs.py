#!/usr/bin/env python3
"""
Build professionally formatted PDFs for the Networking Interview Prep course.

- One PDF per module:  docs/networking-interview-prep/Module-NN-<name>.pdf
- Cumulative master:   docs/Networking_Interview_Master.pdf

Pipeline: Markdown -> HTML (python-markdown) -> PDF (WeasyPrint).

Usage:  python3 build_pdfs.py
Deps :  pip install weasyprint markdown pygments
"""

import datetime
import re
from pathlib import Path

import markdown
from weasyprint import HTML

BASE = Path(__file__).resolve().parent
SRC = BASE / "src"
DOCS = BASE.parent  # docs/

MODULES = [
    ("module-01-networking-basics.md", "Module 1", "Networking Basics"),
    ("module-02-tcp.md", "Module 2", "TCP"),
    ("module-03-udp.md", "Module 3", "UDP"),
    ("module-04-http.md", "Module 4", "HTTP (1.1 / 2 / 3, HTTPS, QUIC)"),
    ("module-05-dns.md", "Module 5", "DNS"),
    ("module-06-load-balancing.md", "Module 6", "Load Balancing"),
    ("module-07-cdn.md", "Module 7", "CDN"),
    ("module-08-websockets-grpc.md", "Module 8", "WebSockets, SSE, Polling & gRPC"),
    ("module-09-security.md", "Module 9", "Security (TLS, PKI, JWT, OAuth, CORS, CSRF, XSS)"),
    ("module-10-production-debugging.md", "Module 10", "Production Debugging"),
]

COURSE_TITLE = "Computer Networking for Senior Software Engineer Interviews"
SUBTITLE = ("Interview-focused networking, as asked at Google, Meta, Amazon, "
            "Microsoft, Uber, Netflix, Cloudflare, Stripe, LinkedIn & Cisco")

CSS = """
@page {
    size: A4;
    margin: 2.1cm 1.9cm 2.3cm 1.9cm;
    @bottom-center {
        content: "%(footer)s  \\2022  Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #8a8f98;
        font-family: Helvetica, Arial, sans-serif;
    }
    @top-right {
        content: "%(header)s";
        font-size: 8pt;
        color: #8a8f98;
        font-family: Helvetica, Arial, sans-serif;
    }
}
@page cover {
    margin: 0;
    @bottom-center { content: none; }
    @top-right { content: none; }
}
html { font-size: 10pt; }
body {
    font-family: Helvetica, Arial, sans-serif;
    color: #1c2733;
    line-height: 1.5;
}
.cover {
    page: cover;
    width: 100%%;
    height: 29.7cm;
    background: linear-gradient(150deg, #0b2545 0%%, #13315c 55%%, #1d4e89 100%%);
    color: #ffffff;
    display: block;
    padding: 4.2cm 2.6cm 0 2.6cm;
    box-sizing: border-box;
    page-break-after: always;
}
.cover .kicker {
    font-size: 11pt; letter-spacing: 3px; text-transform: uppercase;
    color: #9fc2e8; margin-bottom: 22px;
}
.cover h1.title {
    font-size: 30pt; line-height: 1.22; margin: 0 0 18px 0;
    color: #ffffff; border: none;
}
.cover .subtitle { font-size: 12.5pt; color: #cfe0f4; line-height: 1.55; margin-bottom: 34px; }
.cover .rule { width: 90px; height: 4px; background: #f4b942; margin-bottom: 34px; }
.cover .meta { font-size: 10pt; color: #9fb8d4; line-height: 1.8; }
.cover .modules-list {
    margin-top: 30px; font-size: 9.5pt; color: #d7e5f5; line-height: 1.85;
    column-count: 2; column-gap: 32px;
}
h1 {
    font-size: 17pt; color: #0b2545;
    border-bottom: 3px solid #f4b942;
    padding-bottom: 6px; margin: 26px 0 14px 0;
    page-break-after: avoid;
    string-set: chapter content();
}
h1.module-start { page-break-before: always; }
h2 {
    font-size: 13pt; color: #13315c;
    background: #eef3f9;
    border-left: 5px solid #1d4e89;
    padding: 6px 10px; margin: 22px 0 10px 0;
    page-break-after: avoid;
}
h3 {
    font-size: 10.5pt; color: #1d4e89;
    margin: 14px 0 6px 0;
    page-break-after: avoid;
}
p { margin: 6px 0; text-align: justify; }
li { margin: 3px 0; }
strong { color: #0b2545; }
blockquote {
    margin: 10px 0; padding: 8px 14px;
    background: #fdf6e3; border-left: 4px solid #f4b942;
    color: #4d4433; font-style: italic;
}
blockquote p { text-align: left; }
code {
    font-family: "DejaVu Sans Mono", Menlo, monospace;
    font-size: 8.4pt;
    background: #f1f4f8; color: #b13a3a;
    padding: 1px 4px; border-radius: 3px;
}
pre {
    background: #0f1b2d; color: #dbe7f5;
    padding: 10px 12px; border-radius: 6px;
    font-size: 7.9pt; line-height: 1.38;
    overflow: hidden; white-space: pre-wrap;
    page-break-inside: avoid;
    margin: 10px 0;
}
pre code {
    background: transparent; color: inherit; padding: 0;
    font-size: inherit;
}
table {
    border-collapse: collapse; width: 100%%;
    margin: 10px 0; font-size: 8.8pt;
    page-break-inside: avoid;
}
th {
    background: #13315c; color: #ffffff;
    padding: 5px 8px; text-align: left; font-size: 8.8pt;
}
td { border: 1px solid #ccd6e2; padding: 4px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #f4f7fb; }
hr { border: none; border-top: 1px solid #ccd6e2; margin: 18px 0; }
a { color: #1d4e89; text-decoration: none; }
.toc { page-break-after: always; }
.toc h1 { border-bottom: 3px solid #f4b942; }
.toc ol { list-style: none; padding-left: 0; font-size: 11pt; line-height: 2.0; }
.toc .mod-num {
    display: inline-block; width: 88px; color: #b13a3a; font-weight: bold;
}
"""


def md_to_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "smarty"],
        output_format="html5",
    )


def cover_html(title: str, subtitle: str, meta_lines, modules=None) -> str:
    mods = ""
    if modules:
        items = "".join(f"<div>{num} — {name}</div>" for _, num, name in modules)
        mods = f'<div class="modules-list">{items}</div>'
    meta = "<br/>".join(meta_lines)
    return f"""
    <div class="cover">
      <div class="kicker">Senior SWE Interview Series</div>
      <h1 class="title">{title}</h1>
      <div class="rule"></div>
      <div class="subtitle">{subtitle}</div>
      <div class="meta">{meta}</div>
      {mods}
    </div>
    """


def build_pdf(html_body: str, out_path: Path, header: str, footer: str):
    css = CSS % {"header": header, "footer": footer}
    doc = f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{html_body}</body></html>"
    HTML(string=doc).write_pdf(str(out_path))
    print(f"  wrote {out_path.relative_to(DOCS.parent)}  ({out_path.stat().st_size // 1024} KB)")


def main():
    today = datetime.date.today().strftime("%B %d, %Y")
    DOCS.mkdir(exist_ok=True)

    master_parts = [cover_html(
        COURSE_TITLE,
        SUBTITLE,
        [f"Master Edition — all 10 modules, cumulative", f"Built {today}",
         "Each topic: concept, internals, packet flow, diagrams, trade-offs, "
         "debugging, interview questions & mock interviews"],
        MODULES,
    )]

    toc_items = "".join(
        f'<li><span class="mod-num">{num}</span>{name}</li>'
        for _, num, name in MODULES
    )
    master_parts.append(
        f'<div class="toc"><h1>Table of Contents</h1><ol>{toc_items}</ol></div>'
    )

    print("Building per-module PDFs...")
    for fname, num, name in MODULES:
        md_text = (SRC / fname).read_text(encoding="utf-8")
        body_html = md_to_html(md_text)

        module_doc = cover_html(
            f"{num}: {name}",
            SUBTITLE,
            [f"Part of: {COURSE_TITLE}", f"Built {today}"],
        ) + body_html

        nn = num.split()[1].zfill(2)
        safe = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")
        out = DOCS / f"Networking-{nn}-{safe}.pdf"
        build_pdf(module_doc, out, header=f"{num} — {name}",
                  footer=COURSE_TITLE)

        # Master gets the body with a forced page break before each module.
        master_parts.append(
            body_html.replace("<h1>", '<h1 class="module-start">', 1)
        )

    print("Building cumulative Master PDF...")
    build_pdf("".join(master_parts),
              DOCS / "Networking_Interview_Master.pdf",
              header=COURSE_TITLE,
              footer="Networking Interview Master Notes")
    print("Done.")


if __name__ == "__main__":
    main()
