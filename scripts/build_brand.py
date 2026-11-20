# SPDX-License-Identifier: MIT
"""Generate the Thermogeist logo files (spec BRD-001 to BRD-004).

Writes the SVG sources to ``brand/`` and, if ``rsvg-convert`` is installed, the PNG exports.
Usage: python3 scripts/build_brand.py
"""

import shutil
import subprocess
from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parent.parent / "brand"

NIGHT_BLUE = "#0F1720"
CAP = "#DDE4EB"
BODY = "#F4F7FA"
METAL = "#AEBBC8"
METAL_LIGHT = "#D3DAE1"
GROOVE = "#8796A6"
MINT = "#3DDC97"
MINT_ON_LIGHT = "#1FA870"
AMBER = "#FFB547"
GREY_TEXT_DARK = "#9AA8B6"
GREY_TEXT_LIGHT = "#5B6B7B"

# The body overlaps the lower edge of the cap, so the visible cap spans y = 25..61.
# The grooves are centred on that visible part (centre y = 43).
GROOVES = "\n".join(f'      <line x1="{x}" y1="31" x2="{x}" y2="55"/>' for x in range(92, 165, 12))

# Thermostat seen from the side: grooved cap, white body with a visor and two mint eyes,
# amber status LED, hex union nut. Light fills plus a dark outline keep it visible on any
# background.
MARK = f"""  <g stroke="{NIGHT_BLUE}" stroke-width="6" stroke-linejoin="round">
    <rect x="96" y="186" width="64" height="30" rx="4" fill="{METAL}"/>
    <rect x="78" y="22" width="100" height="46" rx="13" fill="{CAP}"/>
    <rect x="72" y="64" width="112" height="124" rx="18" fill="{BODY}"/>
  </g>
  <rect x="112" y="191" width="32" height="22" fill="{METAL_LIGHT}"/>
  <g stroke="{GROOVE}" stroke-width="3.5" stroke-linecap="round">
{GROOVES}
  </g>
  <rect x="90" y="86" width="76" height="44" rx="22" fill="{NIGHT_BLUE}"/>
  <rect x="108" y="96" width="12" height="22" rx="6" fill="{MINT}"/>
  <rect x="136" y="96" width="12" height="22" rx="6" fill="{MINT}"/>
  <circle cx="128" cy="160" r="5" fill="{AMBER}"/>"""

MARK_256 = f'  <g transform="translate(0 8)">\n{MARK}\n  </g>'


def _svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n  <title>Thermogeist</title>\n{body}\n</svg>\n'
    )


def _logo(background: str | None, text: str, cursor: str, tagline: str) -> str:
    rect = f'  <rect width="640" height="180" rx="24" fill="{background}"/>\n' if background else ""
    return _svg(
        640,
        180,
        f"""{rect}  <g transform="translate(22 14) scale(0.6)">
{MARK}
  </g>
  <text x="182" y="100" font-family="JetBrains Mono, ui-monospace, Menlo, monospace" \
font-size="54" font-weight="700" fill="{text}">thermogeist<tspan fill="{cursor}">_</tspan></text>
  <text x="184" y="132" font-family="Inter, -apple-system, Helvetica, sans-serif" \
font-size="17" letter-spacing="3" fill="{tagline}">CALM RADIATOR CONTROL</text>""",
    )


FILES = {
    "icon.svg": _svg(
        256, 256, f'  <rect width="256" height="256" rx="56" fill="{NIGHT_BLUE}"/>\n' + MARK_256
    ),
    "icon-transparent.svg": _svg(256, 256, MARK_256),
    "logo.svg": _logo(NIGHT_BLUE, BODY, MINT, GREY_TEXT_DARK),
    "logo-light.svg": _logo(None, NIGHT_BLUE, MINT_ON_LIGHT, GREY_TEXT_LIGHT),
}

PNG_EXPORTS = [
    ("icon.svg", "icon.png", 256),
    ("icon.svg", "icon@2x.png", 512),
    ("icon-transparent.svg", "icon-transparent.png", 256),
    ("icon-transparent.svg", "icon-transparent@2x.png", 512),
    ("logo.svg", "logo.png", 640),
    ("logo-light.svg", "logo-light.png", 640),
]


def main() -> None:
    BRAND_DIR.mkdir(exist_ok=True)
    for name, content in FILES.items():
        (BRAND_DIR / name).write_text(content, encoding="utf-8")
    converter = shutil.which("rsvg-convert")
    if converter is None:
        print("rsvg-convert not found: SVGs written, PNG export skipped")
        return
    for source, target, width in PNG_EXPORTS:
        subprocess.run(
            [converter, "-w", str(width), str(BRAND_DIR / source), "-o", str(BRAND_DIR / target)],
            check=True,
        )
    print(f"Brand files written to {BRAND_DIR}")


if __name__ == "__main__":
    main()
