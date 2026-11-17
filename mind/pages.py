"""Page chrome shared by all puzzle and solution pages.

Navigation is done with tappable buttons (PDF links), because the reMarkable
has no "back" gesture for link jumps. Every page therefore carries a way
home, a way to the game hub and previous/next buttons.
"""
from .draw import (button, circle, checkbox, fit_size, icon_bulb,
                   icon_calendar, icon_chevron, icon_home, line, link,
                   paragraph, rrect, stars, text, text_mid)
from .theme import (BOTTOM_BAR_H, CATEGORIES, GREY, H, INK, LEVEL_NAMES, M,
                    MID, PLAY_BOX, W, WHITE)

BAR_H = 32.0
BAR_Y = H - 22.0 - BAR_H
LEFT_SAFE = 46.0   # keep clear of the reMarkable menu toggle in the top-left


def _icon_button(c, x, y, icon, dest, **kw):
    button(c, x, y, BAR_H + 6, BAR_H, "", dest)
    icon(c, x + (BAR_H + 6) / 2, y + BAR_H / 2, 15, **kw)
    return x + BAR_H + 6 + 6


def top_bar(c, nav, hub_label=None, counter=None):
    """nav: dict with optional keys home, training, hub, prev, next."""
    nav = nav or {}
    x = LEFT_SAFE
    x = _icon_button(c, x, BAR_Y, icon_home, nav.get("home"))
    x = _icon_button(c, x, BAR_Y, icon_calendar, nav.get("training"))
    if hub_label:
        size = 10.5
        from reportlab.pdfbase.pdfmetrics import stringWidth
        w = stringWidth(hub_label, "SansS", size) + 26
        button(c, x, BAR_Y, w, BAR_H, hub_label, nav.get("hub"), size=size)
    # right side: previous / counter / next
    bw = BAR_H + 6
    xr = W - M - bw
    button(c, xr, BAR_Y, bw, BAR_H, "", nav.get("next"))
    icon_chevron(c, xr + bw / 2, BAR_Y + BAR_H / 2, 13, 1)
    if counter:
        text_mid(c, xr - 30, BAR_Y + BAR_H / 2, counter, "SansS", 10.5, INK)
        xl = xr - 60 - bw
    else:
        xl = xr - 6 - bw
    button(c, xl, BAR_Y, bw, BAR_H, "", nav.get("prev"))
    icon_chevron(c, xl + bw / 2, BAR_Y + BAR_H / 2, 13, -1)


def title_block(c, game, index, level, subtitle="", prefix=""):
    """Game title with numbered badge, level stars and an instruction line."""
    cat = CATEGORIES[game.category]
    y = BAR_Y - 40
    r = 17
    circle(c, M + r, y + 9, r, fill=cat["color"], stroke=None)
    text_mid(c, M + r, y + 9, str(index), "SansB", 15 if index < 10 else 13,
             cat["on"])
    name = (prefix + game.name) if prefix else game.name
    size = fit_size(name, "SerifB", W - 2 * M - 180, 25)
    text(c, M + 2 * r + 10, y + 1, name, "SerifB", size, INK)
    # level, right aligned
    lx = W - M - 3 * 13 - 2
    stars(c, lx, y + 13, level, r=5, color=INK)
    text(c, W - M, y - 3, LEVEL_NAMES[level - 1], "SansM", 8.5, GREY, "r")
    line(c, M, y - 12, W - M, y - 12, 1.4, INK)
    if subtitle:
        paragraph(c, M, y - 18, W - 2 * M, subtitle, "Sans", 9.5, color=INK)


def bottom_bar(c, left=None, right=None, mid=None):
    """Each of left/mid/right is None or (label, dest, filled)."""
    y = 16
    h = 34
    slots = {"l": left, "m": mid, "r": right}
    bw = 150
    xs = {"l": M, "m": (W - bw) / 2, "r": W - M - bw}
    for k, spec in slots.items():
        if not spec:
            continue
        label, dest, filled = spec
        button(c, xs[k], y, bw, h, label, dest,
               fill=INK if filled else None, fg=WHITE if filled else INK)


def tracker(c):
    """Pen fields in the bottom-left: time taken and a 'solved' tick box."""
    y = 16
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
