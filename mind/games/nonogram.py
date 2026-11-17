"""Japanse puzzel (nonogram) - colour cells until a picture appears.

Pictures come from a small library of hand-drawn pixel icons and from a
procedural generator of mirror-symmetric masks and creatures. Every puzzle
is checked by a real solver (line solving + backtracking) to have exactly
one solution.
"""
import math

from ..draw import Grid, line, text, text_mid
from ..theme import INK, PEN, GREY
from .base import Game

# --- hand-drawn icons ---------------------------------------------------------
# name -> (Dutch title, rows). '#' = filled.
ICONS_10 = {
    "hart": ("een hart", """
.##....##.
####..####
##########
##########
##########
.########.
..######..
...####...
....##....
..........
"""),
    "huis": ("een huis", """
....##....
...####...
..######..
.########.
##########
.########.
.##..####.
.##..#..#.
.##..#..#.
.########.
"""),
    "boom": ("een boom", """
...####...
..######..
.########.
##########
##########
.########.
..######..
....##....
....##....
..######..
"""),
    "zeilboot": ("een zeilboot", """
....#.....
....##....
....###...
....####..
....#####.
....#.....
##########
.########.
..######..
..........
"""),
    "kat": ("een kat", """
#........#
##......##
###....###
##########
#.##..##.#
##########
####..####
#.######.#
.#......#.
..######..
"""),
    "sleutel": ("een sleutel", """
.####.....
##..##....
#....#....
##..##....
.####.....
..##......
..##......
..####....
..##......
..####....
"""),
    "kopje": ("een kopje koffie", """
..#..#....
.#..#.....
..#..#....
########..
#########.
########.#
########.#
#########.
.######...
##########
"""),
    "paraplu": ("een paraplu", """
....##....
..######..
.########.
##########
#.#.##.#.#
....#.....
....#.....
....#.....
.#..#.....
..##......
"""),
    "raket": ("een raket", """
....##....
...####...
...#..#...
...#..#...
...####...
..######..
.##.##.##.
.#..##..#.
....##....
...#..#...
"""),
    "vis": ("een vis", """
..........
..###....#
.#####..##
###.######
##########
##########
.#####..##
..###....#
..........
..........
"""),
    "paddenstoel": ("een paddenstoel", """
...####...
..######..
.##.##.##.
##########
##.####.##
##########
...####...
...#..#...
...#..#...
..######..
"""),
    "anker": ("een anker", """
....##....
...#..#...
....##....
..######..
....##....
....##....
#...##...#
##..##..##
.########.
..######..
"""),
    "ster": ("een ster", """
....##....
....##....
...####...
##########
.########.
..######..
..######..
.###..###.
.##....##.
##......##
"""),
    "eend": ("een eend", """
..###.....
.#.###....
#####.....
.####.....
..####...#
.#######.#
.#########
.########.
..######..
...#..#...
"""),
    "appel": ("een appel", """
.....#....
....##....
..##.###..
.########.
##########
##########
##########
.########.
.###..###.
..##..##..
"""),
    "tulp": ("een tulp", """
.#..##..#.
.##.##.##.
.########.
.########.
..######..
...####...
....##....
.#..##..#.
.##.##.##.
..######..
"""),
    "maan": ("de maan", """
...####...
..#####...
.####.....
.###......
####......
####......
.###.....#
.####...##
..#######.
...#####..
"""),
    "vlinder": ("een vlinder", """
#...##...#
##..##..##
###.##.###
##########
.########.
.########.
##########
###.##.###
##..##..##
#........#
"""),
    "auto": ("een auto", """
..........
...####...
..#..#.#..
.#...#..#.
##########
##########
##########
.##....##.
.##....##.
..........
"""),
}

