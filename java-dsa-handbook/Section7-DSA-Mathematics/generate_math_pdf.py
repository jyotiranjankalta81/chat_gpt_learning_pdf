#!/usr/bin/env python3
"""Generate a simple PDF version of the DSA mathematics handbook.

This script intentionally uses only the Python standard library so it works in
minimal interview-prep environments without pandoc, wkhtmltopdf, or ReportLab.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_MD = BASE_DIR / "complete-dsa-mathematics-handbook.md"
PDF_DIR = BASE_DIR / "PDFs"
OUTPUT_PDF = PDF_DIR / "Complete_DSA_Mathematics_Handbook.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_X = 36
MARGIN_Y = 36
FONT_SIZE = 8.3
LEADING = 10.5
CHARS_PER_LINE = 104
LINES_PER_PAGE = int((PAGE_HEIGHT - 2 * MARGIN_Y) / LEADING)


def strip_markdown(line: str) -> str:
    """Convert a markdown line to readable plain text for the PDF."""
    line = line.rstrip()
    if not line:
        return ""

    if line.startswith("#"):
        level = len(line) - len(line.lstrip("#"))
        text = line[level:].strip()
        return text.upper() if level <= 2 else text

    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    line = line.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return line


def markdown_to_pdf_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    for raw in markdown.splitlines():
        plain = strip_markdown(raw)
        if not plain:
            lines.append("")
            continue

        indent = ""
        content = plain
        if plain.startswith("- "):
            indent = "  "
            content = "* " + plain[2:]
        elif re.match(r"^\d+\. ", plain):
            indent = "  "

        wrapped = textwrap.wrap(
            content,
            width=CHARS_PER_LINE - len(indent),
            break_long_words=False,
            break_on_hyphens=False,
        )
        if not wrapped:
            lines.append("")
        else:
            lines.append(indent + wrapped[0])
            for extra in wrapped[1:]:
                lines.append(indent + "  " + extra)
    return lines


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_page_stream(lines: list[str]) -> bytes:
    commands = [
        "BT",
        f"/F1 {FONT_SIZE} Tf",
        f"{MARGIN_X} {PAGE_HEIGHT - MARGIN_Y} Td",
        f"{LEADING} TL",
    ]
    for line in lines:
        commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return ("\n".join(commands) + "\n").encode("latin-1", errors="replace")


def write_pdf(pages: list[list[str]], out_path: Path) -> None:
    objects: list[bytes] = []

    def add_object(data: bytes | str) -> int:
        if isinstance(data, str):
            data = data.encode("latin-1", errors="replace")
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"")
    pages_id = add_object(b"")
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for page_lines in pages:
        stream = build_page_stream(page_lines)
        content_id = add_object(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, obj in enumerate(objects, start=1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n".encode("ascii"))
            f.write(obj)
            f.write(b"\nendobj\n")

        xref_offset = f.tell()
        f.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        f.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            f.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        f.write(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )


def main() -> None:
    markdown = SOURCE_MD.read_text(encoding="utf-8")
    pdf_lines = markdown_to_pdf_lines(markdown)
    pages = [
        pdf_lines[i : i + LINES_PER_PAGE]
        for i in range(0, len(pdf_lines), LINES_PER_PAGE)
    ]
    write_pdf(pages, OUTPUT_PDF)
    print(f"Created {OUTPUT_PDF.relative_to(BASE_DIR)} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
