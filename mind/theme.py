"""Visual identity of Remarkable Mind: page geometry, colours and fonts.

The page is exactly 3:4, the aspect ratio of the reMarkable Paper Pro screen
(1620 x 2160 px, 11.8"), so every page fills the display edge to edge.
Colours are bold, saturated spot colours: the Gallery 3 colour e-ink panel
renders those far better than pastel tints or gradients.
"""
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
ASSET_DIR = ROOT / "assets"

# --- page geometry (points) -------------------------------------------------
W, H = 510.0, 680.0          # 3:4, ~180 x 240 mm
M = 28.0                     # outer margin
TOP_BAR_Y = H - 62.0         # bottom edge of the top navigation bar
BOTTOM_BAR_H = 54.0          # height reserved for the bottom bar
# Area a game may draw in on a puzzle page: (x, y, w, h), y = bottom edge.
PLAY_BOX = (M, BOTTOM_BAR_H + 16, W - 2 * M, H - 150 - BOTTOM_BAR_H - 16)

# --- colours ----------------------------------------------------------------
INK = HexColor("#141414")
WHITE = HexColor("#FFFFFF")
RED = HexColor("#D8432B")
TEAL = HexColor("#0F7F86")
MUSTARD = HexColor("#E2A019")
PEN = HexColor("#1D4FD8")      # "handwritten" solutions, like blue pen ink
GREEN = HexColor("#2F8F4E")
PURPLE = HexColor("#7B3FA0")
ORANGE = HexColor("#E8741C")
GREY = HexColor("#6F6F6F")
MID = HexColor("#B4B4B4")
LIGHT = HexColor("#E8E8E8")
PAPER = HexColor("#F6F1E6")

# Palette for puzzles that need many distinguishable colours.
PALETTE = [RED, TEAL, MUSTARD, PEN, GREEN, PURPLE, ORANGE, INK]

CATEGORIES = {
    "getallen": {"name": "Getallen", "color": RED, "on": WHITE,
                 "blurb": "Rekenen, tellen en combineren"},
    "logica": {"name": "Logica", "color": TEAL, "on": WHITE,
               "blurb": "Redeneren zonder te gokken"},
    "ruimte": {"name": "Ruimte", "color": MUSTARD, "on": INK,
               "blurb": "Kijken, draaien en verbinden"},
    "taal": {"name": "Taal & Geheugen", "color": INK, "on": WHITE,
             "blurb": "Woorden, codes en onthouden"},
}
CATEGORY_ORDER = ["getallen", "logica", "ruimte", "taal"]

LEVEL_NAMES = ("Opwarmen", "Pittig", "Meesterlijk")

# --- fonts ------------------------------------------------------------------
_FONTS = {
    "Serif": "Fraunces-600.ttf",
    "SerifB": "Fraunces-700.ttf",
    "SerifX": "Fraunces-900.ttf",
    "SerifR": "Fraunces-400.ttf",
    "SerifI": "Fraunces-400.ttf",      # upright: the italic's swashes hurt legibility
    "Sans": "Inter-400.ttf",
    "SansM": "Inter-500.ttf",
    "SansS": "Inter-600.ttf",
    "SansB": "Inter-700.ttf",
    "SansX": "Inter-800.ttf",
    "Hand": "Caveat-700.ttf",
    "HandM": "Caveat-500.ttf",
}
_registered = False


def register_fonts():
    """Register the bundled OFL fonts with reportlab (idempotent)."""
    global _registered
    if _registered:
        return
    for name, filename in _FONTS.items():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
    _registered = True