ICONS_15 = {
    "dennenboom": ("een dennenboom", """
.......#.......
......###......
.....#####.....
....#######....
......###......
.....#####.....
....#######....
...#########...
.....#####.....
....#######....
...#########...
..###########..
.#############.
......###......
......###......
"""),
    "huis": ("een huis met schoorsteen", """
.......#.......
......###..##..
.....#####.##..
....#########..
...##########..
..###########..
.#############.
..###########..
..##..###..##..
..##..###..##..
..###########..
..####...####..
..####...####..
..####...####..
..####...####..
"""),
    "kat": ("een zittende kat", """
..#...#........
..##.##........
..#####........
..#.#.#........
..#####........
...###.........
..#####......#.
.#######.....##
.########....##
.#########...##
.##########.##.
.#############.
.############..
.####..#####...
.##.#..#.##....
"""),
    "kopje": ("een dampend kopje", """
.....#.........
....##...##....
...##...##.....
....##...##....
...............
.###########...
.#############.
.###########.##
.###########..#
.###########.##
.#############.
.###########...
..#########....
...............
###############
"""),
    "raket": ("een raket", """
.......#.......
......###......
.....#####.....
.....#####.....
.....##.##.....
.....##.##.....
.....#####.....
.....#####.....
....#######....
...#########...
..###.###.###..
..##..###..##..
..#...###...#..
.......#.......
......#.#......
"""),
    "paddenstoel": ("een paddenstoel", """
....#######....
..###########..
.####..###..##.
.####..###..##.
###############
##..#####..####
##..#####..####
###############
.....#####.....
.....#####.....
.....#####.....
.....#####.....
....#######....
...#########...
...............
"""),
    "vuurtoren": ("een vuurtoren", """
.......#.......
......###......
.....#####.....
.....#.#.#.....
......###......
.....#####.....
.....#...#.....
.....#####.....
....#######....
....##...##....
....#######....
...#########...
...###...###...
..###########..
###############
"""),
    "eend": ("een eend", """
....####.......
...######......
...##.####.....
#########......
.########......
...######......
...######.....#
..########...##
.###########.##
.##############
.##############
.#############.
..###########..
...#########...
.....##.##.....
"""),
    "vis": ("een vis", """
...............
..#............
.....#.........
....#####.....#
..#########..##
.###.#######.##
.##############
###############
###############
.##############
.###########.##
..#########..##
....#####.....#
...............
...............
"""),
    "anker": ("een anker", """
......###......
.....##.##.....
.....##.##.....
......###......
.......#.......
...#########...
...#########...
.......#.......
.......#.......
#......#......#
##.....#.....##
###....#....###
.###...#...###.
..###########..
....#######....
"""),
    "hart": ("een hart", """
..###.....###..
.#####...#####.
#######.#######
###############
###############
###############
###############
.#############.
..###########..
...#########...
....#######....
.....#####.....
......###......
.......#.......
...............
"""),
    "fiets": ("een fiets", """
...............
...............
..###......##..
....#......#...
....########...
....##....##...
...#.#...#.#...
...#..#..#..#..
.###..#.#..###.
#...#..##.#...#
#.######..###.#
#...#.....#...#
.###.......###.
...............
...............
"""),
    "zeilboot": ("een zeilboot", """
.......#.......
......##.......
.....###.#.....
....####.##....
...#####.###...
..######.####..
.#######.#####.
########.######
.......#.......
###############
.#############.
..###########..
...#########...
...............
###.###.###.###
"""),
    "kasteel": ("een kasteel", """
#.#.#.....#.#.#
#####.....#####
#####.#.#.#####
.###..###..###.
.###.#####.###.
.#############.
.##.#######.##.
.#############.
.#############.
.#####...#####.
.####.....####.
.####.....####.
.####.....####.
.####.....####.
###############
"""),
    "cactus": ("een cactus", """
......###......
.....#####.....
.....#####..#..
.#...#####.###.
###..#####.###.
###..#####.###.
###..#########.
###..########..
#########......
.########......
.....#####.....
.....#####.....
...#########...
....#######....
....#######....
"""),
}


def _parse(art):
    rows = [r for r in art.strip().splitlines()]
    w = len(rows[0])
    assert all(len(r) == w for r in rows), "ragged icon"
    return [[1 if ch == "#" else 0 for ch in r] for r in rows]


# --- clues and solver ---------------------------------------------------------
def line_clue(cells):
    out, run = [], 0
    for v in cells:
        if v:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out


def clues_of(grid):
    rows = [line_clue(r) for r in grid]
    cols = [line_clue([r[c] for r in grid]) for c in range(len(grid[0]))]
    return rows, cols


def solve_line(clue, cells):
    """Deduce a line. cells: list of -1 (unknown) / 0 / 1.
    Returns the refined list, or None if the clue cannot fit."""
    n, k = len(cells), len(clue)
    can_fill = [False] * n
    can_empty = [False] * n
    memo = {}

    def rec(pos, ci):
        key = (pos, ci)
        if key in memo:
            return memo[key]
        if ci == k:
            ok = all(cells[x] != 1 for x in range(pos, n))
            if ok:
                for x in range(pos, n):
                    can_empty[x] = True
            memo[key] = ok
            return ok
        length = clue[ci]
        need = sum(clue[ci:]) + (k - ci - 1)
        result = False
        for start in range(pos, n - need + 1):
            if start > pos and cells[start - 1] == 1:
                break
            end = start + length
            if any(cells[x] == 0 for x in range(start, end)):
                continue
            if end < n and cells[end] == 1:
                continue
            if rec(min(end + 1, n), ci + 1):
                result = True
                for x in range(pos, start):
                    can_empty[x] = True
                for x in range(start, end):
                    can_fill[x] = True
                if end < n:
                    can_empty[end] = True
        memo[key] = result
        return result

    if not rec(0, 0):
        return None
    out = []
    for x in range(n):
        if can_fill[x] and can_empty[x]:
            out.append(-1)
        else:
            out.append(1 if can_fill[x] else 0)
    return out


