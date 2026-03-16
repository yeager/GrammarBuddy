# GrammarBuddy – Svensk grammatikträning med AI

En GTK4/Adwaita-applikation för att träna svensk grammatik, designad för SFI-elever och alla som vill förbättra sin svenska.

## Funktioner

- **Textanalys** – Skriv meningar och få grammatikfeedback på lättläst svenska
- **Övningslägen** – Stavning, meningsbyggnad, tempus och ordföljd
- **Svårighetsnivåer** – SFI A (grundläggande) till Avancerat
- **Progress tracking** – Statistik, sviträknare och resultathistorik
- **AI-integration** – Valfri OpenAI-integration för djupare analys
- **Lokalisering** – Svenska som huvudspråk, engelsk fallback (i18n med gettext)
- **ARASAAC-kompatibel design** – Tydligt gränssnitt för språkinlärning

## Krav

- Python 3.10+
- GTK4 och libadwaita
- PyGObject

## Installation

### Ubuntu/Debian

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
pip install -e .
```

### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita
pip install -e .
```

### macOS (Homebrew)

```bash
brew install gtk4 libadwaita pygobject3
pip install -e .
```

### Arch Linux

```bash
sudo pacman -S python-gobject gtk4 libadwaita
pip install -e .
```

## Användning

```bash
# Kör direkt
python -m grammarbuddy

# Eller efter installation
grammarbuddy
```

## AI-integration (valfritt)

Sätt miljövariabeln för AI-baserad grammatikanalys:

```bash
export OPENAI_API_KEY="din-api-nyckel"
grammarbuddy
```

Utan API-nyckel används den inbyggda regelbaserade analysen.

## Övningslägen

| Läge | Beskrivning |
|------|-------------|
| Stavning | Öva verb- och ordformer |
| Meningsbyggnad | Bygg korrekta meningar |
| Tempus | Öva verbböjning i olika tempus |
| Ordföljd | Lär dig svensk ordföljd (V2-regeln) |
| Fri skrivning | Skriv fritt och få feedback |

## Svårighetsnivåer

- **SFI A** – Grundläggande: enkel presens, vanliga ord
- **SFI B** – Fortsättning: preteritum, frågor
- **SFI C** – Mellannivå: perfekt, bisatser
- **SFI D** – Avancerad: pluskvamperfekt, passiv
- **Avancerat** – Konjunktiv, korrelativa konjunktioner

## Projektstruktur

```
GrammarBuddy/
├── grammarbuddy/
│   ├── __init__.py          # Paketinfo
│   ├── __main__.py          # python -m entry point
│   ├── app.py               # Gtk.Application
│   ├── grammar_engine.py    # Grammatikmotor & övningar
│   ├── progress.py          # Progress tracking & settings
│   └── window.py            # GTK4 UI
├── data/
│   └── se.grammarbuddy.app.desktop
├── po/
│   ├── grammarbuddy.pot     # Översättningsmall
│   ├── sv/LC_MESSAGES/      # Svenska
│   └── en/LC_MESSAGES/      # Engelska
├── tests/
│   └── test_grammar_engine.py
├── requirements.txt
├── setup.py
└── README.md
```

## Tester

```bash
python -m pytest tests/
```

## Licens

MIT
