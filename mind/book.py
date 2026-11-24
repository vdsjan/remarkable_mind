"""Assemble a Remarkable Mind book.

    python -m mind.book --seed 2026                    # Paper Pro, colour
    python -m mind.book --seed 2026 --device rm2       # reMarkable 2, greyscale
    python -m mind.book --seed 2026 --device move      # Paper Pro Move, 9:16
    python -m mind.book --games sudoku:10,doolhof:6 --difficulty 2 --no-plan

The "app" is one PDF: every button is an internal link, so it runs on a
stock reMarkable without developer mode and without any network. The same
code runs in a browser through Pyodide (see web/): there it builds the book
sequentially, without PyMuPDF and without worker processes.
"""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

from reportlab.pdfgen import canvas

from . import __version__, games, theme
from .draw import (button, checkbox, circle, fit_size, icon_calendar,
                   icon_check, icon_chevron, icon_home, line, link, paragraph,
                   rrect, stars, text, text_mid, wrap)
# Geometry names below are rebound by theme.set_device() for each device.
from .pages import BAR_H, BAR_Y, LEFT_SAFE, puzzle_page, solution_page, top_bar
from .theme import (ASSET_DIR, CATEGORIES, CATEGORY_ORDER, COMPACT, GREY, H,
                    INK, LEVEL_NAMES, M, MID, MUSTARD, PLAY_BOX, RED, TEAL, W,
                    WHITE, register_fonts)

ROOT = Path(__file__).resolve().parents[1]
TITLE = "Remarkable Mind"
SUBTITLE = "Hersengym op papier"
DAYS = 30                       # longest day plan
MAX_PER_GAME = 30
DIFFICULTIES = {"mix": "Oplopend", "1": "Opwarmen", "2": "Pittig",
                "3": "Meesterlijk"}
# Games whose puzzles are too text-heavy to shrink into a hub-page example.
NO_EXAMPLE = {"geheugen", "woordzoeker", "logigram", "codekraker",
              "letterchaos", "reeksen", "woordladder", "plaatsdelict", "vouwcode"}


# --- what goes into the book ----------------------------------------------------
def levels_for(n, difficulty="mix"):
    """Levels (1..3) of n puzzles. "mix" rises like the standard book
    (9/8/8 for 25 puzzles); "1", "2" or "3" uses one level throughout."""
    if str(difficulty) in ("1", "2", "3"):
        return [int(difficulty)] * n
    a, b = round(n * 9 / 25), round(n * 17 / 25)
    return [1] * a + [2] * (b - a) + [3] * (n - b)


class Selection:
    """Which games, how many puzzles each, and which extras.

    counts: {game key: number of puzzles}; games left out or set to 0 are
    skipped. Order follows the home screen. The default is the full book:
    every game with 25 puzzles, rising difficulty, day plan and solutions."""

    def __init__(self, counts=None, difficulty="mix", plan=True, solutions=True):
        if counts is None:
            counts = {k: 25 for k in games.ORDER}
        unknown = set(counts) - set(games.ORDER)
        if unknown:
            raise ValueError(f"unknown games: {', '.join(sorted(unknown))}")
        if str(difficulty) not in DIFFICULTIES:
            raise ValueError(f"unknown difficulty: {difficulty}")
        self.counts = {k: max(0, min(MAX_PER_GAME, int(counts[k])))
                       for k in games.ORDER if k in counts and int(counts[k]) > 0}
        if not self.counts:
            raise ValueError("choose at least one game")
        self.difficulty = str(difficulty)
        self.plan = bool(plan)
        self.solutions = bool(solutions)

    @property
    def levels(self):
        return {k: levels_for(n, self.difficulty) for k, n in self.counts.items()}

    @classmethod
    def parse(cls, spec, **kw):
        """"sudoku:10,doolhof:6" -> Selection."""
        counts = {}
        for part in filter(None, (p.strip() for p in spec.split(","))):
            key, _, n = part.partition(":")
            counts[key.strip()] = int(n or 25)
        return cls(counts, **kw)


def level_of(game, i, levels=None):
    """Level (1..3) of the i-th puzzle (0-based) of a game."""
    levels = levels or levels_for(sum(game.counts))
    return levels[i]


# --- puzzle generation --------------------------------------------------------
def generate_game(key, seed, levels, progress=None):
    """All puzzles of one game. Never prints the same puzzle twice, and avoids
    repeating a theme, proverb or picture while fresh material is available."""
    game = games.get(key)
    out, seen = [], set()
    for i, level in enumerate(levels):
        salt = 0
        while True:
            rng = random.Random(f"{seed}:{key}:{i}:{salt}")
            puz = game.generate(rng, level)
            sig = json.dumps(puz, sort_keys=True)
            marks = set(game.fingerprints(puz))
            if sig not in seen and (not marks & seen or salt >= 400):
                break
            salt += 1
            if salt > 800:
                raise RuntimeError(f"{key}: cannot generate a new puzzle {i + 1}")
        seen.add(sig)
        seen |= marks
        out.append(puz)
        if progress:
            progress(key, i + 1, len(levels))
    return out


def _generate_game(args):
    key, seed, levels, device = args
    theme.set_device(device)                # worker processes start in colour
    return key, generate_game(key, seed, levels)


def _variant():
    """Cache suffix: a few games generate differently per device."""
    return ("-mono" if theme.MONO else "") + ("-move" if theme.COMPACT else "")