def _propagate(rows, cols, grid):
    """Line-solve until stable. Returns False on contradiction."""
    h, w = len(rows), len(cols)
    todo_r, todo_c = set(range(h)), set(range(w))
    while todo_r or todo_c:
        for r in sorted(todo_r):
            new = solve_line(rows[r], grid[r])
            if new is None:
                return False
            for c in range(w):
                if new[c] != grid[r][c]:
                    grid[r][c] = new[c]
                    todo_c.add(c)
        todo_r = set()
        for c in sorted(todo_c):
            col = [grid[r][c] for r in range(h)]
            new = solve_line(cols[c], col)
            if new is None:
                return False
            for r in range(h):
                if new[r] != col[r]:
                    grid[r][c] = new[r]
                    todo_r.add(r)
        todo_c = set()
    return True


def count_solutions(rows, cols, limit=2, max_nodes=400, out=None):
    """Number of grids matching the clues, capped at ``limit``.
    Gives up (returning ``limit``) after ``max_nodes`` search nodes."""
    h, w = len(rows), len(cols)
    found = 0
    nodes = 0

    def search(grid):
        nonlocal found, nodes
        nodes += 1
        if nodes > max_nodes:
            found = limit
            return
        if not _propagate(rows, cols, grid):
            return
        for r in range(h):
            for c in range(w):
                if grid[r][c] == -1:
                    for v in (1, 0):
                        g2 = [row[:] for row in grid]
                        g2[r][c] = v
                        search(g2)
                        if found >= limit:
                            return
                    return
        found += 1
        if out is not None and found == 1:
            out[:] = [row[:] for row in grid]

    search([[-1] * w for _ in range(h)])
    return found


def is_unique(grid):
    rows, cols = clues_of(grid)
    return count_solutions(rows, cols, 2) == 1


