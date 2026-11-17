"""Binairo - the binary puzzle: nullen en enen in balans."""
from itertools import combinations

from ..draw import Grid, line, text_mid
from .base import Game

SIZES = {1: 6, 2: 8, 3: 10}
KEEP = {1: 0.42, 2: 0.36, 3: 0.30}   # share of cells that stay filled in


def _valid_rows(n):
    """Balanced 0/1 rows of length n without three equal neighbours."""
    rows = []
    for ones in combinations(range(n), n // 2):
        row = [0] * n
        for i in ones:
            row[i] = 1
        if all(not (row[i] == row[i + 1] == row[i + 2]) for i in range(n - 2)):
            rows.append(tuple(row))
    return rows


_ROWS = {}


def valid_rows(n):
    if n not in _ROWS:
        _ROWS[n] = _valid_rows(n)
    return _ROWS[n]


def full_grid(rng, n):
    """A random completely filled, valid grid as a flat list."""
    options = valid_rows(n)
    half = n // 2
    while True:
        rows = []
        ones = [0] * n

        def place(r):
            if r == n:
                return True
            cand = list(options)
            rng.shuffle(cand)
            for row in cand:
                if row in rows:
                    continue
                ok = True
                for c in range(n):
                    o = ones[c] + row[c]
                    if o > half or (r + 1 - o) > half:
                        ok = False
                        break
                    if r >= 2 and rows[r - 1][c] == rows[r - 2][c] == row[c]:
                        ok = False
                        break
                if not ok:
                    continue
                rows.append(row)
                for c in range(n):
                    ones[c] += row[c]
                if place(r + 1):
                    return True
                rows.pop()
                for c in range(n):
                    ones[c] -= row[c]
            return False

        if place(0):
            cols = [tuple(rows[r][c] for r in range(n)) for c in range(n)]
            if len(set(cols)) == n:
                return [v for row in rows for v in row]


def count_solutions(n, grid, limit=2, out=None):
    """grid: flat list with 0, 1 or -1 (empty). Counts valid completions."""
    lines = ([[r * n + c for c in range(n)] for r in range(n)]
             + [[r * n + c for r in range(n)] for c in range(n)])
    pats = [tuple(1 << v for v in row) for row in valid_rows(n)]
    dom = [3 if v < 0 else 1 << v for v in grid]
    idx = range(n)
    found = 0

    def propagate(dom, cands):
        changed = True
        while changed:
            changed = False
            for li, cells in enumerate(lines):
                old = cands[li]
                d = [dom[i] for i in cells]
                new = [p for p in old if all(d[k] & p[k] for k in idx)]
                if not new:
                    return False
                if len(new) != len(old):
                    cands[li] = new
                for k in idx:
                    m = 0
                    for p in new:
                        m |= p[k]
                    if m != d[k]:
                        dom[cells[k]] = m
                        changed = True
            # a finished line may not be repeated by a parallel line
            for group in (range(n), range(n, 2 * n)):
                fixed = [cands[li][0] for li in group if len(cands[li]) == 1]
                if len(set(fixed)) != len(fixed):
                    return False
                fixed = set(fixed)
                for li in group:
                    if len(cands[li]) > 1:
                        new = [p for p in cands[li] if p not in fixed]
                        if not new:
                            return False
                        if len(new) != len(cands[li]):
                            cands[li] = new
                            changed = True
        return True

    def search(dom, cands):
        nonlocal found
        if not propagate(dom, cands):
            return
        best = next((i for i, m in enumerate(dom) if m == 3), -1)
        if best < 0:
            found += 1
            if out is not None and found == 1:
                out[:] = [m >> 1 for m in dom]
            return
        for bit in (1, 2):
            d2 = list(dom)
            d2[best] = bit
            search(d2, list(cands))
            if found >= limit:
                return

    search(dom, [list(pats) for _ in lines])
    return found


def check_rules(n, sol):
    rows = [tuple(sol[r * n:(r + 1) * n]) for r in range(n)]
    cols = [tuple(sol[c::n]) for c in range(n)]
    for group in (rows, cols):
        assert len(set(group)) == n, "lines must all differ"
        for ln in group:
            assert set(ln) <= {0, 1}
            assert sum(ln) == n // 2, "as many ones as zeros"
            assert all(not (ln[i] == ln[i + 1] == ln[i + 2])
                       for i in range(n - 2)), "no three in a row"


class Binairo(Game):
    key = "binairo"
    name = "Binairo"
    category = "logica"
    tagline = "Alleen nullen en enen, en toch verrassend lastig."
    rules = [
        "Vul elk leeg vakje met een 0 of een 1.",
        "Er staan nooit meer dan twee dezelfde cijfers naast of onder "
        "elkaar.",
        "In elke rij en elke kolom staan evenveel nullen als enen.",
        "Geen twee rijen zijn gelijk, en geen twee kolommen zijn gelijk.",
    ]
    tips = [
        "Twee gelijke cijfers naast elkaar? Dan staat er aan beide kanten "
        "het andere cijfer.",
        "Tel de nullen en enen van een bijna volle rij: de rest ligt dan "
        "vast.",
    ]

    def generate(self, rng, level):
        n = SIZES[level]
        sol = full_grid(rng, n)
        grid = list(sol)
        target = round(n * n * KEEP[level])
        cells = list(range(n * n))
        rng.shuffle(cells)
        left = n * n
        for i in cells:
            if left <= target:
                break
            grid[i] = -1
            if count_solutions(n, grid, 2) == 1:
                left -= 1
            else:
                grid[i] = sol[i]
        return {"n": n, "grid": grid, "solution": sol}

    def verify(self, puz):
        n, grid, sol = puz["n"], puz["grid"], puz["solution"]
        assert len(grid) == n * n and len(sol) == n * n
        check_rules(n, sol)
        for i in range(n * n):
            assert grid[i] in (-1, sol[i])
        assert count_solutions(n, grid, 2) == 1, "binairo must be unique"

    def instruction(self, puz, part=0):
        return ("Vul aan met 0 en 1: nooit drie gelijke naast elkaar, evenveel "
                "nullen als enen, geen dubbele lijnen.")

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        g = Grid(box, n, n, max_cell=66)
        g.lines(c, lw=0.7, outer=min(2.4, max(1.0, g.cell * 0.06)))
        for i in range(n * n):
            r, col = divmod(i, n)
            if puz["grid"][i] >= 0:
                g.given(c, r, col, puz["grid"][i])
            elif solved:
                g.answer(c, r, col, puz["solution"][i])

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        for k in (-h, 0, h):
            lw = 1.0 if k == 0 else 1.8
            line(c, cx + k, cy - h, cx + k, cy + h, lw, color, cap=2)
            line(c, cx - h, cy + k, cx + h, cy + k, lw, color, cap=2)
        q = s / 4
        for dx, dy, v in ((-q, q, "0"), (q, q, "1"), (-q, -q, "1"),
                          (q, -q, "0")):
            text_mid(c, cx + dx, cy + dy, v, "SansB", s * 0.36, color)


GAME = Binairo()