def build_puzzles(seed, cache_dir, jobs=4, log=print, all_games=None,
                  levels=None, progress=None):
    """Generate (or load from cache) all puzzles: {key: [puzzle, ...]}.

    levels: {key: [level, ...]}; default 25 rising puzzles per game.
    cache_dir None disables the cache; jobs <= 1 generates in-process."""
    all_games = all_games or games.all_games()
    levels = levels or {g.key: levels_for(sum(g.counts)) for g in all_games}
    result, todo = {}, []
    for game in all_games:
        lv = levels[game.key]
        path = None
        if cache_dir is not None:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            src = Path(sys.modules[type(game).__module__].__file__).read_bytes()
            extra = b"" if lv == levels_for(25) else json.dumps(lv).encode()
            tag = hashlib.sha1(src + str(game.counts).encode() + extra).hexdigest()[:10]
            path = Path(cache_dir) / f"{seed}-{game.key}-{tag}{_variant()}.json"
            if path.exists():
                result[game.key] = json.loads(path.read_text())
                if progress:
                    progress(game.key, len(lv), len(lv))
                continue
        todo.append((game.key, path))
    if todo:
        log(f"generating {len(todo)} games ...")
        if jobs <= 1 or len(todo) == 1:
            done = ((k, generate_game(k, seed, levels[k], progress)) for k, _ in todo)
        else:
            from concurrent.futures import ProcessPoolExecutor
            pool = ProcessPoolExecutor(max_workers=jobs)
            done = pool.map(_generate_game, [(k, seed, levels[k], theme.device_key())
                                             for k, _ in todo])
        paths = dict(todo)
        for key, puzzles in done:
            if paths[key] is not None:
                paths[key].write_text(json.dumps(puzzles))
            result[key] = puzzles
            log(f"  {key}: {len(puzzles)} puzzles")
            if progress and not (jobs <= 1 or len(todo) == 1):
                progress(key, len(puzzles), len(puzzles))
    return result


