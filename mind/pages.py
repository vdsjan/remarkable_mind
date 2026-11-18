"""Page chrome shared by all puzzle and solution pages.

Navigation is done with tappable buttons (PDF links), because the reMarkable
has no "back" gesture for link jumps. Every page therefore carries a way
home, a way to the game hub and previous/next buttons.
"""
from .draw import (button, circle, checkbox, fit_size, icon_bulb,
                   icon_calendar, icon_chevron, icon_grid, icon_home, line,
                   link, paragraph, rrect, stars, text, text_mid)
# Geometry names (W, H, M, PLAY_BOX, BAR_*, LEFT_SAFE, COMPACT) are rebound by
# theme.set_device() for the chosen device; LEFT_SAFE keeps the buttons clear
# of the reMarkable menu toggle in the top-left corner.
from .theme import (BAR_H, BAR_Y, BOTTOM_BAR_H, CATEGORIES, COMPACT, GREY, H,
                    INK, LEFT_SAFE, LEVEL_NAMES, M, MID, PLAY_BOX, W, WHITE)


def _icon_w():
    return BAR_H + (4 if COMPACT else 6)


def _icon_button(c, x, y, icon, dest, **kw):
    bw = _icon_w()
    button(c, x, y, bw, BAR_H, "", dest)
    icon(c, x + bw / 2, y + BAR_H / 2, 13 if COMPACT else 15, **kw)
    return x + bw + (5 if COMPACT else 6)


def top_bar(c, nav, hub_label=None, counter=None):
    """nav: dict with optional keys home, training, hub, prev, next."""
    nav = nav or {}
    x = LEFT_SAFE
    x = _icon_button(c, x, BAR_Y, icon_home, nav.get("home"))
    if nav.get("training", None) is not False:    # False: book without a day plan
        x = _icon_button(c, x, BAR_Y, icon_calendar, nav.get("training"))
    if hub_label and COMPACT:                 # no room for a label: grid icon
        x = _icon_button(c, x, BAR_Y, icon_grid, nav.get("hub"))
    elif hub_label:
        size = 10.5
        from reportlab.pdfbase.pdfmetrics import stringWidth
        w = stringWidth(hub_label, "SansS", size) + 26
        button(c, x, BAR_Y, w, BAR_H, hub_label, nav.get("hub"), size=size)
    # right side: previous / counter / next
    bw = _icon_w()
    xr = W - M - bw
    button(c, xr, BAR_Y, bw, BAR_H, "", nav.get("next"))
    icon_chevron(c, xr + bw / 2, BAR_Y + BAR_H / 2, 12 if COMPACT else 13, 1)
    cw = 46 if COMPACT else 60
    if counter:
        text_mid(c, xr - cw / 2, BAR_Y + BAR_H / 2, counter, "SansS",
                 fit_size(counter, "SansS", cw - 6, 9.5 if COMPACT else 10.5), INK)
        xl = xr - cw - bw
    else:
        xl = xr - 6 - bw
    button(c, xl, BAR_Y, bw, BAR_H, "", nav.get("prev"))
    icon_chevron(c, xl + bw / 2, BAR_Y + BAR_H / 2, 12 if COMPACT else 13, -1)


def title_block(c, game, index, level, subtitle="", prefix=""):
    """Game title with numbered badge, level stars and an instruction line."""
    cat = CATEGORIES[game.category]
    y = BAR_Y - (34 if COMPACT else 40)
    r = 14 if COMPACT else 17
    circle(c, M + r, y + 9, r, fill=cat["color"], stroke=None)
    text_mid(c, M + r, y + 9, str(index), "SansB",
             (15 if index < 10 else 13) * r / 17, cat["on"])
    name = (prefix + game.name) if prefix else game.name
    size = fit_size(name, "SerifB", W - 2 * M - (2 * r + 10) - (60 if COMPACT else 140),
                    21 if COMPACT else 25)
    text(c, M + 2 * r + 10, y + 1, name, "SerifB", size, INK)
    # level, right aligned
    lx = W - M - 3 * 13 - 2 if not COMPACT else W - M - 3 * 11 - 2
    stars(c, lx, y + 13, level, r=5 if not COMPACT else 4.3, color=INK)
    text(c, W - M, y - 3, LEVEL_NAMES[level - 1], "SansM", 8.5, GREY, "r")
    line(c, M, y - 12, W - M, y - 12, 1.4, INK)
    if subtitle:
        paragraph(c, M, y - (16 if COMPACT else 18), W - 2 * M, subtitle, "Sans",
                  9 if COMPACT else 9.5, color=INK)


def bottom_bar(c, left=None, right=None, mid=None):
    """Each of left/mid/right is None or (label, dest, filled)."""
    y = 14 if COMPACT else 16
    h = 30 if COMPACT else 34
    slots = {"l": left, "m": mid, "r": right}
    bw = min(150, (W - 2 * M - 10) / 2)
    xs = {"l": M, "m": (W - bw) / 2, "r": W - M - bw}
    for k, spec in slots.items():
        if not spec:
            continue
        label, dest, filled = spec
        button(c, xs[k], y, bw, h, label, dest, size=9.5 if COMPACT else 10.5,
               fill=INK if filled else None, fg=WHITE if filled else INK)


def tracker(c):
    """Pen fields in the bottom-left: time taken and a 'solved' tick box."""
    y = 14 if COMPACT else 16
    if COMPACT:
        text(c, M, y + 11, "Tijd", "SansM", 8, GREY)
        line(c, M + 21, y + 9, M + 56, y + 9, 0.8, INK)
        text(c, M + 64, y + 11, "Gelukt", "SansM", 8, GREY)
        checkbox(c, M + 95, y + 6, 14)
        return
    text(c, M, y + 13, "Tijd", "SansM", 8.5, GREY)
    line(c, M + 24, y + 11, M + 78, y + 11, 0.8, INK)
    text(c, M + 90, y + 13, "Gelukt", "SansM", 8.5, GREY)
    checkbox(c, M + 124, y + 7, 16)


def puzzle_page(c, game, puz, index, level, total, part=0, nav=None):
    nav = nav or {}
    top_bar(c, nav, hub_label=game.name, counter=f"{index} / {total}")
    title_block(c, game, index, level, game.instruction(puz, part))
    game.draw(c, PLAY_BOX, puz, solved=False, part=part)
    if part < game.parts - 1:
        bottom_bar(c, right=("Verder  ›", nav.get("continue"), True))
    else:
        tracker(c)
        bottom_bar(c, right=("Oplossing", nav.get("solution"), False))


def solution_page(c, game, puz, index, level, total, nav=None):
    nav = nav or {}
    top_bar(c, nav, hub_label=game.name, counter=f"{index} / {total}")
    title_block(c, game, index, level, prefix="Oplossing · ")
    game.draw(c, PLAY_BOX, puz, solved=True, part=game.parts - 1)
    bottom_bar(c, left=("‹  Terug naar puzzel", nav.get("back"), False),
               right=("Volgende puzzel  ›", nav.get("next_puzzle"), True))