# --- procedural pictures --------------------------------------------------------
def _mirror(half, w):
    """half: rows of ceil(w/2) cells (left part incl. centre) -> full rows."""
    out = []
    for row in half:
        left = row[: w // 2]
        mid = row[w // 2: w // 2 + (w % 2)]
        out.append(left + mid + left[::-1])
    return out


def _creature(rng, n):
    """A blobby mirror-symmetric 'space creature' via cellular smoothing."""
    hw = (n + 1) // 2
    g = [[1 if rng.random() < 0.52 else 0 for _ in range(hw)] for _ in range(n)]
    for _ in range(2):
        new = [[0] * hw for _ in range(n)]
        for y in range(n):
            for x in range(hw):
                s = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if xx >= hw:            # mirror across the centre
                            xx = hw - 1 - (n % 2 == 0 and 0 or 1) if hw > 1 else 0
                        if 0 <= yy < n and 0 <= xx < hw:
                            s += g[yy][xx]
                new[y][x] = 1 if s >= 5 else 0
        g = new
    # eyes: punch two holes in the upper half when there is body around them
    ey = rng.randrange(n // 4, n // 2)
    ex = rng.randrange(max(1, hw - 4), hw - 1)
    if g[ey][ex] and g[ey - 1][ex] and g[ey + 1][ex]:
        g[ey][ex] = 0
    return _mirror(g, n)


def _mask(rng, n):
    """A mirror-symmetric mask: outline, eyes, nose, mouth, horns/ears."""
    hw = (n + 1) // 2
    cx = (n - 1) / 2.0
    top = rng.randrange(2, max(3, n // 5 + 1))          # rows used by horns
    cy = top + (n - top - 1) / 2.0
    ry = (n - top) / 2.0
    rx = n / 2.0 - rng.choice([0, 0, 1])
    power = rng.choice([2.0, 2.6, 3.4])                  # round .. boxy
    chin = rng.uniform(0.0, 0.45)                        # narrower lower half
    g = [[0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            dy = (y - cy) / ry
            dx = (x - cx) / rx
            if dy > 0:
                dx *= 1 + chin * dy
            if abs(dx) ** power + abs(dy) ** power <= 1.0:
                g[y][x] = 1
    # horns or ears growing from the top
    kind = rng.choice(["horns", "ears", "crown"])
    for y in range(top + 1):
        for x in range(hw):
            on = False
            if kind == "horns":
                on = x in (1 + (top - y) // 2 * 0 + y // 2, 2 + y // 2)
            elif kind == "ears":
                on = (1 + y // 2) <= x <= 3 and y >= 1 or (x == 2 and y == 0)
            else:
                on = x % 3 != 2 and y >= top - 1 or x % 3 == 0
            if on:
                g[y][x] = 1
                g[y][n - 1 - x] = 1
    # eyes
    ey = int(cy - ry * rng.uniform(0.25, 0.4))
    ew = rng.choice([2, 2, 3]) if n >= 15 else rng.choice([1, 2])
    eh = rng.choice([1, 2]) if n >= 15 else 1
    ex = hw - 2 - ew - rng.choice([0, 1]) + (0 if n >= 15 else 1)
    for y in range(ey, ey + eh):
        for x in range(ex, ex + ew):
            if 0 <= x < hw:
                g[y][x] = 0
                g[y][n - 1 - x] = 0
    if eh == 2 and ew >= 2 and rng.random() < 0.6:       # pupils
        g[ey + 1][ex + ew - 1] = 1
        g[ey + 1][n - 1 - (ex + ew - 1)] = 1
    # nose
    ny = ey + eh + 1
    for y in range(ny, ny + rng.choice([1, 2, 2])):
        g[y][hw - 1] = 0
        g[y][n - hw] = 0
    # mouth
    my = int(cy + ry * rng.uniform(0.45, 0.6))
    mw = rng.randrange(2, max(3, hw - 2))
    teeth = rng.random() < 0.5
    for x in range(hw - mw, hw):
        if not (teeth and (hw - x) % 2 == 0):
            g[my][x] = 0
            g[my][n - 1 - x] = 0
    if rng.random() < 0.5 and my + 1 < n - 1:
        for x in range(hw - mw + 1, hw):
            g[my + 1][x] = 0
            g[my + 1][n - 1 - x] = 0
    # war paint on the bigger masks: a dashed band across the forehead
    if n >= 20 and ey - 2 > top + 1 and rng.random() < 0.7:
        for x in range(2 + rng.choice([0, 1]), hw - 1, 2):
            if g[ey - 2][x] and g[ey - 3][x]:
                g[ey - 2][x] = 0
                g[ey - 2][n - 1 - x] = 0
    if n >= 20 and rng.random() < 0.6:                  # chin stripes
        for x in range(hw - 1 - rng.choice([2, 3]), hw, 2):
            for y in range(my + 2, n - 1):
                if g[y][x] and g[y + 1][x]:
                    g[y][x] = 0
                    g[y][n - 1 - x] = 0
    # cheek marks
    if rng.random() < 0.6:
        yy = rng.randrange(ey + eh + 1, max(ey + eh + 2, my))
        g[yy][1 + rng.choice([0, 1])] ^= 1
        g[yy] = _mirror([g[yy][:hw]], n)[0]
    return g


def _procedural(rng, n):
    for _ in range(400):
        if rng.random() < 0.7:
            grid, title = _mask(rng, n), "een masker"
        else:
            grid, title = _creature(rng, n), "een ruimtewezen"
        filled = sum(map(sum, grid))
        if not 0.38 * n * n <= filled <= 0.74 * n * n:
            continue
        if any(sum(r) == 0 for r in grid):
            continue
        if any(sum(r[c] for r in grid) == 0 for c in range(n)):
            continue
        if is_unique(grid):
            return grid, title
    raise RuntimeError("no unique procedural nonogram found")


class Nonogram(Game):
    key = "nonogram"
    name = "Japanse puzzel"
    category = "ruimte"
    tagline = "Kleur de juiste vakjes en ontdek de tekening."
    rules = [
        "De getallen naast een rij en boven een kolom geven aan hoe lang de "
        "groepjes gekleurde vakjes zijn, in de juiste volgorde.",
        "Tussen twee groepjes in dezelfde rij of kolom staat minstens één leeg vakje.",
        "Kleur een vakje dat zeker gevuld is; zet een puntje of kruisje in een "
        "vakje dat zeker leeg blijft.",
    ]
    tips = [
        "Begin bij de grootste getallen: een groep van 8 in een rij van 10 "
        "vult de middelste 6 vakjes sowieso.",
        "Een 0 of een lege aanwijzing betekent: de hele lijn blijft leeg.",
    ]
    counts = (9, 8, 8)
    SIZE = {1: 10, 2: 15, 3: 20}

    def fingerprints(self, puz):
        return [f"pic:{puz['pic']}"] if puz.get("pic") else []

    def generate(self, rng, level, avoid=()):
        """``avoid``: optional collection of ``puz["pic"]`` names already used,
        so a book can skip hand-drawn pictures it has shown before."""
        n = self.SIZE[level]
        lib = {1: ICONS_10, 2: ICONS_15}.get(level)
        grid = title = None
        pic = ""
        if lib and rng.random() < 0.8:
            names = sorted(lib)
            rng.shuffle(names)
            for name in names:
                if name in avoid:
                    continue
                cand = _parse(lib[name][1])
                if rng.random() < 0.5:
                    cand = [r[::-1] for r in cand]
                if is_unique(cand):
                    grid, title, pic = cand, lib[name][0], name
                    break
        if grid is None:
            grid, title = _procedural(rng, n)
        rows, cols = clues_of(grid)
        return {"size": n, "rows": rows, "cols": cols, "solution": grid,
                "title": title, "pic": pic}

    def verify(self, puz):
        n = puz["size"]
        grid = puz["solution"]
        assert len(grid) == n and all(len(r) == n for r in grid)
        assert all(v in (0, 1) for r in grid for v in r)
        rows, cols = clues_of(grid)
        assert rows == puz["rows"] and cols == puz["cols"], "clues do not match"
        assert len(puz["rows"]) == n and len(puz["cols"]) == n
        found = []
        assert count_solutions(puz["rows"], puz["cols"], 2, max_nodes=5000,
                               out=found) == 1, "nonogram must be unique"
        assert found == grid

    def instruction(self, puz, part=0):
        return ("Elk getal is de lengte van een groepje gekleurde vakjes "
                "in die rij of kolom.")

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["size"]
        rows, cols = puz["rows"], puz["cols"]
        slot = 0.62 if n <= 15 else 0.66           # clue slot, in cell units
        left = max(len(r) for r in rows) * slot + 0.4
        top = max(len(k) for k in cols) * slot + 0.25
        x, y, w, h = box
        g = Grid((x, y + 26, w, h - 26), n, n, max_cell=34, left=left, top=top)
        cell = g.cell
        fs = cell * (0.50 if n <= 15 else 0.54)
        if solved:
            for r in range(n):
                for col in range(n):
                    if puz["solution"][r][col]:
                        g.fill(c, r, col, PEN, inset=0.9)
        g.lines(c, lw=0.5, outer=2.0, block=(5, 5), block_lw=1.5)
        for r, clue in enumerate(rows):
            vals = clue or [0]
            for i, v in enumerate(reversed(vals)):
                text_mid(c, g.x(0) - (i + 0.5) * slot * cell - 0.22 * cell,
                         g.cy(r), v, "SansS", fs, INK)
        for col, clue in enumerate(cols):
            vals = clue or [0]
            for i, v in enumerate(reversed(vals)):
                text_mid(c, g.cx(col),
                         g.y(0) + (i + 0.5) * slot * cell + 0.1 * cell,
                         v, "SansS", fs, INK)
        # thin guides separating clue rows/columns every five lines
        for k in range(0, n + 1, 5):
            line(c, g.x(0) - left * cell + 2, g.y(k), g.x(0), g.y(k), 0.5, GREY)
            line(c, g.x(k), g.y(0), g.x(k), g.y(0) + top * cell - 2, 0.5, GREY)
        ty = g.y(n) - 20
        if solved:
            text(c, x + w / 2, ty, "Dit is: " + puz["title"], "Hand", 19, PEN, "c")
        else:
            text(c, x + w / 2, ty + 3, "Wat zie je?  ................................",
                 "SansM", 9, GREY, "c")

    def icon(self, c, cx, cy, s, color):
        pat = ["#.#.", ".###", "##.#", ".##."]
        q = s / 4
        c.saveState()
        c.setFillColor(color)
        for r, row in enumerate(pat):
            for k, ch in enumerate(row):
                if ch == "#":
                    c.rect(cx - s / 2 + k * q + 0.6, cy + s / 2 - (r + 1) * q + 0.6,
                           q - 1.2, q - 1.2, stroke=0, fill=1)
        c.restoreState()
        for k in range(5):
            line(c, cx - s / 2 + k * q, cy - s / 2, cx - s / 2 + k * q, cy + s / 2,
                 0.7, color, cap=2)
            line(c, cx - s / 2, cy - s / 2 + k * q, cx + s / 2, cy - s / 2 + k * q,
                 0.7, color, cap=2)


GAME = Nonogram()
