"""Render system-design.md to system-design.pdf (one page, A4)."""
from __future__ import annotations

from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).parent
MD_FILE = ROOT / "system-design.md"
OUT_PDF = ROOT / "system-design.pdf"

CSS = """
@page { size: A4; margin: 20mm 22mm; }
html { font-size: 9.8pt; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; color: #1a1a1a; line-height: 1.45; }
h1 { font-size: 1.4rem; margin: 0 0 0.8em; }
h2 { font-size: 1.05rem; margin: 1.3em 0 0.55em; border-bottom: 1px solid #ddd; padding-bottom: 0.15em; }
p, li { font-size: 0.94rem; margin: 0.45em 0; }
ul { margin: 0.45em 0 0.5em 1.2em; padding: 0; }
li { margin: 0.35em 0; }
code { font-family: "Consolas", "Menlo", monospace; font-size: 0.86rem;
       background: #f5f5f5; padding: 0 0.2em; border-radius: 3px; }
"""


def main() -> None:
    body = markdown.markdown(
        MD_FILE.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )
    html = (
        '<!doctype html><html lang="de"><head><meta charset="utf-8">'
        f"<title>Systemdesign — Gruppe 11</title><style>{CSS}</style>"
        f"</head><body>{body}</body></html>"
    )
    HTML(string=html, base_url=str(ROOT)).write_pdf(OUT_PDF)
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
