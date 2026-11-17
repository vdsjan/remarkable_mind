"""Assemble the complete Remarkable Mind book.

    python -m mind.book --seed 2026                  # Paper Pro, colour
    python -m mind.book --seed 2026 --device rm2     # reMarkable 2, greyscale

The "app" is one PDF: every button is an internal link, so it runs on a
stock reMarkable (Paper Pro in colour, reMarkable 2 in greyscale) without
developer mode and without any network.
"""
import argparse
import hashlib
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from reportlab.pdfgen import canvas

from . import __version__, games, theme
from .draw import (button, checkbox, circle, fit_size, icon_bulb,
                   icon_calendar, icon_check, icon_chevron, icon_grid,
                   icon_home, line, link, paragraph, rrect, stars, text,
                   text_mid, wrap)
from .pages import BAR_H, BAR_Y, LEFT_SAFE, puzzle_page, solution_page, top_bar
from .theme import (ASSET_DIR, CATEGORIES, CATEGORY_ORDER, GREY, H, INK,
                    LEVEL_NAMES, LIGHT, M, MID, MUSTARD, PEN, PLAY_BOX, RED,
                    TEAL, W, WHITE, register_fonts)

ROOT = Path(__file__).resolve().parents[1]
TITLE = "Remarkable Mind"
SUBTITLE = "Hersengym op papier"
DAYS = 30
# Games whose puzzles are too text-heavy to shrink into a hub-page example.
NO_EXAMPLE = {"geheugen", "woordzoeker", "logigram", "codekraker",
              "letterchaos", "reeksen"}


# --- puzzle generation --------------------------------------------------------
def level_of(game, i):
    """Level (1..3) of the i-th puzzle (0-based) of a game."""
    a, b, _ = game.counts
    return 1 if i < a else (2 if i < a + b else 3)


def _generate_game(args):
    key, seed, device = args
    theme.set_device(device)                # worker processes start in colour
    game = games.get(key)
    out, seen = [], set()
    for i in range(sum(game.counts)):
        level = level_of(game, i)
        salt = 0
        while True:
            rng = random.Random(f"{seed}:{key}:{i}:{salt}")
            puz = game.generate(rng, level)
            sig = json.dumps(puz, sort_keys=True)
            marks = set(game.fingerprints(puz))
            # never print the same puzzle twice, and avoid repeating a theme,
            # proverb or picture as long as fresh material is available
            if sig not in seen and (not marks & seen or salt >= 400):
                break
            salt += 1
            if salt > 800:
                raise RuntimeError(f"{key}: cannot generate a new puzzle {i + 1}")
        seen.add(sig)
        seen |= marks
        out.append(puz)
    return key, out


