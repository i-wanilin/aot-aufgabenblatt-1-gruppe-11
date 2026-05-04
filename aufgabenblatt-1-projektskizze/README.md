# Aufgabenblatt 1 – Projektskizze (AOT, SoSe 2026)

Projektskizze zur Aufgabe **Schwarmintelligenz: Ameisenkolonie‑Simulation**
im Kurs *Agententechnologien – Grundlagen und Anwendungen* (TU Berlin,
ISIS‑Modul 2228089).

Dieses Repository enthält ausschließlich die **Entwurfsdokumente** (30 % der
Aufgabenblatt‑Note). Die Implementierung folgt im Repository
`aot-aufgabenblatt-1-projektdokumentation`.

## Struktur

```
.
├── projektskizze.md           # Hauptdokument (Systementwurf, Forschungsfrage, Logging, Plan)
├── diagrams/
│   ├── class-diagram.mmd      # Mermaid-Klassendiagramm
│   └── sequence-diagram.mmd   # Mermaid-Sequenzdiagramm (Tick-Ablauf)
├── config/
│   ├── world_default.json     # Beispielkonfiguration der Simulation
│   └── world.schema.json      # JSON-Schema zur Validierung
└── README.md
```

## Lesen / Rendern

* Die Mermaid‑Dateien lassen sich auf `https://mermaid.live` direkt einfügen
  oder in jedem Markdown‑Renderer mit Mermaid‑Plugin betrachten.
* `projektskizze.md` ist das einzureichende Hauptdokument; alle anderen Dateien
  sind Anhänge.

## Validierung der Beispielkonfiguration

```bash
pip install jsonschema
python3 -c "import json, jsonschema; \
  jsonschema.validate(json.load(open('config/world_default.json')), \
                      json.load(open('config/world.schema.json'))); \
  print('OK')"
```