# --- the day plan -----------------------------------------------------------------
def training_plan(all_games, levels=None, days=DAYS):
    """Up to `days` days, one puzzle per category each day, rising difficulty.

    Returns a list of days; each day is a list of (game, puzzle_index0). The
    plan gets shorter when there are too few puzzles to never repeat one."""
    n_of = {g.key: len(levels[g.key]) if levels else sum(g.counts) for g in all_games}
    by_cat = {cat: [g for g in all_games if g.category == cat and n_of[g.key]]
              for cat in CATEGORY_ORDER}
    cats = [cat for cat in CATEGORY_ORDER if by_cat[cat]]
    if not cats:
        return []

    def fits(d):
        return all(n_of[g.key] >= -(-d // len(by_cat[cat]))
                   for cat in cats for g in by_cat[cat][:min(d, len(by_cat[cat]))])

    while days > 0 and not fits(days):
        days -= 1
    used = {g.key: 0 for g in all_games}
    plan = []
    for day in range(days):
        row = []
        for cat in cats:
            cat_games = by_cat[cat]
            game = cat_games[day % len(cat_games)]
            n = n_of[game.key]
            visits = -(-days // len(cat_games))          # ceil
            idx = round(used[game.key] * (n - 1) / max(1, visits - 1))
            used[game.key] += 1
            row.append((game, min(idx, n - 1)))
        plan.append(row)
    return plan


# --- small layout helpers -------------------------------------------------------------
def asset(name):
    """Artwork for the current device (greyscale version on mono screens)."""
    return str(ASSET_DIR / f"{name}{'_grey' if theme.MONO else ''}.jpg")


def image(c, name, x, y, w, h):
    c.drawImage(asset(name), x, y, w, h, preserveAspectRatio=True, anchor="c")


def para_height(s, width, font, size, leading=None):
    leading = leading or size * 1.38
    n = max(1, len(wrap(s, font, size, width)))
    return size * 1.35 + (n - 1) * leading


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


def _accent(info):
    """Category colour for small text and icons (mustard is too light)."""
    return info["color"] if info["color"] is not MUSTARD else INK


def _bottom_buttons(c, left=None, right=None):
    """(label, dest, filled) pairs, sized for the device."""
    bh = 30 if COMPACT else 34
    bw = min(150, (W - 2 * M - 10) / 2)
    y = 14 if COMPACT else 16
    size = 9.5 if COMPACT else 10.5
    for spec, x in ((left, M), (right, W - M - bw)):
        if spec:
            label, dest, filled = spec
            button(c, x, y, bw, bh, label, dest, size=size,
                   fill=INK if filled else None, fg=WHITE if filled else INK)


def _simple_header(c, title, kicker=None, nav=None):
    top_bar(c, nav or {"home": "home"})
    y = BAR_Y - (36 if COMPACT else 40)
    size = fit_size(title, "SerifB", W - 2 * M - (70 if kicker else 0),
                    22 if COMPACT else 27)
    text(c, M, y, title, "SerifB", size, INK)
    if kicker:
        text(c, W - M, y + 2, kicker, "SansM", 8 if COMPACT else 9, GREY, "r")
    line(c, M, y - 12, W - M, y - 12, 1.4, INK)
    return y - 12


# --- pages --------------------------------------------------------------------------------
def page_cover(c, ctx):
    img_h = min(H, W * 4 / 3)                    # the artwork is 3:4
    c.drawImage(asset("cover"), 0, 0, W, img_h)
    k = W / 510
    title = fit_size(TITLE, "SerifX", W - 2 * M, 47)
    y = H - (92 if not COMPACT else 64)
    text(c, W / 2, y, TITLE, "SerifX", title, INK, "c")
    text(c, W / 2, y - 30 * k - 4, SUBTITLE.upper(), "SansB", 12.5 * max(k, 0.8), RED, "c")
    info = (f"{plural(ctx['n_games'], 'spel', 'spellen')}  ·  "
            f"{ctx['n_puzzles']} puzzels  ·  100% offline")
    text(c, W / 2, y - 54 * k - 6, info, "SansM", fit_size(info, "SansM", W - 2 * M, 10),
         INK, "c")
    bw, bh = (190, 40) if not COMPACT else (170, 34)
    button(c, (W - bw) / 2, 30 if not COMPACT else 22, bw, bh, "Tik om te starten  ›",
           "home", fill=INK, fg=WHITE, size=12.5 if not COMPACT else 11)
    link(c, (0, 0, W, H), "home")


def page_home(c, ctx):
    shortcuts = ([("Dagplan", "training1", True)] if ctx["plan"] else [])
    shortcuts += [("Scorebord", "score", not ctx["plan"]), ("Uitleg", "howto", False)]
    if COMPACT:
        text(c, M, H - 44, TITLE, "SerifX", fit_size(TITLE, "SerifX", W - 2 * M, 22), INK)
        text(c, M + 1, H - 57, SUBTITLE.upper(), "SansB", 7.2, RED)
        gap = 6
        bw = (W - 2 * M - gap * (len(shortcuts) - 1)) / len(shortcuts)
        x = M
        for label, dest, filled in shortcuts:
            button(c, x, H - 96, bw, 28, label, dest, fill=INK if filled else None,
                   fg=WHITE if filled else INK, size=9.5)
            x += bw + gap
        line(c, M, H - 106, W - M, H - 106, 1.4, INK)
        top = H - 116
    else:
        text(c, M, H - 62, TITLE, "SerifX", 22, INK)
        text(c, M + 1, H - 76, SUBTITLE.upper(), "SansB", 7.6, RED)
        bw, bh, gap = 72, 30, 6
        x = W - M - len(shortcuts) * bw - (len(shortcuts) - 1) * gap
        for label, dest, filled in shortcuts:
            button(c, x, H - 72, bw, bh, label, dest, fill=INK if filled else None,
                   fg=WHITE if filled else INK, size=9.5)
            x += bw + gap
        line(c, M, H - 90, W - M, H - 90, 1.4, INK)
        top = H - 102

    groups = [(cat, [g for g in ctx["games"] if g.category == cat]) for cat in CATEGORY_ORDER]
    groups = [(cat, gs) for cat, gs in groups if gs]
    most = max(len(gs) for _, gs in groups)
    # up to 4 games per category: a row of 4 (2 on the Move); more: rows of 3
    cols = (2 if most <= 4 else 3) if COMPACT else (4 if most <= 4 else 3)
    gap = 8 if COMPACT else 9
    head_h, after = 24, 12
    rows = sum(math.ceil(len(gs) / cols) for _, gs in groups)
    avail = top - 26 - len(groups) * (head_h + after) - (rows - len(groups)) * gap
    th = min(52 if COMPACT else (120 if cols == 4 else 54), avail / rows)
    tw = (W - 2 * M - (cols - 1) * gap) / cols
    y0 = top
    for cat, gs in groups:
        info = CATEGORIES[cat]
        pill_w = 20 + c.stringWidth(info["name"], "SansB", 9.5)
        rrect(c, M, y0 - 18, pill_w, 18, 9, fill=info["color"], stroke=None)
        text_mid(c, M + pill_w / 2, y0 - 9, info["name"], "SansB", 9.5, info["on"])
        if pill_w + 8 + c.stringWidth(info["blurb"], "Sans", 9) < W - 2 * M:
            text(c, M + pill_w + 8, y0 - 12.5, info["blurb"], "Sans", 9, GREY)
        y = y0 - head_h
        for gi, game in enumerate(gs):
            r, col = divmod(gi, cols)
            tx, ty = M + col * (tw + gap), y - (r + 1) * th - r * gap
            _tile(c, game, info, tx, ty, tw, th)
        n_rows = math.ceil(len(gs) / cols)
        y0 = y - n_rows * th - (n_rows - 1) * gap - after


def _tile(c, game, info, tx, ty, tw, th):
    c.saveState()
    p = c.beginPath()
    p.roundRect(tx, ty, tw, th, 9)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(info["color"])
    flat = COMPACT or th < 70                    # horizontal tile, colour on the left
    if flat:
        c.rect(tx, ty, 7, th, stroke=0, fill=1)
    else:
        c.rect(tx, ty + th - 7, tw, 7, stroke=0, fill=1)
    c.restoreState()
    rrect(c, tx, ty, tw, th, 9, stroke=INK, lw=1.3)
    if flat and tw < 110:                        # narrow tile: the name only
        size = fit_size(game.name, "SansS", tw - 17, 9.5)
        text(c, tx + 7 + (tw - 7) / 2, ty + th / 2 - size * 0.35, game.name, "SansS",
             size, INK, "c")
    elif flat:
        s = min(26, th * 0.55)
        game.icon(c, tx + 12 + s / 2 + 4, ty + th / 2, s, INK)
        x = tx + 12 + s + 12
        size = fit_size(game.name, "SansS", tx + tw - 6 - x, 10.5)
        text(c, x, ty + th / 2 - size * 0.35, game.name, "SansS", size, INK)
    else:
        game.icon(c, tx + tw / 2, ty + th / 2 + 6, min(40, th * 0.45), INK)
        size = fit_size(game.name, "SansS", tw - 10, 9.5)
        text(c, tx + tw / 2, ty + 9, game.name, "SansS", size, INK, "c")
    link(c, (tx, ty, tw, th), f"hub:{game.key}")


def _howto_items(ctx):
    n_games, n_puz = ctx["n_games"], ctx["n_puzzles"]
    cats = len({g.category for g in ctx["games"]})
    diff = ctx["selection"].difficulty
    lv = ("in drie niveaus: Opwarmen, Pittig en Meesterlijk" if diff == "mix"
          else f"op niveau {DIFFICULTIES[diff]}")
    items = [
        ("Tik met je vinger, schrijf met je pen",
         "Elke knop in dit boek is een link. Tik erop met je vinger om te "
         "bladeren; je pen laat alleen inkt achter. Zo navigeer je zonder "
         "per ongeluk te krabbelen."),
        (f"{plural(cats, 'denkspier', 'denkspieren')}, {plural(n_games, 'spel', 'spellen')}",
         f"Elk spel heeft een eigen pagina met de spelregels en een "
         f"overzicht van zijn puzzels. Samen zijn het er {n_puz}, {lv}."),
        ("Eén oplossing, nooit gokken",
         "Alle logische puzzels zijn door een computer nagerekend: er is "
         "altijd precies één oplossing en je kan ze vinden door te redeneren."),
    ]
    if ctx["selection"].solutions:
        items.append(("Oplossing bekijken",
                      "Onderaan elke puzzel staat de knop Oplossing. De oplossingen "
                      "staan helemaal achteraan, zodat je niets verklapt tijdens het "
                      "bladeren."))
    if ctx["plan"]:
        items.append((f"Train {len(ctx['plan'])} dagen",
                      f"Het dagplan geeft je elke dag "
                      f"{plural(len(ctx['plan'][0]), 'puzzel', 'puzzels')}, één per "
                      "denkspier, en wordt geleidelijk moeilijker. Vink af wat je "
                      "gedaan hebt."))
    items.append(("Opnieuw beginnen",
                  "Je inkt staat los van het boek. Wis een pagina met de gum, of "
                  "gebruik een nieuwe laag om een puzzel nog eens te maken."))
    return items


def _howto_metrics():
    size, lead = (9, 12.4) if COMPACT else (10, 14.2)
    return size, lead, W - 2 * M - 32


def howto_pages(ctx):
    """Split the explanation over as many pages as the device needs."""
    size, lead, width = _howto_metrics()
    legend_h = 100 if COMPACT else 64
    top = BAR_Y - (36 if COMPACT else 40) - 12 - 14
    bottom = (14 + 30 + 12) if COMPACT else (16 + 34 + 14)
    pages, cur, y = [], [], top
    items = _howto_items(ctx)
    for i, (head, body) in enumerate(items):
        h = 20 + para_height(body, width, "Sans", size, lead) + 15
        last = i == len(items) - 1
        need = h + (legend_h if last else 0)
        if cur and y - need < bottom:
            pages.append(cur)
            cur, y = [], top
        cur.append(i)
        y -= h
    pages.append(cur)
    return pages


def page_howto(c, ctx, part):
    pages = ctx["howto_pages"]
    nxt = f"howto{part + 2}" if part + 1 < len(pages) else ctx["after_howto"]
    y = _simple_header(c, "Zo werkt het",
                       "Uitleg" if len(pages) == 1 else f"Uitleg {part + 1}/{len(pages)}",
                       {"home": "home", "training": ctx["nav_training"],
                        "prev": "home" if part == 0 else ("howto" if part == 1 else f"howto{part}"),
                        "next": nxt})
    y -= 14
    size, lead, width = _howto_metrics()
    items = _howto_items(ctx)
    for i in pages[part]:
        head, body = items[i]
        circle(c, M + 11, y - 11, 11, fill=[RED, TEAL, MUSTARD, INK][i % 4], stroke=None)
        text_mid(c, M + 11, y - 11, str(i + 1), "SansB", 10.5, INK if i % 4 == 2 else WHITE)
        text(c, M + 32, y - 15, head, "SansB", fit_size(head, "SansB", width, 11.5), INK)
        y = paragraph(c, M + 32, y - 20, width, body, "Sans", size, leading=lead) - 15
    if part == len(pages) - 1:
        _nav_legend(c, y - 2, ctx)
    after_label = "Naar het dagplan  ›" if ctx["plan"] else "Scorebord  ›"
    _bottom_buttons(c, ("‹  Startscherm", "home", False),
                    ("Verder  ›", nxt, True) if nxt.startswith("howto")
                    else (after_label, nxt, True))


def _nav_legend(c, y, ctx):
    entries = [(icon_home, "Startscherm")]
    if ctx["plan"]:
        entries.append((icon_calendar, "Dagplan"))
    entries += [(lambda c, x, yy, s: icon_chevron(c, x, yy, s, -1), "Vorige"),
                (lambda c, x, yy, s: icon_chevron(c, x, yy, s, 1), "Volgende")]
    cols = 2 if COMPACT else len(entries)
    rows = math.ceil(len(entries) / cols)
    box_h = 20 + rows * 36
    rrect(c, M, y - box_h, W - 2 * M, box_h, 10, stroke=INK, lw=1.2)
    cw = (W - 2 * M - 16) / cols
    for i, (icon, label) in enumerate(entries):
        r, col = divmod(i, cols)
        lx = M + 12 + col * cw
        by = y - 16 - (r + 1) * 36 + 6
        rrect(c, lx, by, 36, 30, 15, stroke=INK, lw=1.2)
        icon(c, lx + 18, by + 15, 14)
        text(c, lx + 42, by + 11.5, label, "SansM", 9.5, INK)


def _training_geometry(first):
    """(y of the first row's top, row height) for a day-plan page."""
    y = BAR_Y - (36 if COMPACT else 40) - 12
    if first:
        bh = (W - 2 * M) / 2 if COMPACT else 122
        y -= bh + (10 if COMPACT else 10)
        y -= para_height("Elke dag één puzzel per denkspier. Tik op een puzzel, los "
                         "hem op en vink de dag af.", W - 2 * M, "Sans", 9.5) + 8
    else:
        y -= 10
    return y, (48 if COMPACT else 33)


def training_pages(plan):
    pages, start = [], 0
    while start < len(plan):
        y, row_h = _training_geometry(not pages)
        bottom = 62 if not COMPACT else 54
        # wide pages always take 15 days and squeeze the rows when needed
        cap = 15 if not COMPACT else max(1, int((y - bottom) / row_h))
        pages.append((start, min(len(plan), start + cap)))
        start = pages[-1][1]
    return pages


def page_training(c, ctx, part):
    pages = ctx["plan_pages"]
    start, end = pages[part]
    n = len(ctx["plan"])
    prev = ctx["howto_last"] if part == 0 else f"training{part}"
    nxt = f"training{part + 2}" if part + 1 < len(pages) else "score"
    y = _simple_header(c, f"{n} dagen hersengym", f"Dag {start + 1}–{end}",
                       {"home": "home", "training": "training1", "prev": prev, "next": nxt})
    y_rows, row_h = _training_geometry(part == 0)
    if not COMPACT:
        row_h = min(row_h, (y_rows - 62) / (end - start))
    if part == 0:
        bh = (W - 2 * M) / 2 if COMPACT else 122
        image(c, "banner_training", M, y - bh - 6, W - 2 * M, bh)
        paragraph(c, M, y - bh - 10, W - 2 * M,
                  "Elke dag één puzzel per denkspier. Tik op een puzzel, los "
                  "hem op en vink de dag af.", "Sans", 9.5)
    k = len(ctx["plan"][0])
    for i, row in enumerate(ctx["plan"][start:end]):
        d = start + i + 1
        ry = y_rows - (i + 1) * row_h
        if COMPACT:
            bh = (row_h - 10) / 2
            text(c, M, ry + row_h / 2 + 1, "Dag", "SansM", 7, GREY)
            text(c, M, ry + row_h / 2 - 11, str(d), "SansB", 12, INK)
            x0 = M + 28
            cols = 2 if k > 1 else 1
            bw = (W - M - 26 - x0 - (cols - 1) * 5) / cols
            for j, (game, idx) in enumerate(row):
                r, col = divmod(j, cols)
                info = CATEGORIES[game.category]
                label = f"{game.name} {idx + 1}"
                button(c, x0 + col * (bw + 5), ry + 5 + (1 - r) * (bh + 4) - (0 if k > 2 else -bh / 2 - 2),
                       bw, bh, label, f"p:{game.key}:{idx + 1}", fill=info["color"],
                       fg=info["on"], stroke=None, size=8.2, font="SansS", r=6)
            checkbox(c, W - M - 18, ry + (row_h - 18) / 2, 18)
        else:
            bh = row_h - 6
            text(c, M, ry + bh / 2 - 3.4, "Dag", "SansM", 7.5, GREY)
            text(c, M + 19, ry + bh / 2 - 4.5, str(d), "SansB", 12.5, INK)
            x0 = M + 44
            bw = (W - M - 30 - x0 - (k - 1) * 5) / k
            for j, (game, idx) in enumerate(row):
                info = CATEGORIES[game.category]
                label = f"{game.name} {idx + 1}"
                button(c, x0 + j * (bw + 5), ry, bw, bh, label, f"p:{game.key}:{idx + 1}",
                       fill=info["color"], fg=info["on"], stroke=None, size=8.6,
                       font="SansS", r=7)
            checkbox(c, W - M - 20, ry + (bh - 20) / 2, 20)
    left = (("‹  Startscherm", "home", False) if part == 0
            else (f"‹  Dag {pages[part - 1][0] + 1}–{pages[part - 1][1]}", prev, False))
    right = ((f"Dag {pages[part + 1][0] + 1}–{pages[part + 1][1]}  ›", nxt, True)
             if part + 1 < len(pages) else ("Scorebord  ›", "score", True))
    _bottom_buttons(c, left, right)


def score_pages(ctx):
    """Compact screens get one block per game (name above wrapped boxes);
    wide screens show one row per game on a single page."""
    if not COMPACT:
        n = len(ctx["games"])
        if n <= 16:
            return [list(range(n))]
        pages, cur = [], []
        for gi, game in enumerate(ctx["games"]):
            new_cat = gi and ctx["games"][gi - 1].category != game.category
            if cur and (len(cur) >= 14 or (new_cat and len(cur) >= 8)):
                pages.append(cur)
                cur = []
            cur.append(gi)
        pages.append(cur)
        return pages
    top = BAR_Y - 36 - 12 - 14
    bottom = 14 + 30 + 30
    per_row = int((W - 2 * M + 3) / 17)
    pages, cur, y = [], [], top
    for gi, game in enumerate(ctx["games"]):
        n = len(ctx["puzzles"][game.key])
        h = 16 + math.ceil(n / per_row) * 17 + 8
        if cur and y - h < bottom:
            pages.append(cur)
            cur, y = [], top
        cur.append(gi)
        y -= h
    pages.append(cur)
    return pages


def page_score(c, ctx, part):
    pages = ctx["score_pages"]
    key = lambda p: "score" if p == 0 else f"score{p + 1}"
    prev = (f"training{len(ctx['plan_pages'])}" if ctx["plan"] else ctx["howto_last"]) \
        if part == 0 else key(part - 1)
    nxt = key(part + 1) if part + 1 < len(pages) else f"hub:{ctx['games'][0].key}"
    kicker = "Vink af wat je oploste" if len(pages) == 1 else f"{part + 1}/{len(pages)}"
    y = _simple_header(c, "Scorebord", kicker, {
        "home": "home", "training": ctx["nav_training"], "prev": prev, "next": nxt})
    gs = [ctx["games"][i] for i in pages[part]]
    if COMPACT:
        y -= 14
        per_row = int((W - 2 * M + 3) / 17)
        for game in gs:
            info = CATEGORIES[game.category]
            lv = ctx["levels"][game.key]
            rrect(c, M, y - 12, 5, 12, 2.5, fill=info["color"], stroke=None)
            text(c, M + 10, y - 10, game.name, "SansS", 9.5, INK)
            link(c, (M, y - 14, W - 2 * M, 16), f"hub:{game.key}")
            y -= 16
            for k in range(len(lv)):
                r, col = divmod(k, per_row)
                rrect(c, M + col * 17, y - (r + 1) * 17 + 3, 14, 14, 2, stroke=INK,
                      lw=1.6 if lv[k] == 3 else 0.8)
            y -= math.ceil(len(lv) / per_row) * 17 + 8
        text(c, M, 54, "Dikke vakjes: niveau Meesterlijk.", "SerifI", 8.5, GREY)
    else:
        label_w = 96
        n = max(len(ctx["levels"][g.key]) for g in gs)
        cw = (W - 2 * M - label_w) / max(n, 25)
        y -= 30
        lvs = [ctx["levels"][g.key] for g in gs]
        if all(lv == lvs[0] for lv in lvs) and len(set(lvs[0])) > 1:
            lv = lvs[0]
            for level in sorted(set(lv)):
                idx = [i for i, v in enumerate(lv) if v == level]
                cx = M + label_w + (idx[0] + len(idx) / 2) * cw
                text(c, cx, y + 12, LEVEL_NAMES[level - 1], "SansM", 8, GREY, "c")
        row_h = min(31.0, (y - 64) / len(gs))
        for gi, game in enumerate(gs):
            info = CATEGORIES[game.category]
            lv = ctx["levels"][game.key]
            ry = y - (gi + 1) * row_h
            if gi and gs[gi - 1].category != game.category:
                line(c, M, ry + row_h, W - M, ry + row_h, 0.8, INK)
            rrect(c, M, ry + (row_h - 12) / 2, 5, 12, 2.5, fill=info["color"], stroke=None)
            size = fit_size(game.name, "SansS", label_w - 14, 9.5)
            text(c, M + 10, ry + row_h / 2 - 3.3, game.name, "SansS", size, INK)
            link(c, (M, ry, label_w - 4, row_h), f"hub:{game.key}")
            s = min(cw - 3.2, row_h - 12)
            for k in range(len(lv)):
                bx = M + label_w + k * cw + (cw - s) / 2
                rrect(c, bx, ry + (row_h - s) / 2, s, s, 2, stroke=INK, lw=0.8)
                if k and lv[k] != lv[k - 1]:
                    lx = M + label_w + k * cw
                    line(c, lx, ry + 4, lx, ry + row_h - 4, 0.5, MID)
        if len(pages) == 1:                 # with more pages the buttons need the room
            text(c, M, 28, "Tip: schrijf je tijd in het vakje bij de puzzel en verbeter "
                 "jezelf.", "SerifI", 9.5, GREY)
    if part + 1 < len(pages):
        _bottom_buttons(c, ("Startscherm", "home", False), ("Verder  ›", nxt, True))
    else:
        _bottom_buttons(c, None, ("Startscherm", "home", False))


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


def _groups(levels):
    """Consecutive runs of equal level: [(level, [puzzle numbers 1-based])]."""
    out = []
    for i, lv in enumerate(levels):
        if out and out[-1][0] == lv:
            out[-1][1].append(i + 1)
        else:
            out.append((lv, [i + 1]))
    return out


def page_hub(c, ctx, game):
    gi = ctx["games"].index(game)
    n_games = len(ctx["games"])
    prev_key = ctx["games"][gi - 1].key if gi else None
    next_key = ctx["games"][gi + 1].key if gi + 1 < n_games else None
    top_bar(c, {"home": "home", "training": ctx["nav_training"],
                "prev": f"hub:{prev_key}" if prev_key else "home",
                "next": f"hub:{next_key}" if next_key else "home"})
    info = CATEGORIES[game.category]
    r = 18 if COMPACT else 23
    y = BAR_Y - (38 if COMPACT else 44)
    circle(c, M + r, y + 10, r, fill=info["color"], stroke=None)
    game.icon(c, M + r, y + 10, r * 1.13, info["on"])
    tx = M + 2 * r + 12
    size = fit_size(game.name, "SerifB", W - M - tx - (0 if COMPACT else 70), 23 if COMPACT else 29)
    text(c, tx, y + 7, game.name, "SerifB", size, INK)
    tsize = fit_size(game.tagline, "SerifI", W - M - tx, 10.5, min_size=8)
    text(c, tx, y - 8, game.tagline, "SerifI", tsize, GREY)
    if not COMPACT:
        text(c, W - M, y + 22, info["name"].upper(), "SansB", 7.8, _accent(info), "r")
    line(c, M, y - 20, W - M, y - 20, 1.4, INK)
    y -= 30

    # index of puzzles at the bottom, text + example fill the rest
    levels = ctx["levels"][game.key]
    groups = _groups(levels)
    gap = 5 if COMPACT else 6
    per_row = min(max(len(nums) for _, nums in groups), 6 if COMPACT else 9)
    bw = (W - 2 * M - (per_row - 1) * gap) / per_row
    bh = 30 if COMPACT else 35
    heights = [15 + math.ceil(len(nums) / per_row) * (bh + gap) + 3 for _, nums in groups]
    index_top = 18 + sum(heights)
    gy = index_top
    for (lvl, nums), gh in zip(groups, heights):
        stars(c, M, gy - 7, lvl, r=4.2, color=INK)
        text(c, M + 36, gy - 10, LEVEL_NAMES[lvl - 1], "SansB", 9, INK)
        for k, n in enumerate(nums):
            row, col = divmod(k, per_row)
            button(c, M + col * (bw + gap), gy - 15 - (row + 1) * (bh + gap) + gap, bw, bh,
                   str(n), f"p:{game.key}:{n}", size=12 if COMPACT else 13, font="SansB",
                   r=8, fill=info["color"] if lvl == 3 else None,
                   fg=info["on"] if lvl == 3 else INK, stroke=INK,
                   lw=1.2 if lvl == 1 else 1.9)
        gy -= gh
    line(c, M, index_top + 8, W - M, index_top + 8, 0.8, INK)

    # rules and tips; drop the tips or shrink the text when space is short
    show_example = game.example and game.key not in NO_EXAMPLE
    side_art = not show_example and not COMPACT
    text_w = W - 2 * M - (190 if side_art else 0)
    room = y - (index_top + 16)
    for tips, size in (((game.tips), 10.2), ((game.tips), 9.2), ((), 9.2), ((), 8.4)):
        lead = size * 1.35
        need = 15 + sum(para_height(r, text_w - 13, "Sans", size, lead) + 6.5
                        for r in game.rules)
        if tips:
            need += 18 + sum(para_height(t, text_w - 13, "SerifI", size, lead) + 6.5
                             for t in tips)
        if need <= room or side_art:
            break
    text(c, M, y - 9, "SPELREGELS", "SansB", 8, GREY)
    y -= 15
    for rule in game.rules:
        circle(c, M + 3.5, y - size * 0.73, 2.2, fill=INK, stroke=None)
        y = paragraph(c, M + 13, y, text_w - 13, rule, "Sans", size, leading=lead) - 6.5
    if tips:
        y -= 3
        text(c, M, y - 9, "SLIMME TIPS", "SansB", 8, GREY)
        y -= 15
        for tip in tips:
            icon_check(c, M + 4, y - size * 0.7, 7, _accent(info), 1.6)
            y = paragraph(c, M + 13, y, text_w - 13, tip, "SerifI", size, leading=lead) - 6.5
    if show_example:
        avail = y - (index_top + 16)
        if avail > 90:
            _example(c, game, ctx["examples"][game.key], M, index_top + 14,
                     W - 2 * M, avail)
    elif side_art:
        top_y = BAR_Y - 44 - 30
        image(c, f"cat_{game.category}", W - M - 178, top_y - 182, 178, 178)
        y = min(y, top_y - 186)
        avail = y - (index_top + 22)
        if avail > 110:
            _teaser(c, game, ctx["examples"][game.key], M, index_top + 16,
                    W - 2 * M, avail)
    else:
        avail = y - (index_top + 22)
        if avail > 110:
            _teaser(c, game, ctx["examples"][game.key], M, index_top + 16,
                    W - 2 * M, avail)


def page_solutions_intro(c, ctx):
    y = _simple_header(c, "Oplossingen", "Niet spieken!", {
        "home": "home", "training": ctx["nav_training"], "prev": "home", "next": "home"})
    y = paragraph(c, M, y - 12, W - 2 * M,
                  "Vanaf hier vind je alle oplossingen. Je komt er het snelst "
                  "via de knop Oplossing onderaan elke puzzel. Kies hieronder "
                  "een spel om naar de eerste oplossing te springen.",
                  "Sans", 9.5 if COMPACT else 10.5, leading=13 if COMPACT else 15) - 14
    cols = 2
    gap = 8 if COMPACT else 12
    bw = (W - 2 * M - gap) / cols
    rows = math.ceil(len(ctx["games"]) / cols)
    bottom = 60 if COMPACT else 66
    vgap = 9 if rows <= 8 else 6
    bh = max(18, min(40, (y - bottom) / rows - vgap))
    for i, game in enumerate(ctx["games"]):
        info = CATEGORIES[game.category]
        bx = M + (i % cols) * (bw + gap)
        by = y - (i // cols + 1) * (bh + vgap)
        rrect(c, bx, by, bw, bh, 9, stroke=INK, lw=1.2)
        rad = min(13, bh / 2 - 4)
        circle(c, bx + 8 + rad, by + bh / 2, rad, fill=info["color"], stroke=None)
        game.icon(c, bx + 8 + rad, by + bh / 2, rad * 1.15, info["on"])
        x = bx + 16 + 2 * rad
        size = fit_size(game.name, "SansS", bx + bw - 6 - x, 10.5)
        text(c, x, by + bh / 2 - size * 0.35, game.name, "SansS", size, INK)
        link(c, (bx, by, bw, bh), f"s:{game.key}:1")
    _bottom_buttons(c, None, ("Startscherm", "home", True))


def page_colophon(c, ctx):
    sel = ctx["selection"]
    y = _simple_header(c, "Colofon", f"Editie {ctx['seed']}", {
        "home": "home", "training": ctx["nav_training"], "prev": "home", "next": "home"})
    extra = f", {plural(len(ctx['plan']), 'dag', 'dagen')} training" if ctx["plan"] else ""
    blocks = [
        ("Remarkable Mind",
         f"Versie {__version__}, editie {ctx['seed']}. "
         f"{plural(ctx['n_games'], 'spel', 'spellen')}, {ctx['n_puzzles']} puzzels"
         f"{extra}. Deze uitgave is gemaakt voor de {theme.DEVICE['label']} "
         f"({theme.DEVICE['screen']}) en ook bruikbaar op andere e-paper tablets."),
        ("Puzzels",
         "Alle puzzels zijn procedureel gegenereerd. Elke logische puzzel is "
         "met een solver gecontroleerd op precies één oplossing. Met een "
         "ander editienummer bouw je een volledig nieuw boek."
         + ("" if sel.solutions else " Deze uitgave bevat geen oplossingen.")),
        ("Beeld",
         "De illustraties in risografie-stijl zijn gegenereerd met de "
         "beeldmodellen van ElevenLabs. De pictogrammen en puzzels zijn "
         "vectortekeningen, zodat ze haarscherp blijven op e-ink."),
        ("Letters en woorden",
         "Fraunces, Inter en Caveat, alle drie onder de SIL Open Font License. "
         "De woordladders gebruiken woorden uit de OpenTaal-woordenlijst "
         "(BSD / CC BY 3.0)."),
        ("Merken",
         "reMarkable is een merk van reMarkable AS. Dit is een onafhankelijk "
         "project, niet verbonden met of goedgekeurd door reMarkable AS."),
    ]
    size, lead = (9, 12.4) if COMPACT else (10, 14.2)
    y -= 16
    for head, body in blocks:
        text(c, M, y - 10, head, "SansB", 10.5 if COMPACT else 11, INK)
        y = paragraph(c, M, y - 14, W - 2 * M, body, "Sans", size, leading=lead) - 14
    gap = 18
    s = min(100, (W - 2 * M - 3 * gap) / 4, max(0, y - 62 - (8 if COMPACT else 12)))
    if s > 40:
        for i, cat in enumerate(CATEGORY_ORDER):
            image(c, f"cat_{cat}", M + i * (s + gap), 62 if COMPACT else 70, s, s)
    _bottom_buttons(c, None, ("Startscherm", "home", True))


# --- assembly -------------------------------------------------------------------
def default_out(device):
    return ROOT / "dist" / f"RemarkableMind{theme.DEVICES[device]['suffix']}.pdf"


def build(seed=2026, out=None, jobs=4, cache=ROOT / "build" / "cache",
          log=print, strict=True, only=None, device="paperpro", selection=None,
          progress=None):
    """Build a book. progress(stage, done, total) is called with stage
    "puzzels" while puzzles are generated and "pagina's" while drawing."""
    register_fonts()
    theme.set_device(device)
    out = Path(out or default_out(device))
    t0 = time.time()
    if selection is None:
        all_games = games.all_games(strict and not only)
        if only:                            # dev builds: a subset of the games
            all_games = [g for g in all_games if g.key in only]
        selection = Selection({g.key: sum(g.counts) for g in all_games})
    all_games = [games.get(k) for k in selection.counts]
    levels = selection.levels
    total_puz = sum(len(v) for v in levels.values())
    done_puz = {}

    def gen_progress(key, i, n):
        done_puz[key] = i
        if progress:
            progress("puzzels", sum(done_puz.values()), total_puz)

    puzzles = build_puzzles(seed, cache, jobs, log, all_games, levels, gen_progress)
    examples = {g.key: g.generate(random.Random(f"{seed}:{g.key}:example"), 1)
                for g in all_games}
    plan = training_plan(all_games, levels) if selection.plan else []
    if len(plan) < 3:
        plan = []
    ctx = {"seed": seed, "games": all_games, "puzzles": puzzles, "plan": plan,
           "levels": levels, "selection": selection, "examples": examples,
           "n_games": len(all_games), "n_puzzles": total_puz,
           "nav_training": "training1" if plan else False}
    ctx["plan_pages"] = training_pages(plan) if plan else []
    in_plan = {}
    for p, (a, b) in enumerate(ctx["plan_pages"]):
        for row in plan[a:b]:
            for g, idx in row:
                in_plan[(g.key, idx)] = f"training{p + 1}"
    ctx["howto_pages"] = howto_pages(ctx)
    ctx["howto_last"] = "howto" if len(ctx["howto_pages"]) == 1 else \
        f"howto{len(ctx['howto_pages'])}"
    ctx["after_howto"] = "training1" if plan else "score"
    ctx["score_pages"] = score_pages(ctx)

    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".raw.pdf")
    c = canvas.Canvas(str(raw), pagesize=(W, H), pageCompression=1)
    c.setTitle(f"{TITLE} – {SUBTITLE}")
    c.setAuthor("Remarkable Mind")
    c.setSubject(f"{plural(ctx['n_games'], 'hersenspel', 'hersenspellen')}, "
                 f"{total_puz} puzzels, offline voor de {theme.DEVICE['label']}")
    c.setCreator(f"remarkable_mind {__version__} (editie {seed})")
    n_links = [0]
    _link_rect = c.linkRect

    def counting_link(*a, **k):
        n_links[0] += 1
        return _link_rect(*a, **k)

    c.linkRect = counting_link

    n_pages = (2 + len(ctx["howto_pages"]) + len(ctx["plan_pages"]) + len(ctx["score_pages"])
               + len(all_games) + sum(len(levels[g.key]) * g.parts for g in all_games)
               + ((1 + total_puz) if selection.solutions else 0) + 1)
    keys = {}                                   # destination key -> page index

    def page(key, draw, *args, outline=None, level=0):
        keys[key] = len(keys)
        c.bookmarkPage(key, fit="Fit")
        if outline:
            c.addOutlineEntry(outline, key, level=level, closed=level == 0)
        draw(c, *args)
        c.showPage()
        if progress:
            progress("pagina's", len(keys), n_pages)

    page("cover", page_cover, ctx, outline=TITLE)
    page("home", page_home, ctx, outline="Startscherm")
    for p in range(len(ctx["howto_pages"])):
        page("howto" if p == 0 else f"howto{p + 1}", page_howto, ctx, p,
             outline="Uitleg" if p == 0 else None)
    for p in range(len(ctx["plan_pages"])):
        page(f"training{p + 1}", page_training, ctx, p,
             outline=f"{len(plan)} dagen hersengym" if p == 0 else None)
    for p in range(len(ctx["score_pages"])):
        page("score" if p == 0 else f"score{p + 1}", page_score, ctx, p,
             outline="Scorebord" if p == 0 else None)

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
                    "training": in_plan.get((g.key, i), ctx["nav_training"]),
                    "prev": (f"p:{g.key}:{n - 1}" if n > 1 else f"hub:{g.key}")
                    if part == 0 else base,
                    "next": f"p:{g.key}:{n + 1}" if n < total else f"hub:{g.key}",
                    "continue": f"{base}:{'abcdefgh'[part + 1]}",
                    "solution": f"s:{g.key}:{n}" if selection.solutions else False,
                }
                page(key, lambda c, *a, **k: puzzle_page(c, *a, **k), g, puz, n,
                     levels[g.key][i], total, part, nav)

    if selection.solutions:
        page("solutions", page_solutions_intro, ctx, outline="Oplossingen")
        for g in all_games:
            total = len(puzzles[g.key])
            for i, puz in enumerate(puzzles[g.key]):
                n = i + 1
                back = f"p:{g.key}:{n}" + (f":{'abcdefgh'[g.parts - 1]}" if g.parts > 1 else "")
                nxt = f"p:{g.key}:{n + 1}" if n < total else f"hub:{g.key}"
                nav = {"home": "home", "hub": f"hub:{g.key}",
                       "training": in_plan.get((g.key, i), ctx["nav_training"]),
                       "prev": back, "next": nxt, "back": back, "next_puzzle": nxt}
                page(f"s:{g.key}:{n}", lambda c, *a, **k: solution_page(c, *a, **k),
                     g, puz, n, levels[g.key][i], total, nav,
                     outline=g.name if i == 0 else None, level=1)
    page("colophon", page_colophon, ctx, outline="Colofon")
    c.save()
    try:
        import pymupdf  # noqa: F401  (optional: rewrites links, compresses)
    except ImportError:
        pymupdf = None
    if pymupdf is not None:
        stats = finalize(raw, out)
        raw.unlink()
    else:                                   # browser build: reportlab already
        raw.replace(out)                    # writes explicit page links
        stats = {"pages": len(keys), "links": n_links[0],
                 "mb": round(out.stat().st_size / 1e6, 2)}
    out.with_suffix(".json").write_text(json.dumps(
        {"title": TITLE, "version": __version__, "seed": seed, "device": device,
         "games": selection.counts, "difficulty": selection.difficulty,
         "plan_days": len(plan), "solutions": selection.solutions, "pages": keys},
        indent=0))
    stats.update(seconds=round(time.time() - t0, 1), games=ctx["n_games"],
                 puzzles=total_puz)
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
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=2026, help="edition number")
    ap.add_argument("--device", choices=sorted(theme.DEVICES), default="paperpro",
                    help="paperpro (colour, default), move (Paper Pro Move), "
                         "rm2 (reMarkable 2, greyscale)")
    ap.add_argument("--out", default=None,
                    help="default: dist/RemarkableMind[-Move|-rM2].pdf")
    ap.add_argument("--games", default="",
                    help="e.g. sudoku:10,doolhof:6 (default: all games, 25 each)")
    ap.add_argument("--difficulty", choices=sorted(DIFFICULTIES), default="mix")
    ap.add_argument("--no-plan", action="store_true", help="leave out the day plan")
    ap.add_argument("--no-solutions", action="store_true", help="leave out solutions")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--dev", action="store_true",
                    help="skip games that are missing or broken")
    ap.add_argument("--only", default="", help="comma separated game keys (dev)")
    a = ap.parse_args(argv)
    selection = None
    if a.games or a.difficulty != "mix" or a.no_plan or a.no_solutions:
        kw = dict(difficulty=a.difficulty, plan=not a.no_plan,
                  solutions=not a.no_solutions)
        selection = (Selection.parse(a.games, **kw) if a.games else Selection(**kw))
    build(a.seed, Path(a.out) if a.out else None, a.jobs,
          strict=not (a.dev or a.only),
          only=set(a.only.split(",")) if a.only else None, device=a.device,
          selection=selection)


if __name__ == "__main__":
    sys.exit(main())
