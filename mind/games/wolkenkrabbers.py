"""Wolkenkrabbers (Skyscrapers) - a Latin square with view clues."""
from itertools import permutations

from ..draw import Grid, line, text_mid
from ..theme import INK
from .base import Game

SIZES = {1: 4, 2: 5, 3: 6}
KEEP = {1: 11, 2: 11, 3: 12}     # clues that stay on the board (at most)


def visible(seq):
    count = top = 0
    for v in seq:
        if v > top:
            top = v
            count += 1
    return count


_PERMS = {}


def _perms(n):
    """All permutations of 1..n as (bit tuple, view from start, from end)."""
    if n not in _PERMS:
        _PERMS[n] = [(tuple(1 << (v - 1) for v in p), visible(p),
                      visible(p[::-1])) for p in permutations(range(1, n + 1))]
    return _PERMS[n]


def latin(rng, n):
    """A uniformly shuffled random Latin square (flat list), by backtracking."""
    grid = [0] * (n * n)
    rows, cols = [0] * n, [0] * n

    def fill(i):
        if i == n * n:
            return True
        r, c = divmod(i, n)
        vals = list(range(1, n + 1))
        rng.shuffle(vals)
        for v in vals:
            bit = 1 << v
            if rows[r] & bit or cols[c] & bit:
                continue
            grid[i] = v
            rows[r] |= bit
            cols[c] |= bit
            if fill(i + 1):
                return True
            rows[r] ^= bit
            cols[c] ^= bit
        grid[i] = 0
        return False

    fill(0)
    return grid


def _lines(n):
    rows = [[r * n + c for c in range(n)] for r in range(n)]
    cols = [[r * n + c for r in range(n)] for c in range(n)]
    return rows + cols


def clues_of(n, sol):
    rows = [sol[r * n:(r + 1) * n] for r in range(n)]
    cols = [sol[c::n] for c in range(n)]
    return {
        "left": [visible(r) for r in rows],
        "right": [visible(r[::-1]) for r in rows],
        "top": [visible(k) for k in cols],
        "bottom": [visible(k[::-1]) for k in cols],
    }


def _propagate(n, lines, dom, cands):
    idx = range(n)
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
    return True


def count_solutions(n, top, bottom, left, right, givens, limit=2, out=None):
    """Count Latin squares matching the clues (0 = no clue) up to limit."""
    lines = _lines(n)
    full = (1 << n) - 1
    dom = [1 << (g - 1) if g else full for g in givens]
    starts = list(left) + list(top)
    ends = list(right) + list(bottom)
    cands = [[p for p, a, b in _perms(n)
              if (not starts[li] or a == starts[li])
              and (not ends[li] or b == ends[li])]
             for li in range(2 * n)]
    found = 0

    def search(dom, cands):
        nonlocal found
        if not _propagate(n, lines, dom, cands):
            return
        best, best_n = -1, n + 1
        for i, m in enumerate(dom):
            k = bin(m).count("1")
            if 1 < k < best_n:
                best, best_n = i, k
        if best < 0:
            found += 1
            if out is not None and found == 1:
                out[:] = [m.bit_length() for m in dom]
            return
        for v in range(n):
            bit = 1 << v
            if dom[best] & bit:
                d2 = list(dom)
                d2[best] = bit
                search(d2, list(cands))
                if found >= limit:
                    return

    search(dom, cands)
    return found


class Wolkenkrabbers(Game):
    key = "wolkenkrabbers"
    name = "Wolkenkrabbers"
    category = "logica"
    tagline = "Bouw een skyline en kijk wie achter wie verdwijnt."
    rules = [
        "In elk vakje staat een gebouw; het cijfer is de hoogte in "
        "verdiepingen.",
        "In elke rij en elke kolom komt elke hoogte precies één keer voor.",
        "Een cijfer buiten het rooster zegt hoeveel gebouwen je vanaf die "
        "kant ziet: hogere gebouwen verbergen de lagere erachter.",
    ]
    tips = [
        "Een 1 aan de rand betekent dat het hoogste gebouw er vlak naast "
        "staat.",
        "Staat het hoogste cijfer aan de rand, dan staan de gebouwen in die "
        "lijn netjes oplopend.",
    ]

    def generate(self, rng, level):
        n = SIZES[level]
        givens = [0] * (n * n)
        while True:                    # not every skyline is fixed by its views
            sol = latin(rng, n)
            clues = clues_of(n, sol)
            if count_solutions(n, clues["top"], clues["bottom"], clues["left"],
                               clues["right"], givens, 2) == 1:
                break
        slots = [(side, k) for side in ("top", "bottom", "left", "right")
                 for k in range(n)]
        rng.shuffle(slots)
        count = 4 * n
        for side, k in slots:
            if count <= KEEP[level]:
                break
            keep = clues[side][k]
            clues[side][k] = 0
            if count_solutions(n, clues["top"], clues["bottom"], clues["left"],
                               clues["right"], givens, 2) == 1:
                count -= 1
            else:
                clues[side][k] = keep
        return {"n": n, **clues, "givens": givens, "solution": sol}

    def verify(self, puz):
        n, sol = puz["n"], puz["solution"]
        assert len(sol) == n * n and len(puz["givens"]) == n * n
        for k in range(n):
            assert sorted(sol[k * n:(k + 1) * n]) == list(range(1, n + 1))
            assert sorted(sol[k::n]) == list(range(1, n + 1))
        true = clues_of(n, sol)
        for side in ("top", "bottom", "left", "right"):
            assert len(puz[side]) == n
            for k in range(n):
                assert puz[side][k] in (0, true[side][k])
        for i, g in enumerate(puz["givens"]):
            assert g in (0, sol[i])
        assert count_solutions(n, puz["top"], puz["bottom"], puz["left"],
                               puz["right"], puz["givens"], 2) == 1, \
            "skyscrapers must be unique"

    def instruction(self, puz, part=0):
        n = puz["n"]
        return (f"Plaats gebouwen van 1 tot {n} hoog. De cijfers rondom "
                "tellen hoeveel je er vanaf die kant ziet.")

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        g = Grid(box, n, n, max_cell=72, left=1, top=1, right=1, bottom=1)
        g.lines(c, lw=0.7, outer=min(2.4, max(1.0, g.cell * 0.06)))
        size = g.cell * 0.42
        off = g.cell * 0.4                # clue distance from the grid edge
        for k in range(n):
            for val, cx, cy in (
                    (puz["top"][k], g.cx(k), g.y(0) + off),
                    (puz["bottom"][k], g.cx(k), g.y(n) - off),
                    (puz["left"][k], g.x(0) - off, g.cy(k)),
                    (puz["right"][k], g.x(n) + off, g.cy(k))):
                if val:
                    text_mid(c, cx, cy, val, "SansB", size, INK)
        for i in range(n * n):
            r, col = divmod(i, n)
            if puz["givens"][i]:
                g.given(c, r, col, puz["givens"][i])
            elif solved:
                g.answer(c, r, col, puz["solution"][i])

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        base = cy - h
        w = s / 4
        for k, height in enumerate((0.55, 1.0, 0.35, 0.75)):
            x = cx - h + k * w
            line(c, x, base, x, base + s * height, 1.6, color, cap=2)
            line(c, x, base + s * height, x + w, base + s * height, 1.6,
                 color, cap=2)
            line(c, x + w, base + s * height, x + w, base, 1.6, color, cap=2)
        line(c, cx - h, base, cx + h, base, 1.8, color, cap=2)


GAME = Wolkenkrabbers()
