"""Render projektskizze.md to a .docx the user can edit in Word.

Embeds the class- and sequence-diagram PNGs at the start of sections 4
and 5, mirroring build_pdf.py. The conversion is intentionally light:
headings, paragraphs, lists, tables, fenced code blocks, blockquotes,
inline code/bold/italic, and the diagram images. That is enough for
this Projektskizze; complex Markdown features are not used.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).parent
MD_FILE = ROOT / "projektskizze.md"
DIAGRAMS = ROOT / "diagrams"
OUT_DOCX = ROOT / "projektskizze.docx"

CLASS_PNG = DIAGRAMS / "class-diagram.png"
CLASS_TYPES_PNG = DIAGRAMS / "class-diagram-types.png"
SEQ_PNG = DIAGRAMS / "sequence-diagram.png"


# ---------- inline parsing (bold, italic, code, links) -------------------

INLINE_RE = re.compile(
    r"(\*\*[^*\n]+\*\*|__[^_\n]+__|"  # bold
    r"\*[^*\n]+\*|_[^_\n]+_|"          # italic
    r"`[^`\n]+`|"                      # code
    r"\[[^\]]+\]\([^)]+\))"            # link
)


def add_runs(paragraph, text: str) -> None:
    parts = INLINE_RE.split(text)
    for part in parts:
        if not part:
            continue
        if (part.startswith("**") and part.endswith("**")) or (
            part.startswith("__") and part.endswith("__")
        ):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif (part.startswith("*") and part.endswith("*")) or (
            part.startswith("_") and part.endswith("_")
        ):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        elif part.startswith("[") and "](" in part:
            label = part[1 : part.index("]")]
            run = paragraph.add_run(label)
            run.font.color.rgb = RGBColor(0x1A, 0x4F, 0x8A)
            run.underline = True
        else:
            paragraph.add_run(part)


# ---------- table parsing ------------------------------------------------


def is_table_sep(line: str) -> bool:
    s = line.strip().strip("|").strip()
    return bool(s) and all(c in "-:| " for c in s) and "-" in s


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def add_table(doc, header_row: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(header_row))
    table.style = "Light Grid Accent 1"
    for i, cell_text in enumerate(header_row):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(cell_text)
        run.bold = True
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    for r, row in enumerate(rows, start=1):
        for c, cell_text in enumerate(row):
            if c >= len(header_row):
                continue
            cell = table.rows[r].cells[c]
            cell.text = ""
            add_runs(cell.paragraphs[0], cell_text)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP


# ---------- main render --------------------------------------------------


def add_image(doc, png_path: Path, caption: str, *, width_cm: float = 16.0) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(png_path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run(caption)
    cap_run.italic = True
    cap_run.font.size = Pt(9)
    cap_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def add_code_block(doc, code: str) -> None:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.4)
    pf.space_before = Pt(4)
    pf.space_after = Pt(4)
    # Light grey shading on the paragraph
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F2F2F2")
    pPr.append(shd)
    run = p.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(9)


def render_title_page(doc) -> None:
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = title.paragraph_format
    pf.space_before = Pt(150)
    pf.space_after = Pt(8)
    r = title.add_run("Aufgabenblatt 1\nProjektskizze: Schwarmintelligenz")
    r.bold = True
    r.font.size = Pt(22)

    meta_lines = [
        "Agententechnologien — Grundlagen und Anwendungen",
        "TU Berlin, Sommersemester 2026",
        "",
        "Gruppe 11",
        "Ivan Wanylyn",
        "",
        "Abgabe: 04.05.2026",
    ]
    for line in meta_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.font.size = Pt(11)
        if line == "Gruppe 11":
            run.bold = True

    # Page break
    doc.add_paragraph().add_run().add_break()


def render(md_text: str, doc) -> None:
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Skip top-level title (we have our own title page)
        if stripped.startswith("# ") and i < 3:
            i += 1
            continue

        if stripped.startswith("---") and not stripped.startswith("----"):
            # horizontal rule -> small space
            doc.add_paragraph()
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            heading = doc.add_heading(level=min(level, 4))
            add_runs(heading, text)

            # Insert diagrams at the start of section 4 and 5
            if level == 2 and text.lstrip().startswith("4."):
                add_image(
                    doc,
                    CLASS_PNG,
                    "Abbildung 1a: Klassendiagramm – Struktur und Komposition.",
                )
                add_image(
                    doc,
                    CLASS_TYPES_PNG,
                    "Abbildung 1b: Klassendiagramm – Wertobjekte (Item-/Action-"
                    "Hierarchie) und Botschaftsobjekte zwischen Manager und Agent.",
                )
            elif level == 2 and text.lstrip().startswith("5."):
                add_image(
                    doc,
                    SEQ_PNG,
                    "Abbildung 2: Sequenzdiagramm eines Ticks.",
                )
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # consume closing ```
            add_code_block(doc, "\n".join(buf))
            continue

        # Tables: header line followed by separator line of dashes
        if "|" in stripped and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            header = split_row(stripped)
            i += 2  # skip separator
            rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, header, rows)
            continue

        # Blockquote
        if stripped.startswith(">"):
            buf_q: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf_q.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            run = p.add_run(" ".join(buf_q))
            run.italic = True
            continue

        # Bullet list
        if stripped.lstrip().startswith("* ") or stripped.lstrip().startswith("- "):
            text = stripped.lstrip()[2:]
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, text)
            i += 1
            continue

        # Ordered list
        if re.match(r"^\d+\.\s+", stripped.lstrip()):
            text = re.sub(r"^\d+\.\s+", "", stripped.lstrip())
            p = doc.add_paragraph(style="List Number")
            add_runs(p, text)
            i += 1
            continue

        # Blank line
        if not stripped:
            i += 1
            continue

        # Paragraph: gather consecutive non-empty, non-special lines
        buf_p = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if (not nxt) or nxt.startswith("#") or nxt.startswith("```") \
                    or nxt.startswith(">") or nxt.startswith("---") \
                    or nxt.lstrip().startswith("* ") or nxt.lstrip().startswith("- ") \
                    or re.match(r"^\d+\.\s+", nxt.lstrip()) \
                    or ("|" in nxt and i + 1 < len(lines) and is_table_sep(lines[i + 1])):
                break
            buf_p.append(nxt)
            i += 1
        p = doc.add_paragraph()
        add_runs(p, " ".join(buf_p))


def main() -> None:
    md_text = MD_FILE.read_text(encoding="utf-8")
    doc = Document()

    # Default body style
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    render_title_page(doc)
    render(md_text, doc)

    doc.save(OUT_DOCX)
    print(f"Wrote {OUT_DOCX}")


if __name__ == "__main__":
    main()
