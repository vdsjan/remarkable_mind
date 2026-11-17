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

# --- device profiles ----------------------------------------------------------
# Both tablets have a 3:4 screen, so the page geometry is shared. The
# reMarkable 2 is monochrome: its profile maps every spot colour to a grey
# that stays distinguishable on a 16-level e-ink panel, and swaps the few
# texts and puzzles that rely on colour.
DEVICES = {
    "paperpro": {"label": "reMarkable Paper Pro", "screen": "11,8 inch, kleur",
                 "px": (1620, 2160), "mono": False, "suffix": ""},
    "rm2": {"label": "reMarkable 2", "screen": "10,3 inch, zwart-wit",
            "px": (1404, 1872), "mono": True, "suffix": "-rM2"},
}
DEVICE = DEVICES["paperpro"]
MONO = False

_SPOT = {"RED": RED, "TEAL": TEAL, "MUSTARD": MUSTARD, "PEN": PEN,
         "GREEN": GREEN, "PURPLE": PURPLE, "ORANGE": ORANGE}
_COLOUR_RGB = {k: v.rgb() for k, v in _SPOT.items()}
_GREY_HEX = {"RED": "#3C3C3C", "TEAL": "#787878", "MUSTARD": "#D0D0D0",
             "PEN": "#505050", "GREEN": "#555555", "PURPLE": "#8C8C8C",
             "ORANGE": "#A6A6A6"}
_MONO_TEXT = [
    ("van de rode pijl", "van de pijl"),
    ("de gele vakjes", "de grijze vakjes"),
    ("Verbind de kleuren en laat", "Verbind de letters en laat"),
    ("met dezelfde letter en kleur", "met dezelfde letter"),
    (" Pak er gerust de kleurpennen van je Paper Pro bij.", ""),
    ("blauwe lucifer", "grijze lucifer"),
]


def set_device(name):
    """Switch the whole book to a device profile ("paperpro" or "rm2").

    The colour objects are changed in place, so every module that imported
    them follows along."""
    global DEVICE, MONO
    DEVICE = DEVICES[name]
    MONO = DEVICE["mono"]
    for key, colour in _SPOT.items():
        rgb = HexColor(_GREY_HEX[key]).rgb() if MONO else _COLOUR_RGB[key]
        colour.red, colour.green, colour.blue = rgb
    return DEVICE


def localize(s):
    """Text for the current device: drops references to colour on mono."""
    if MONO and isinstance(s, str):
        for old, new in _MONO_TEXT:
            s = s.replace(old, new)
    return s


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