def build_puzzles(seed, cache_dir, jobs=4, log=print, all_games=None):
    """Generate (or load from cache) all puzzles: {key: [puzzle, ...]}."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    result, todo = {}, []
    for game in all_games or games.all_games():
        src = Path(sys.modules[type(game).__module__].__file__).read_bytes()
        tag = hashlib.sha1(src + str(game.counts).encode()).hexdigest()[:10]
        mono = "-mono" if theme.MONO else ""   # a few games differ without colour
        path = cache_dir / f"{seed}-{game.key}-{tag}{mono}.json"
        if path.exists():
            result[game.key] = json.loads(path.read_text())
        else:
            todo.append((game.key, path))
    if todo:
        log(f"generating {len(todo)} games ...")
        device = next(k for k, v in theme.DEVICES.items() if v is theme.DEVICE)
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            for key, puzzles in pool.map(_generate_game,
                                         [(k, seed, device) for k, _ in todo]):
                path = dict(todo)[key]
                path.write_text(json.dumps(puzzles))
                result[key] = puzzles
                log(f"  {key}: {len(puzzles)} puzzles")
    return result


# --- the 30-day plan ----------------------------------------------------------
def training_plan(all_games):
    """30 days x 4 puzzles: one per category, difficulty rising over the month.

    Returns a list of days; each day is a list of (game, puzzle_index0)."""
    by_cat = {cat: [g for g in all_games if g.category == cat]
              for cat in CATEGORY_ORDER}
    used = {g.key: 0 for g in all_games}
    plan = []
    for day in range(DAYS):
        row = []
        for cat in CATEGORY_ORDER:
            cat_games = by_cat[cat]
            if not cat_games:               # only happens in partial dev builds
                continue
            game = cat_games[day % len(cat_games)]
            n = sum(game.counts)
            visits = -(-DAYS // len(cat_games))          # ceil
            idx = round(used[game.key] * (n - 1) / max(1, visits - 1))
            used[game.key] += 1
            row.append((game, min(idx, n - 1)))
        plan.append(row)
    return plan


# --- page drawing ---------------------------------------------------------------
def asset(name):
    """Artwork for the current device (greyscale version on mono screens)."""
    return str(ASSET_DIR / f"{name}{'_grey' if theme.MONO else ''}.jpg")


def image(c, name, x, y, w, h):
    c.drawImage(asset(name), x, y, w, h, preserveAspectRatio=True, anchor="c")


def page_cover(c, ctx):
    c.drawImage(asset("cover"), 0, 0, W, H)
    text(c, W / 2, H - 92, TITLE, "SerifX", 47, INK, "c")
    text(c, W / 2, H - 122, SUBTITLE.upper(), "SansB", 12.5, RED, "c")
    c.setFont("SansB", 12.5)
    info = f"{ctx['n_games']} spellen  ·  {ctx['n_puzzles']} puzzels  ·  100% offline"
    text(c, W / 2, H - 146, info, "SansM", 10, INK, "c")
    bw, bh = 190, 40
    button(c, (W - bw) / 2, 30, bw, bh, "Tik om te starten  ›", "home",
           fill=INK, fg=WHITE, size=12.5)
    link(c, (0, 0, W, H), "home")


def _wordmark(c, y):
    text(c, M, y, TITLE, "SerifX", 22, INK)
    text(c, M + 1, y - 14, SUBTITLE.upper(), "SansB", 7.6, RED)


def page_home(c, ctx):
    _wordmark(c, H - 62)
    # shortcuts, top right
    bw, bh, gap = 72, 30, 6
    x = W - M - 3 * bw - 2 * gap
    for label, dest, filled in (("30 dagen", "training1", True),
                                ("Scorebord", "score", False),
                                ("Uitleg", "howto", False)):
        button(c, x, H - 72, bw, bh, label, dest, fill=INK if filled else None,
               fg=WHITE if filled else INK, size=9.5)
        x += bw + gap
    line(c, M, H - 90, W - M, H - 90, 1.4, INK)

    top = H - 102
    band_h = (top - 26) / 4
    tw = (W - 2 * M - 3 * 9) / 4
    for ci, cat in enumerate(CATEGORY_ORDER):
        info = CATEGORIES[cat]
        y0 = top - ci * band_h
        # category header: colour pill + blurb
        pill_w = 20 + c.stringWidth(info["name"], "SansB", 9.5)
        rrect(c, M, y0 - 18, pill_w, 18, 9, fill=info["color"], stroke=None)
        text_mid(c, M + pill_w / 2, y0 - 9, info["name"], "SansB", 9.5, info["on"])
        text(c, M + pill_w + 8, y0 - 12.5, info["blurb"], "Sans", 9, GREY)
        th = band_h - 18 - 6 - 12
        ty = y0 - 18 - 6 - th
        for gi, game in enumerate([g for g in ctx["games"] if g.category == cat]):
            tx = M + gi * (tw + 9)
            rrect(c, tx, ty, tw, th, 9, stroke=INK, lw=1.3)
            c.saveState()
            p = c.beginPath()
            p.roundRect(tx, ty, tw, th, 9)
            c.clipPath(p, stroke=0, fill=0)
            c.setFillColor(info["color"])
            c.rect(tx, ty + th - 7, tw, 7, stroke=0, fill=1)
            c.restoreState()
            rrect(c, tx, ty, tw, th, 9, stroke=INK, lw=1.3)
            game.icon(c, tx + tw / 2, ty + th / 2 + 6, min(40, th * 0.45), INK)
            size = fit_size(game.name, "SansS", tw - 10, 9.5)
            text(c, tx + tw / 2, ty + 9, game.name, "SansS", size, INK, "c")
            link(c, (tx, ty, tw, th), f"hub:{game.key}")


def _simple_header(c, title, kicker=None, nav=None):
    top_bar(c, nav or {"home": "home", "training": "training1"})
    y = BAR_Y - 40
    text(c, M, y, title, "SerifB", 27, INK)
    if kicker:
        text(c, W - M, y + 2, kicker, "SansM", 9, GREY, "r")
    line(c, M, y - 12, W - M, y - 12, 1.4, INK)
    return y - 12


def page_howto(c, ctx):
    y = _simple_header(c, "Zo werkt het", "Uitleg", {
        "home": "home", "training": "training1", "prev": "home", "next": "training1"})
    y -= 14
    items = [
        ("Tik met je vinger, schrijf met je pen",
         "Elke knop in dit boek is een link. Tik erop met je vinger om te "
         "bladeren; je pen laat alleen inkt achter. Zo navigeer je zonder "
         "per ongeluk te krabbelen."),
        ("Vier denkspieren, zestien spellen",
         "Getallen, Logica, Ruimte en Taal & Geheugen. Elk spel heeft een "
         "eigen pagina met de spelregels, een voorbeeld en 25 puzzels in "
         "drie niveaus: Opwarmen, Pittig en Meesterlijk."),
        ("Eén oplossing, nooit gokken",
         "Alle logische puzzels zijn door een computer nagerekend: er is "
         "altijd precies één oplossing en je kan ze vinden door te redeneren."),
        ("Oplossing bekijken",
         "Onderaan elke puzzel staat de knop Oplossing. De oplossingen "
         "staan helemaal achteraan, zodat je niets verklapt tijdens het bladeren."),
        ("Train 30 dagen",
         "Het dagplan geeft je elke dag vier puzzels, één per denkspier, en "
         "wordt geleidelijk moeilijker. Vink af wat je gedaan hebt. Tien "
         "minuten per dag is genoeg."),
        ("Opnieuw beginnen",
         "Je inkt staat los van het boek. Wis een pagina met de gum, of "
         "gebruik een nieuwe laag om een puzzel nog eens te maken."),
    ]
    for i, (head, body) in enumerate(items):
        circle(c, M + 11, y - 11, 11, fill=[RED, TEAL, MUSTARD, INK][i % 4],
               stroke=None)
        text_mid(c, M + 11, y - 11, str(i + 1), "SansB", 10.5,
                 INK if i % 4 == 2 else WHITE)
        text(c, M + 32, y - 15, head, "SansB", 11.5, INK)
        y = paragraph(c, M + 32, y - 20, W - 2 * M - 32, body, "Sans", 10,
                      leading=14.2) - 15
    # legend of the navigation buttons
    y -= 2
    rrect(c, M, y - 62, W - 2 * M, 62, 10, stroke=INK, lw=1.2)
    lx = M + 16
    for icon, label in ((icon_home, "Startscherm"), (icon_calendar, "Dagplan"),
                        (lambda c, x, yy, s: icon_chevron(c, x, yy, s, -1), "Vorige"),
                        (lambda c, x, yy, s: icon_chevron(c, x, yy, s, 1), "Volgende")):
        rrect(c, lx, y - 46, 36, 30, 15, stroke=INK, lw=1.2)
        icon(c, lx + 18, y - 31, 14)
        text(c, lx + 42, y - 34.5, label, "SansM", 9.5, INK)
        lx += 110
    button(c, W - M - 150, 16, 150, 34, "Naar het dagplan  ›", "training1",
           fill=INK, fg=WHITE)
    button(c, M, 16, 150, 34, "‹  Startscherm", "home")


def page_training(c, ctx, part):
    """part 0: days 1-15 (with banner), part 1: days 16-30."""
    key_other = "training2" if part == 0 else "training1"
    y = _simple_header(c, "30 dagen hersengym",
                       f"Dag {1 + part * 15}–{15 + part * 15}",
                       {"home": "home", "training": "training1",
                        "prev": "howto" if part == 0 else "training1",
                        "next": "training2" if part == 0 else "score"})
    if part == 0:
        image(c, "banner_training", M, y - 128, W - 2 * M, 122)
        y -= 132
        y = paragraph(c, M, y, W - 2 * M,
                      "Elke dag vier puzzels: één per denkspier. Tik op een "
                      "puzzel, los hem op en vink de dag af.", "Sans", 9.5) - 4
    else:
        y -= 10
    days = ctx["plan"][part * 15:(part + 1) * 15]
    row_h = min(33.0, (y - 62) / len(days))
    bh = row_h - 6
    x0 = M + 44
    bw = (W - M - 30 - x0 - 3 * 5) / 4
    for i, row in enumerate(days):
        d = part * 15 + i + 1
        ry = y - (i + 1) * row_h
        text(c, M, ry + bh / 2 - 3.4, "Dag", "SansM", 7.5, GREY)
        text(c, M + 19, ry + bh / 2 - 4.5, str(d), "SansB", 12.5, INK)
        for k, (game, idx) in enumerate(row):
            info = CATEGORIES[game.category]
            label = f"{game.name} {idx + 1}"
            button(c, x0 + k * (bw + 5), ry, bw, bh, label, f"p:{game.key}:{idx + 1}",
                   fill=info["color"], fg=info["on"], stroke=None, size=8.6,
                   font="SansS", r=7)
        checkbox(c, W - M - 20, ry + (bh - 20) / 2, 20)
    button(c, W - M - 150, 16, 150, 34,
           "Dag 16–30  ›" if part == 0 else "Scorebord  ›",
           key_other if part == 0 else "score", fill=INK, fg=WHITE)
    button(c, M, 16, 150, 34, "‹  Startscherm" if part == 0 else "‹  Dag 1–15",
           "home" if part == 0 else "training1")


def page_score(c, ctx):
    y = _simple_header(c, "Scorebord", "Vink af wat je oploste", {
        "home": "home", "training": "training1", "prev": "training2",
        "next": f"hub:{ctx['games'][0].key}"})
    label_w = 96
    n = 25
    cw = (W - 2 * M - label_w) / n
    y -= 30
    # column header: level groups
    a, b, _ = ctx["games"][0].counts
    for lvl, (start, cnt) in enumerate(((0, a), (a, b), (a + b, n - a - b))):
        cx = M + label_w + (start + cnt / 2) * cw
        text(c, cx, y + 12, LEVEL_NAMES[lvl], "SansM", 8, GREY, "c")
    row_h = min(31.0, (y - 64) / len(ctx["games"]))
    for gi, game in enumerate(ctx["games"]):
        info = CATEGORIES[game.category]
        ry = y - (gi + 1) * row_h
        if gi and ctx["games"][gi - 1].category != game.category:
            line(c, M, ry + row_h, W - M, ry + row_h, 0.8, INK)
        rrect(c, M, ry + (row_h - 12) / 2, 5, 12, 2.5, fill=info["color"], stroke=None)
        size = fit_size(game.name, "SansS", label_w - 14, 9.5)
        text(c, M + 10, ry + row_h / 2 - 3.3, game.name, "SansS", size, INK)
        link(c, (M, ry, label_w - 4, row_h), f"hub:{game.key}")
        total = sum(game.counts)
        for k in range(total):
            s = min(cw - 3.2, row_h - 12)
            bx = M + label_w + k * cw + (cw - s) / 2
            gap = 0
            rrect(c, bx + gap, ry + (row_h - s) / 2, s, s, 2, stroke=INK, lw=0.8)
        for cut in (game.counts[0], game.counts[0] + game.counts[1]):
            lx = M + label_w + cut * cw
            line(c, lx, ry + 4, lx, ry + row_h - 4, 0.5, MID)
    text(c, M, 28, "Tip: schrijf je tijd in het vakje bij de puzzel en verbeter jezelf.",
         "SerifI", 9.5, GREY)
    button(c, W - M - 150, 16, 150, 34, "Startscherm", "home")


def _example(c, game, puz, x, y, w, h):
    """Puzzle + solution shrunk side by side into box (x, y, w, h)."""
    bx, by, bw, bh = PLAY_BOX
    gap = 14
    scale = min((w - gap) / 2 / bw, (h - 14) / bh, 0.42)
    sw, sh = bw * scale, bh * scale
    x0 = x + (w - 2 * sw - gap) / 2
    for k, (label, solved) in enumerate((("Voorbeeld", False), ("Oplossing", True))):
        ox = x0 + k * (sw + gap)
        text(c, ox + sw / 2, y + h - 9, label.upper(), "SansB", 7.5, GREY, "c")
        c.saveState()
        c.translate(ox, y + (h - 14 - sh) / 2)
        c.scale(scale, scale)
        c.translate(-bx, -by)
        game.draw(c, PLAY_BOX, puz, solved=solved, part=0)
        c.restoreState()


def _teaser(c, game, puz, x, y, w, h):
    """One unsolved example puzzle, shrunk, to show what the game looks like."""
    bx, by, bw, bh = PLAY_BOX
    scale = min(w / bw, (h - 14) / bh, 0.5)
    sw, sh = bw * scale, bh * scale
    ox = x + (w - sw) / 2
    text(c, x + w / 2, y + h - 9, "ZO ZIET HET ERUIT", "SansB", 7.5, GREY, "c")
    oy = y + (h - 14 - sh) / 2
    rrect(c, ox - 6, oy - 6, sw + 12, sh + 12, 8, stroke=MID, lw=0.8)
    c.saveState()
    c.translate(ox, oy)
    c.scale(scale, scale)
    c.translate(-bx, -by)
    game.draw(c, PLAY_BOX, puz, solved=False, part=0)
    c.restoreState()


def page_hub(c, ctx, game):
    gi = ctx["games"].index(game)
    n_games = len(ctx["games"])
    prev_key = ctx["games"][gi - 1].key if gi else None
    next_key = ctx["games"][gi + 1].key if gi + 1 < n_games else None
    top_bar(c, {"home": "home", "training": "training1",
                "prev": f"hub:{prev_key}" if prev_key else "home",
                "next": f"hub:{next_key}" if next_key else "home"})
    info = CATEGORIES[game.category]
    y = BAR_Y - 44
    circle(c, M + 23, y + 10, 23, fill=info["color"], stroke=None)
    game.icon(c, M + 23, y + 10, 26, info["on"])
    size = fit_size(game.name, "SerifB", W - 2 * M - 180, 29)
    text(c, M + 58, y + 7, game.name, "SerifB", size, INK)
    text(c, M + 58, y - 8, game.tagline, "SerifI", 10.5, GREY)
    text(c, W - M, y + 22, info["name"].upper(), "SansB", 7.8, info["color"]
         if info["color"] != MUSTARD else INK, "r")
    line(c, M, y - 20, W - M, y - 20, 1.4, INK)
    y -= 30

    # index of puzzles at the bottom (fixed), text + example fill the rest
    counts = game.counts
    per_row = max(counts)
    gap = 6
    bw = (W - 2 * M - (per_row - 1) * gap) / per_row
    bh = 35
    group_h = 15 + bh + 9
    index_top = 24 + 3 * group_h
    n = 0
    for lvl in range(3):
        gy = index_top - lvl * group_h
        stars(c, M, gy - 7, lvl + 1, r=4.2, color=INK)
        text(c, M + 36, gy - 10, LEVEL_NAMES[lvl], "SansB", 9, INK)
        for k in range(counts[lvl]):
            n += 1
            button(c, M + k * (bw + gap), gy - 15 - bh, bw, bh, str(n),
                   f"p:{game.key}:{n}", size=13, font="SansB", r=8,
                   fill=info["color"] if lvl == 2 else None,
                   fg=info["on"] if lvl == 2 else INK,
                   stroke=INK if lvl < 2 or info["color"] != INK else INK,
                   lw=1.2 if lvl == 0 else 1.9)
    line(c, M, index_top + 8, W - M, index_top + 8, 0.8, INK)

    # rules and tips
    show_example = game.example and game.key not in NO_EXAMPLE
    text_w = W - 2 * M if show_example else W - 2 * M - 190
    text(c, M, y - 9, "SPELREGELS", "SansB", 8, GREY)
    y -= 15
    for rule in game.rules:
        circle(c, M + 3.5, y - 7.5, 2.2, fill=INK, stroke=None)
        y = paragraph(c, M + 13, y, text_w - 13, rule, "Sans", 10.2,
                      leading=13.8) - 6.5
    if game.tips:
        y -= 3
        text(c, M, y - 9, "SLIMME TIPS", "SansB", 8, GREY)
        y -= 15
        for tip in game.tips:
            icon_check(c, M + 4, y - 7, 7, info["color"]
                       if info["color"] != MUSTARD else INK, 1.6)
            y = paragraph(c, M + 13, y, text_w - 13, tip, "SerifI", 10.2,
                          leading=13.8) - 6.5
    if show_example:
        avail = y - (index_top + 16)
        if avail > 90:
            _example(c, game, ctx["examples"][game.key], M, index_top + 14,
                     W - 2 * M, avail)
    else:
        top_y = BAR_Y - 44 - 30
        image(c, f"cat_{game.category}", W - M - 178, top_y - 182, 178, 178)
        y = min(y, top_y - 186)
        avail = y - (index_top + 22)
        if avail > 110:
            _teaser(c, game, ctx["examples"][game.key], M, index_top + 16,
                    W - 2 * M, avail)


def page_solutions_intro(c, ctx):
    y = _simple_header(c, "Oplossingen", "Niet spieken!", {
        "home": "home", "training": "training1", "prev": "home", "next": "home"})
    y = paragraph(c, M, y - 12, W - 2 * M,
                  "Vanaf hier vind je alle oplossingen. Je komt er het snelst "
                  "via de knop Oplossing onderaan elke puzzel. Kies hieronder "
                  "een spel om naar de eerste oplossing te springen.",
                  "Sans", 10.5, leading=15) - 14
    cols = 2
    bw = (W - 2 * M - 12) / cols
    bh = 40
    for i, game in enumerate(ctx["games"]):
        info = CATEGORIES[game.category]
        bx = M + (i % cols) * (bw + 12)
        by = y - (i // cols + 1) * (bh + 9)
        rrect(c, bx, by, bw, bh, 9, stroke=INK, lw=1.2)
        circle(c, bx + 22, by + bh / 2, 13, fill=info["color"], stroke=None)
        game.icon(c, bx + 22, by + bh / 2, 15, info["on"])
        text(c, bx + 44, by + bh / 2 - 3.6, game.name, "SansS", 10.5, INK)
        link(c, (bx, by, bw, bh), f"s:{game.key}:1")
    button(c, W - M - 150, 16, 150, 34, "Startscherm", "home", fill=INK, fg=WHITE)


def page_colophon(c, ctx):
    y = _simple_header(c, "Colofon", f"Editie {ctx['seed']} · {theme.DEVICE['label']}", {
        "home": "home", "training": "training1", "prev": "home", "next": "home"})
    blocks = [
        ("Remarkable Mind",
         f"Versie {__version__}, editie {ctx['seed']}. {ctx['n_games']} spellen, "
         f"{ctx['n_puzzles']} puzzels, {DAYS} dagen training. Deze uitgave is "
         f"gemaakt voor de {theme.DEVICE['label']} ({theme.DEVICE['screen']}) "
         "en ook bruikbaar op andere e-paper tablets."),
        ("Puzzels",
         "Alle puzzels zijn procedureel gegenereerd. Elke logische puzzel is "
         "met een solver gecontroleerd op precies één oplossing. Met een "
         "ander editienummer bouw je een volledig nieuw boek."),
        ("Beeld",
         "De illustraties in risografie-stijl zijn gegenereerd met de "
         "beeldmodellen van ElevenLabs. De pictogrammen en puzzels zijn "
         "vectortekeningen, zodat ze haarscherp blijven op e-ink."),
        ("Letters",
         "Fraunces, Inter en Caveat, alle drie onder de SIL Open Font License."),
        ("Merken",
         "reMarkable is een merk van reMarkable AS. Dit is een onafhankelijk "
         "project, niet verbonden met of goedgekeurd door reMarkable AS."),
    ]
    y -= 16
    for head, body in blocks:
        text(c, M, y - 10, head, "SansB", 11, INK)
        y = paragraph(c, M, y - 14, W - 2 * M, body, "Sans", 10, leading=14.2) - 16
    image(c, "cat_getallen", M, 70, 100, 100)
    image(c, "cat_logica", M + 118, 70, 100, 100)
    image(c, "cat_ruimte", M + 236, 70, 100, 100)
    image(c, "cat_taal", M + 354, 70, 100, 100)
    button(c, W - M - 150, 16, 150, 34, "Startscherm", "home", fill=INK, fg=WHITE)


# --- assembly -------------------------------------------------------------------
def default_out(device):
    return ROOT / "dist" / f"RemarkableMind{theme.DEVICES[device]['suffix']}.pdf"


def build(seed=2026, out=None, jobs=4, cache=ROOT / "build" / "cache",
          log=print, strict=True, only=None, device="paperpro"):
    register_fonts()
    theme.set_device(device)
    out = out or default_out(device)
    t0 = time.time()
    all_games = games.all_games(strict and not only)
    if only:                                # dev builds: a subset of the games
        all_games = [g for g in all_games if g.key in only]
    puzzles = build_puzzles(seed, Path(cache), jobs, log, all_games)
    examples = {}
    for g in all_games:
        examples[g.key] = g.generate(random.Random(f"{seed}:{g.key}:example"), 1)
    plan = training_plan(all_games)
    in_plan = {}
    for d, row in enumerate(plan):
        for g, idx in row:
            in_plan[(g.key, idx)] = "training1" if d < 15 else "training2"
    ctx = {"seed": seed, "games": all_games, "puzzles": puzzles, "plan": plan,
           "examples": examples, "n_games": len(all_games),
           "n_puzzles": sum(len(v) for v in puzzles.values())}

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".raw.pdf")
    c = canvas.Canvas(str(raw), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{TITLE} – {SUBTITLE}")
    c.setAuthor("Remarkable Mind")
    c.setSubject(f"{ctx['n_games']} hersenspellen, {ctx['n_puzzles']} puzzels, "
                 f"offline voor de {theme.DEVICE['label']}")
    c.setCreator(f"remarkable_mind {__version__} (editie {seed})")

    keys = {}                                   # destination key -> page index

    def page(key, draw, *args, outline=None, level=0):
        keys[key] = len(keys)
        c.bookmarkPage(key, fit="Fit")
        if outline:
            c.addOutlineEntry(outline, key, level=level, closed=level == 0)
        draw(c, *args)
        c.showPage()

    page("cover", page_cover, ctx, outline=TITLE)
    page("home", page_home, ctx, outline="Startscherm")
    page("howto", page_howto, ctx, outline="Uitleg")
    page("training1", page_training, ctx, 0, outline="30 dagen hersengym")
    page("training2", page_training, ctx, 1)
    page("score", page_score, ctx, outline="Scorebord")

    last_cat = None
    for g in all_games:
        if g.category != last_cat:
            last_cat = g.category
            c.bookmarkPage(f"cat:{g.category}", fit="Fit")
            c.addOutlineEntry(CATEGORIES[g.category]["name"], f"cat:{g.category}",
                              level=0, closed=True)
        page(f"hub:{g.key}", page_hub, ctx, g, outline=g.name, level=1)
        total = len(puzzles[g.key])
        for i, puz in enumerate(puzzles[g.key]):
            n = i + 1
            base = f"p:{g.key}:{n}"
            for part in range(g.parts):
                key = base if part == 0 else f"{base}:{'abcdefgh'[part]}"
                nav = {
                    "home": "home", "hub": f"hub:{g.key}",
                    "training": in_plan.get((g.key, i), "training1"),
                    "prev": (f"p:{g.key}:{n - 1}" if n > 1 else f"hub:{g.key}")
                    if part == 0 else base,
                    "next": f"p:{g.key}:{n + 1}" if n < total else f"hub:{g.key}",
                    "continue": f"{base}:{'abcdefgh'[part + 1]}",
                    "solution": f"s:{g.key}:{n}",
                }
                page(key, lambda c, *a, **k: puzzle_page(c, *a, **k), g, puz, n,
                     level_of(g, i), total, part, nav)

    page("solutions", page_solutions_intro, ctx, outline="Oplossingen")
    for g in all_games:
        total = len(puzzles[g.key])
        for i, puz in enumerate(puzzles[g.key]):
            n = i + 1
            back = f"p:{g.key}:{n}" + (f":{'abcdefgh'[g.parts - 1]}" if g.parts > 1 else "")
            nxt = f"p:{g.key}:{n + 1}" if n < total else f"hub:{g.key}"
            nav = {"home": "home", "hub": f"hub:{g.key}",
                   "training": in_plan.get((g.key, i), "training1"),
                   "prev": back, "next": nxt, "back": back, "next_puzzle": nxt}
            page(f"s:{g.key}:{n}", lambda c, *a, **k: solution_page(c, *a, **k),
                 g, puz, n, level_of(g, i), total, nav,
                 outline=g.name if i == 0 else None, level=1)
    page("colophon", page_colophon, ctx, outline="Colofon")
    c.save()
    stats = finalize(raw, out)
    raw.unlink()
    out.with_suffix(".json").write_text(json.dumps(
        {"title": TITLE, "version": __version__, "seed": seed, "device": device,
         "pages": keys},
        indent=0))
    stats.update(seconds=round(time.time() - t0, 1), games=ctx["n_games"],
                 puzzles=ctx["n_puzzles"])
    log(f"{out}: {stats}")
    return stats


def finalize(raw, out):
    """Rewrite named links as explicit page links (most robust on e-readers),
    then compress. Returns basic statistics and fails on any dangling link."""
    import pymupdf
    doc = pymupdf.open(str(raw))
    n_links = 0
    for page in doc:
        for l in page.get_links():
            if l["kind"] not in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED):
                continue
            target = l.get("page", -1)
            if target is None or target < 0:
                raise RuntimeError(f"dangling link on page {page.number + 1}: {l}")
            page.delete_link(l)
            page.insert_link({"kind": pymupdf.LINK_GOTO, "from": l["from"],
                              "page": target, "to": pymupdf.Point(0, 0), "zoom": 0})
            n_links += 1
    doc.save(str(out), garbage=4, deflate=True, clean=True)
    pages = doc.page_count
    doc.close()
    return {"pages": pages, "links": n_links,
            "mb": round(Path(out).stat().st_size / 1e6, 2)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=2026, help="edition number")
    ap.add_argument("--device", choices=sorted(theme.DEVICES), default="paperpro",
                    help="paperpro = colour (default), rm2 = reMarkable 2, greyscale")
    ap.add_argument("--out", default=None,
                    help="default: dist/RemarkableMind[-rM2].pdf")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--dev", action="store_true",
                    help="skip games that are missing or broken")
    ap.add_argument("--only", default="", help="comma separated game keys (dev)")
    a = ap.parse_args(argv)
    build(a.seed, Path(a.out) if a.out else None, a.jobs,
          strict=not (a.dev or a.only),
          only=set(a.only.split(",")) if a.only else None, device=a.device)


if __name__ == "__main__":
    sys.exit(main())
