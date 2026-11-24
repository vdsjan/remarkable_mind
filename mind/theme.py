"""Visual identity of Remarkable Mind: page geometry, colours and fonts.

Every device gets a page with exactly the aspect ratio of its screen, so each
page fills the display edge to edge:

* reMarkable Paper Pro: 3:4, 1620 x 2160 px, 11.8", colour
* reMarkable 2: 3:4, 1404 x 1872 px, 10.3", greyscale
* reMarkable Paper Pro Move: 9:16, 954 x 1696 px, 7.3", colour

Colours are bold, saturated spot colours: the Gallery 3 colour e-ink panel
renders those far better than pastel tints or gradients.
"""
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
ASSET_DIR = ROOT / "assets"

# --- page geometry (points) -------------------------------------------------
# "wide" is the 3:4 page of the Paper Pro and the reMarkable 2 (510 pt is
# almost exactly the physical width of the Paper Pro screen). "tall" is the
# 9:16 page of the Paper Pro Move: 320 pt wide, shown at about 81% of its
# nominal size on the 7.3" screen, so the layout uses tighter margins.
GEOMETRIES = {
    "wide": {"W": 510.0, "H": 680.0, "M": 28.0, "TOP_RESERVE": 150.0,
             "BOTTOM_BAR_H": 54.0, "BAR_H": 32.0, "BAR_TOP": 22.0,
             "LEFT_SAFE": 46.0, "COMPACT": False},
    "tall": {"W": 320.0, "H": 320.0 * 16 / 9, "M": 16.0, "TOP_RESERVE": 156.0,
             "BOTTOM_BAR_H": 50.0, "BAR_H": 28.0, "BAR_TOP": 16.0,
             "LEFT_SAFE": 40.0, "COMPACT": True},
}
GEOMETRY_KEYS = ("W", "H", "M", "TOP_BAR_Y", "BOTTOM_BAR_H", "PLAY_BOX",
                 "BAR_H", "BAR_Y", "LEFT_SAFE", "COMPACT")


def _derive(g):
    d = dict(g)
    d["TOP_BAR_Y"] = d["H"] - 62.0          # bottom edge of the top navigation bar
    d["BAR_Y"] = d["H"] - d["BAR_TOP"] - d["BAR_H"]
    # Area a game may draw in on a puzzle page: (x, y, w, h), y = bottom edge.
    d["PLAY_BOX"] = (d["M"], d["BOTTOM_BAR_H"] + 16, d["W"] - 2 * d["M"],
                     d["H"] - d["TOP_RESERVE"] - d["BOTTOM_BAR_H"] - 16)
    return d


globals().update({k: v for k, v in _derive(GEOMETRIES["wide"]).items()
                  if k in GEOMETRY_KEYS})

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
             "blurb": "Woorden, codes, verhalen en onthouden"},
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
                 "px": (1620, 2160), "mono": False, "suffix": "",
                 "geometry": "wide"},
    "move": {"label": "reMarkable Paper Pro Move", "screen": "7,3 inch, kleur",
             "px": (954, 1696), "mono": False, "suffix": "-Move",
             "geometry": "tall"},
    "rm2": {"label": "reMarkable 2", "screen": "10,3 inch, zwart-wit",
            "px": (1404, 1872), "mono": True, "suffix": "-rM2",
            "geometry": "wide"},
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
    """Switch the whole book to a device profile ("paperpro", "move", "rm2").

    The colour objects are changed in place, so every module that imported
    them follows along. Geometry values are numbers, which cannot change in
    place: they are rebound here and in every loaded ``mind`` module that
    imported them by name (``from .theme import W``), so the page code keeps
    using plain names."""
    global DEVICE, MONO
    DEVICE = DEVICES[name]
    MONO = DEVICE["mono"]
    for key, colour in _SPOT.items():
        rgb = HexColor(_GREY_HEX[key]).rgb() if MONO else _COLOUR_RGB[key]
        colour.red, colour.green, colour.blue = rgb
    geo = {k: v for k, v in _derive(GEOMETRIES[DEVICE["geometry"]]).items()
           if k in GEOMETRY_KEYS}
    globals().update(geo)
    package = __name__.rsplit(".", 1)[0]
    for mod_name, mod in list(sys.modules.items()):
        spec = getattr(mod, "__spec__", None)
        real = spec.name if spec is not None else mod_name   # "python -m mind.book"
        if mod is None or not real.startswith(package + ".") or real == __name__:
            continue
        for k, v in geo.items():
            if k in vars(mod):
                setattr(mod, k, v)
    return DEVICE


def device_key():
    return next(k for k, v in DEVICES.items() if v is DEVICE)


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
