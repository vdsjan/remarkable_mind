"""Rekenpiramide - every brick is the sum of the two bricks below it."""
from fractions import Fraction
from math import comb

from ..draw import polyline, rrect, text_mid
from ..theme import INK, PEN
from .base import Game

# level -> (number of pyramids, base width, lowest and highest base value)
SETUP = {1: (2, 4, 1, 9), 2: (1, 5, 1, 12), 3: (1, 6, 2, 20)}
MAX_BOTTOM = {1: 2, 2: 2, 3: 2}     # givens allowed in the bottom row


def bricks(base):
    return [(r, i) for r in range(base) for i in range(base - r)]


def vector(base, r, i):
    """Brick (r, i) as a combination of the bottom-row values."""
    return [comb(r, j - i) if i <= j <= i + r else 0 for j in range(base)]


def solve_base(base, givens):
    """Solve the bottom row from givens [[r, i, value], ...].

    Returns the list of Fractions, or None when the givens do not pin down
    exactly one pyramid (rank below ``base`` or contradictory)."""
    rows = [[Fraction(v) for v in vector(base, r, i)] + [Fraction(val)]
            for r, i, val in givens]
    rank = 0
    for col in range(base):
        piv = next((k for k in range(rank, len(rows)) if rows[k][col]), None)
        if piv is None:
            return None
        rows[rank], rows[piv] = rows[piv], rows[rank]
        p = rows[rank][col]
        rows[rank] = [v / p for v in rows[rank]]
        for k in range(len(rows)):
            if k != rank and rows[k][col]:
                f = rows[k][col]
                rows[k] = [a - f * b for a, b in zip(rows[k], rows[rank])]
        rank += 1
    if any(row[-1] for row in rows[rank:]):
        return None
    return [rows[k][-1] for k in range(base)]


def build(bottom):
    rows = [list(bottom)]
    while len(rows[-1]) > 1:
        prev = rows[-1]
        rows.append([prev[k] + prev[k + 1] for k in range(len(prev) - 1)])
    return rows


def stepwise(base, cells):
    """Can the pyramid be completed with single add/subtract steps only?"""
    known = set(cells)
    changed = True
    while changed:
        changed = False
        for r in range(base - 1):
            for i in range(base - r - 1):
                trio = [(r + 1, i), (r, i), (r, i + 1)]
                have = [t for t in trio if t in known]
                if len(have) == 2:
                    known.update(trio)
                    changed = True
    return len(known) == base * (base + 1) // 2


def make_pyramid(rng, base, lo, hi, level):
    bottom = [rng.randint(lo, hi) for _ in range(base)]
    rows = build(bottom)
    cells = bricks(base)
    want_algebra = level == 3 and rng.random() < 0.5
    pick = None
    for attempt in range(3000):
        cand = rng.sample(cells, base)
        if sum(1 for r, _ in cand if r == 0) > MAX_BOTTOM[level]:
            continue
        if solve_base(base, [[r, i, rows[r][i]] for r, i in cand]) is None:
            continue
        easy = stepwise(base, cand)
        if level < 3 and not easy:
            continue
        if want_algebra and easy and attempt < 2000:
            continue
        pick = cand
        break
    if pick is None:                      # practically unreachable fallback
        pick = [(0, 0)] + [(1, i) for i in range(base - 1)]
    givens = [[r, i, rows[r][i]] for r, i in sorted(pick)]
    return {"base": base, "givens": givens, "solution": rows}


class Piramide(Game):
    key = "piramide"
    name = "Rekenpiramide"
    category = "getallen"
    tagline = "Stapel sommen tot de top klopt."
    rules = [
        "Elke steen is de som van de twee stenen waar hij op rust.",
        "Vul alle lege stenen in met positieve gehele getallen.",
        "Soms tel je op naar boven, soms trek je af naar beneden.",
    ]
    tips = [
        "Ken je een steen en één van de twee eronder? Trek af en je hebt de "
        "andere.",
        "Loop je vast, noem dan een lege steen x en reken door tot je een "
        "bekende steen bereikt.",
    ]

    def generate(self, rng, level):
        count, base, lo, hi = SETUP[level]
        return {"pyramids": [make_pyramid(rng, base, lo, hi, level)
                             for _ in range(count)]}

    def verify(self, puz):
        assert puz["pyramids"]
        for p in puz["pyramids"]:
            base, rows, givens = p["base"], p["solution"], p["givens"]
            assert [len(r) for r in rows] == list(range(base, 0, -1))
            for r in range(1, base):
                for i in range(base - r):
                    assert rows[r][i] == rows[r - 1][i] + rows[r - 1][i + 1]
            assert all(isinstance(v, int) and v > 0 for r in rows for v in r)
            assert len(givens) == base
            assert len({(r, i) for r, i, _ in givens}) == base
            assert any(r > 0 for r, _, _ in givens), "not all in bottom row"
            for r, i, val in givens:
                assert rows[r][i] == val
            bottom = solve_base(base, givens)
            assert bottom is not None, "givens must fix exactly one pyramid"
            assert all(v.denominator == 1 for v in bottom)
            assert [int(v) for v in bottom] == rows[0]

    def instruction(self, puz, part=0):
        return ("Vul de lege stenen in: elke steen is de som van de twee "
                "stenen eronder.")

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        pyramids = puz["pyramids"]
        gap = 26 if len(pyramids) > 1 else 0
        sub_h = (h - gap * (len(pyramids) - 1)) / len(pyramids)
        for k, p in enumerate(pyramids):
            top = y + h - k * (sub_h + gap)
            self._pyramid(c, (x, top - sub_h, w, sub_h), p, solved)

    def _pyramid(self, c, box, p, solved):
        x, y, w, h = box
        base = p["base"]
        bw = min(w / base, 84.0, h / base * 1.72)
        bh = bw / 1.72
        x0 = x + (w - bw * base) / 2
        y0 = y + (h - bh * base) / 2
        given = {(r, i): val for r, i, val in p["givens"]}
        inset = max(1.2, bw * 0.03)
        for r in range(base):
            for i in range(base - r):
                bx = x0 + i * bw + r * bw / 2
                by = y0 + r * bh
                rrect(c, bx + inset, by + inset, bw - 2 * inset,
                      bh - 2 * inset, bh * 0.14, stroke=INK,
                      lw=1.5 if bw > 40 else 1.0)
                cx, cy = bx + bw / 2, by + bh / 2
                if (r, i) in given:
                    text_mid(c, cx, cy, given[(r, i)], "SansS", bh * 0.44, INK)
                elif solved:
                    text_mid(c, cx, cy, p["solution"][r][i], "Hand",
                             bh * 0.62, PEN)

    def icon(self, c, cx, cy, s, color):
        bw, bh = s / 3, s / 3
        for r in range(3):
            for i in range(3 - r):
                bx = cx - s / 2 + i * bw + r * bw / 2
                by = cy - s / 2 + r * bh
                polyline(c, [(bx, by), (bx + bw, by), (bx + bw, by + bh),
                             (bx, by + bh)], 1.5, color, close=True)


GAME = Piramide()
