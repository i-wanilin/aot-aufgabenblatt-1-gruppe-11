"""Render projektskizze.md to a single submission HTML/PDF.

Diagrams (SVG) are embedded at the start of the sections that explain
them ("4. Klassen-diagramm" and "5. Sequenz-diagramm"), per the
assignment's requirement that the diagram come first, then the text.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
MD_FILE = ROOT / "projektskizze.md"
DIAGRAMS = ROOT / "diagrams"
OUT_HTML = ROOT / "projektskizze.html"

CLASS_SVG = (DIAGRAMS / "class-diagram.svg").read_text(encoding="utf-8")
CLASS_TYPES_SVG = (DIAGRAMS / "class-diagram-types.svg").read_text(encoding="utf-8")
SEQ_SVG = (DIAGRAMS / "sequence-diagram.svg").read_text(encoding="utf-8")


_svg_counter = [0]


def inline_svg(svg: str, caption: str) -> str:
    # Strip any XML prologue, drop the bundled fixed sizing/styling on the
    # root <svg>, and rewrite the id so multiple inlined SVGs don't collide.
    svg = re.sub(r"^<\?xml[^?]*\?>\s*", "", svg.strip())
    _svg_counter[0] += 1
    new_id = f"diagram-svg-{_svg_counter[0]}"

    def rewrite_svg_open(m: re.Match[str]) -> str:
        attrs = m.group(1)
        attrs = re.sub(r'\s(width|height|style|id)="[^"]*"', "", attrs)
        return f'<svg id="{new_id}"{attrs} style="max-width:100%;height:auto;">'

    svg = re.sub(r"<svg\b([^>]*)>", rewrite_svg_open, svg, count=1)
    # Mermaid puts a `#my-svg{...}` block in the embedded <style>; rescope
    # those rules to the new id so each diagram styles only itself.
    svg = svg.replace("#my-svg", f"#{new_id}")
    return (
        f'<figure class="diagram">\n{svg}\n'
        f"<figcaption>{caption}</figcaption>\n</figure>\n"
    )


def inject_diagrams(md_text: str) -> str:
    # Insert class diagram right after the "## 4. ..." heading line,
    # and the sequence diagram right after the "## 5. ..." heading line.
    def insert_after_h2(text: str, h2_prefix: str, payload: str) -> str:
        # Match the H2 line, capture any blank lines after it, then inject.
        pattern = re.compile(
            r"^(##\s+" + re.escape(h2_prefix) + r"[^\n]*\n)",
            re.MULTILINE,
        )
        replaced = pattern.sub(lambda m: m.group(1) + "\n" + payload + "\n", text, count=1)
        if replaced == text:
            print(f"WARNING: heading '## {h2_prefix}' not found", file=sys.stderr)
        return replaced

    class_panels = (
        inline_svg(
            CLASS_SVG,
            "Abbildung 1a: Klassendiagramm – Struktur und Komposition.",
        )
        + inline_svg(
            CLASS_TYPES_SVG,
            "Abbildung 1b: Klassendiagramm – Wertobjekte (Item-/Action-Hierarchie) "
            "und Botschafts­objekte zwischen Manager und Agent.",
        )
    )
    md_text = insert_after_h2(md_text, "4. ", class_panels)
    md_text = insert_after_h2(
        md_text,
        "5. ",
        inline_svg(SEQ_SVG, "Abbildung 2: Sequenzdiagramm eines Ticks."),
    )
    return md_text


CSS = """
@page { size: A4; margin: 22mm 20mm; }
html { font-size: 11pt; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; color: #1a1a1a; line-height: 1.45; }
h1 { font-size: 1.8rem; margin-top: 0; }
h2 { font-size: 1.3rem; margin-top: 1.6em; border-bottom: 1px solid #ddd; padding-bottom: 0.2em; }
h3 { font-size: 1.05rem; margin-top: 1.2em; }
h4 { font-size: 0.95rem; }
p, li { font-size: 0.95rem; }
code, pre { font-family: "Consolas", "Menlo", monospace; font-size: 0.85rem; }
pre { background: #f5f5f5; padding: 0.6em 0.8em; border-radius: 4px; overflow-x: auto; page-break-inside: avoid; }
code { background: #f5f5f5; padding: 0 0.2em; border-radius: 3px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 0.6em 0; width: 100%; font-size: 0.9rem; }
th, td { border: 1px solid #bbb; padding: 0.35em 0.55em; text-align: left; vertical-align: top; }
th { background: #eee; }
blockquote { border-left: 3px solid #888; margin: 0.6em 0; padding: 0.2em 0.9em; color: #444; background: #fafafa; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.6em 0; }
figure.diagram { margin: 1em 0 1.4em; page-break-inside: avoid; text-align: center; }
figure.diagram svg { max-width: 100%; height: auto; }
figure.diagram figcaption { font-size: 0.85rem; color: #555; margin-top: 0.4em; font-style: italic; }
a { color: #1a4f8a; text-decoration: none; }
.titlepage { page-break-after: always; text-align: center; padding-top: 30vh; }
.titlepage h1 { font-size: 2.2rem; margin-bottom: 0.3em; }
.titlepage .meta { font-size: 1rem; color: #444; line-height: 1.8; }
"""

TITLE_PAGE = """
<div class="titlepage">
  <h1>Aufgabenblatt 1<br>Projektskizze: Schwarmintelligenz</h1>
  <div class="meta">
    Agententechnologien — Grundlagen und Anwendungen<br>
    TU Berlin, Sommersemester 2026<br><br>
    <strong>Gruppe 11</strong><br>
    Ivan Wanylyn<br><br>
    Abgabe: 04.05.2026
  </div>
</div>
"""


def main() -> None:
    md_text = MD_FILE.read_text(encoding="utf-8")
    md_text = inject_diagrams(md_text)

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
        output_format="html5",
    )

    html = (
        "<!doctype html><html lang=\"de\"><head>"
        "<meta charset=\"utf-8\">"
        "<title>Projektskizze – Schwarmintelligenz (Gruppe 11)</title>"
        f"<style>{CSS}</style></head><body>"
        f"{TITLE_PAGE}{body}"
        "</body></html>"
    )

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
