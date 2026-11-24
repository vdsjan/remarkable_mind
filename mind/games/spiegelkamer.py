"""Spiegelkamer - bend a beam of light with a fixed number of mirrors.

A room is an n x n grid. A lamp on the wall shoots a beam into the room; the
beam travels straight, is turned a quarter by diagonal mirrors ("/" or "\\")
and is stopped by pillars. The player draws exactly ``k`` extra mirrors so
that the beam passes every gem and leaves the room through the exit. Every
drawn mirror has to be hit, which makes the set of mirrors well defined, and
the generator only keeps rooms where exactly one set works.

Coordinates are (row, col) with row 0 at the top. Directions are numbered
0 = up, 1 = right, 2 = down, 3 = left.
"""
import math

from ..draw import Grid, circle, line, polyline, text_mid
from ..theme import INK, MUSTARD, PEN, TEAL, WHITE
from .base import Game

STEP = ((-1, 0), (0, 1), (1, 0), (0, -1))
TURN = {"/": (1, 0, 3, 2), "\\": (3, 2, 1, 0)}
# level -> (size, mirrors to draw, fixed mirrors, gems, pillars)
LEVELS = {
    1: (5, 2, (0, 0), (2, 2), (0, 1)),
    2: (6, 3, (0, 0), (3, 3), (1, 2)),
    3: (7, 4, (1, 2), (3, 4), (2, 3)),
}


# --- the beam -------------------------------------------------------------------
def trace(n, src, mirrors, pillars):
    """Follow the beam. Returns (cells in order, outcome) where outcome is
    ("out", r, c, d) when the beam leaves the room from cell (r, c) going d,
    ("stop",) at a pillar and ("loop",) when it runs in circles."""
    r, c, d = src
    seen, cells = set(), []
    while 0 <= r < n and 0 <= c < n:
        if (r, c) in pillars:
            return cells, ("stop",)
        if (r, c, d) in seen:
            return cells, ("loop",)
        seen.add((r, c, d))
        cells.append((r, c))
        m = mirrors.get((r, c))
        if m:
            d = TURN[m][d]
        r, c = r + STEP[d][0], c + STEP[d][1]
    return cells, ("out", r - STEP[d][0], c - STEP[d][1], d)


def solutions(n, src, exit_, gems, fixed, pillars, k, limit=2):
    """All ways (up to ``limit``) to draw exactly k mirrors, each hit by the
    beam, so that the beam passes every gem and leaves through the exit.

    The search walks along the beam. The first time the beam enters an empty
    cell it either passes, or - while mirrors are left - meets a new "/" or
    "\\". A cell the beam crosses again keeps what was decided for it."""
    gems, pillars = set(gems), set(pillars)
    state = dict(fixed)                     # (r, c) -> mirror
    passed = set()                          # empty cells the beam went through
    placed = []
    found = []
    ex = tuple(exit_)

    def walk(r, c, d, left, seen, got):
        while True:
            if not (0 <= r < n and 0 <= c < n):
                pr, pc = r - STEP[d][0], c - STEP[d][1]
                if left == 0 and got == len(gems) and (pr, pc, d) == ex:
                    found.append(sorted(placed))
                return
            cell = (r, c)
            if cell in pillars or (r, c, d) in seen:
                return
            seen = seen | {(r, c, d)}
            m = state.get(cell)
            if m:
                d = TURN[m][d]
            elif cell in gems:
                if not any(s[0] == r and s[1] == c for s in seen if s != (r, c, d)):
                    got += 1
            elif cell not in passed:
                passed.add(cell)            # option 1: nothing here
                walk(r + STEP[d][0], c + STEP[d][1], d, left, seen, got)
                passed.discard(cell)
                if left and len(found) < limit:
                    for m in "/\\":         # option 2 and 3: a new mirror
                        state[cell] = m
                        placed.append([r, c, m])
                        nd = TURN[m][d]
                        walk(r + STEP[nd][0], c + STEP[nd][1], nd, left - 1, seen, got)
                        placed.pop()
                        del state[cell]
                        if len(found) >= limit:
                            break
                return
            r, c = r + STEP[d][0], c + STEP[d][1]

    walk(src[0], src[1], src[2], k, frozenset(), 0)
    return found


def edge_of(n, r, c, d):
    """Side of the room ("t", "r", "b", "l") a beam going d crosses at (r, c)."""
    return "trbl"[d]


class Spiegelkamer(Game):
    key = "spiegelkamer"
    name = "Spiegelkamer"
    category = "ruimte"
    tagline = "Stuur de lichtstraal met spiegels langs alle edelstenen naar buiten."
    rules = [
        "De lichtstraal vertrekt bij de lamp en gaat rechtdoor. Een schuine "
        "spiegel kaatst haar een kwartslag weg; een pilaar (gevuld vakje) houdt haar tegen.",
        "Teken het gevraagde aantal schuine spiegels in lege vakjes, zodat de "
        "straal langs alle edelstenen loopt en de kamer verlaat bij UIT.",
        "Elke spiegel die je tekent moet door de straal geraakt worden.",
    ]
    tips = [
        "Redeneer ook terug vanaf UIT: uit welke richting moet de straal daar aankomen?",
        "Een edelsteen die niet op de rechte lijn van de lamp ligt, verraadt waar de straal moet afbuigen.",
    ]
    counts = (9, 8, 8)

    # -- generation -------------------------------------------------------------
    def generate(self, rng, level):
        n, k, n_fixed, n_gems, n_pillars = LEVELS[level]
        for _ in range(4000):
            puz = self._attempt(rng, n, k, rng.randint(*n_fixed), rng.randint(*n_gems),
                                rng.randint(*n_pillars))
            if puz:
                return puz
        raise AssertionError("could not generate a unique Spiegelkamer puzzle")

    def _attempt(self, rng, n, k, n_fixed, n_gems, n_pillars):
        total = k + n_fixed
        side, pos = rng.randrange(4), rng.randrange(n)
        src = [(0, pos, 2), (pos, n - 1, 3), (n - 1, pos, 0), (pos, 0, 1)][side]
        # a random beam: drop mirrors on fresh cells along the way
        mirrors, order, seen, crossed = {}, [], set(), []
        r, c, d = src
        run = 0                                     # straight cells since the last turn
        while 0 <= r < n and 0 <= c < n:
            if (r, c, d) in seen:
                return None
            seen.add((r, c, d))
            cell = (r, c)
            m = mirrors.get(cell)
            if m is None and cell not in crossed and len(mirrors) < total and run >= 1 \
                    and rng.random() < 0.34:
                m = mirrors[cell] = rng.choice("/\\")
                order.append(cell)
            if m:
                d = TURN[m][d]
                run = 0
            else:
                if cell not in crossed:
                    crossed.append(cell)
                run += 1
            if cell in mirrors and cell in crossed:
                return None                         # a mirror on an already used cell
            r, c = r + STEP[d][0], c + STEP[d][1]
        if len(mirrors) < total or len(crossed) < n_gems + 2:
            return None
        exit_ = (r - STEP[d][0], c - STEP[d][1], d)
        src_edge = ("trbl"[(src[2] + 2) % 4], src[0], src[1])
        if (edge_of(n, *exit_), exit_[0], exit_[1]) == src_edge:
            return None                             # lamp and exit in the same gap
        cells, outcome = trace(n, src, mirrors, set())
        if outcome != ("out",) + exit_ or len(set(cells)) < n + k:
            return None
        # gems: spread over the straight stretches of the beam
        stretches, cur = [], []
        for cell in cells:
            if cell in mirrors:
                if cur:
                    stretches.append(cur)
                cur = []
            elif cell not in cur:
                cur.append(cell)
        if cur:
            stretches.append(cur)
        rng.shuffle(stretches)
        gems = []
        for stretch in stretches * 2:
            free = [x for x in stretch if x not in gems]
            if free and len(gems) < n_gems:
                gems.append(rng.choice(free))
        if len(gems) < n_gems:
            return None
        used = set(cells)
        spare = [(a, b) for a in range(n) for b in range(n) if (a, b) not in used]
        if len(spare) < n_pillars:
            return None
        pillars = rng.sample(spare, n_pillars)
        fixed_cells = rng.sample(order, n_fixed)
        fixed = {cell: mirrors[cell] for cell in fixed_cells}
        answer = sorted([a, b, m] for (a, b), m in mirrors.items() if (a, b) not in fixed)
        found = solutions(n, src, exit_, gems, fixed, pillars, k, 2)
        if found != [answer]:
            return None
        return {"n": n, "k": k, "src": list(src), "exit": list(exit_),
                "gems": sorted([a, b] for a, b in gems),
                "fixed": sorted([a, b, m] for (a, b), m in fixed.items()),
                "pillars": sorted([a, b] for a, b in pillars),
                "mirrors": answer}

    # -- checking ---------------------------------------------------------------
    @staticmethod
    def _parts(puz):
        gems = [tuple(g) for g in puz["gems"]]
        fixed = {(a, b): m for a, b, m in puz["fixed"]}
        pillars = {tuple(p) for p in puz["pillars"]}
        return tuple(puz["src"]), tuple(puz["exit"]), gems, fixed, pillars

    def verify(self, puz):
        n, k = puz["n"], puz["k"]
        src, exit_, gems, fixed, pillars = self._parts(puz)
        assert len(puz["mirrors"]) == k >= 1
        cells_in = lambda a, b: 0 <= a < n and 0 <= b < n
        taken = set(gems) | set(fixed) | pillars
        assert len(taken) == len(gems) + len(fixed) + len(pillars), "objects overlap"
        assert all(cells_in(a, b) for a, b in taken)
        # the lamp stands on the wall its beam comes from, the exit on its own wall
        r, c, d = src
        assert cells_in(r, c) and not cells_in(r - STEP[d][0], c - STEP[d][1])
        r, c, d = exit_
        assert cells_in(r, c) and not cells_in(r + STEP[d][0], c + STEP[d][1])
        mirrors = dict(fixed)
        for a, b, m in puz["mirrors"]:
            assert m in TURN and cells_in(a, b) and (a, b) not in taken
            assert (a, b) not in mirrors, "two mirrors in one cell"
            mirrors[(a, b)] = m
        cells, outcome = trace(n, src, mirrors, pillars)
        assert outcome == ("out",) + exit_, "the beam must leave through the exit"
        hit = set(cells)
        assert all(g in hit for g in gems), "the beam must pass every gem"
        assert all((a, b) in hit for a, b, _ in puz["mirrors"]), "every mirror is hit"
        found = solutions(n, src, exit_, gems, fixed, pillars, k, 2)
        assert found == [sorted(puz["mirrors"])], "the mirrors must be the only solution"

    def instruction(self, puz, part=0):
        k = puz["k"]
        return (f"Teken precies {k} spiegels zodat de lichtstraal langs alle "
                "edelstenen loopt en de kamer verlaat bij UIT.")

    # -- drawing ------------------------------------------------------------------
    @staticmethod
    def _mirror(c, g, r, col, m, color, lw):
        x0, x1 = g.x(col) + g.cell * 0.14, g.x(col + 1) - g.cell * 0.14
        yt, yb = g.y(r) - g.cell * 0.14, g.y(r + 1) + g.cell * 0.14
        if m == "/":
            line(c, x0, yb, x1, yt, lw, color)
        else:
            line(c, x0, yt, x1, yb, lw, color)

    @staticmethod
    def _arrow(c, x, y, dx, dy, length, color, lw):
        """Arrow from (x, y) along the unit vector (dx, dy)."""
        x2, y2 = x + dx * length, y + dy * length
        line(c, x, y, x2, y2, lw, color)
        h = max(4.0, length * 0.34)
        px, py = -dy, dx
        polyline(c, [(x2 - dx * h + px * h * 0.55, y2 - dy * h + py * h * 0.55), (x2, y2),
                     (x2 - dx * h - px * h * 0.55, y2 - dy * h - py * h * 0.55)], lw, color)

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        src, exit_, gems, fixed, pillars = self._parts(puz)
        g = Grid(box, n, n, max_cell=56, left=0.95, top=0.95, right=0.95, bottom=0.95)
        s = g.cell
        g.lines(c, lw=0.7, outer=2.4)

        def edge_point(r, col, d, out):
            """Point `out` cells outside the wall that a beam going d crosses."""
            dr, dc = STEP[d]
            return (g.cx(col) + dc * s * (0.5 + out), g.cy(r) - dr * s * (0.5 + out))

        def gap(r, col, d):
            (x, y), (dr, dc) = edge_point(r, col, d, 0), STEP[d]
            h = s * 0.5 - 1.6
            line(c, x - abs(dr) * h, y - abs(dc) * h, x + abs(dr) * h, y + abs(dc) * h,
                 4.2, WHITE, cap=0)

        # the lamp: an opening in the wall, a lamp outside and an arrow going in
        sr, sc, sd = src
        back = (sd + 2) % 4
        gap(sr, sc, back)
        lx, ly = edge_point(sr, sc, back, 0.56)
        dr, dc = STEP[sd]
        for k in range(8):                                  # rays around the lamp
            a = k * math.pi / 4
            line(c, lx + math.cos(a) * s * 0.2, ly + math.sin(a) * s * 0.2,
                 lx + math.cos(a) * s * 0.29, ly + math.sin(a) * s * 0.29, 1.0, INK)
        circle(c, lx, ly, s * 0.15, fill=MUSTARD, stroke=INK, lw=1.2)
        self._arrow(c, lx + dc * s * 0.24, ly - dr * s * 0.24, dc, -dr, s * 0.3, INK, 1.6)

        # the exit: an opening with an arrow going out and the word UIT
        er, ec, ed = exit_
        gap(er, ec, ed)
        ex, ey = edge_point(er, ec, ed, 0.06)
        dr, dc = STEP[ed]
        self._arrow(c, ex, ey, dc, -dr, s * 0.36, INK, 1.6)
        size = max(7.5, min(10.5, s * 0.23))
        if ed in (1, 3):                                    # text sits beyond the arrow
            tx = ex + dc * (s * 0.36 + size * 1.25)
            text_mid(c, tx, ey, "UIT", "SansB", size, INK)
        else:
            text_mid(c, ex, ey - dr * (s * 0.36 + size * 0.85), "UIT", "SansB", size, INK)

        for r, col in pillars:
            x, y, _, _ = g.rect(r, col)
            c.saveState()
            c.setFillColor(INK)
            c.roundRect(x + s * 0.13, y + s * 0.13, s * 0.74, s * 0.74, s * 0.1, stroke=0, fill=1)
            c.restoreState()
        for r, col in gems:
            cx, cy, q = g.cx(col), g.cy(r), s * 0.21
            polyline(c, [(cx, cy + q * 1.15), (cx + q, cy + q * 0.25), (cx, cy - q * 1.15),
                         (cx - q, cy + q * 0.25)], lw=1.2, color=INK, close=True, fill=TEAL)
            polyline(c, [(cx - q, cy + q * 0.25), (cx + q, cy + q * 0.25)], lw=0.8, color=INK)
        fixed_lw = max(2.8, s * 0.085)
        for (r, col), m in fixed.items():
            self._mirror(c, g, r, col, m, INK, fixed_lw)

        if solved:
            mirrors = dict(fixed)
            mirrors.update({(a, b): m for a, b, m in puz["mirrors"]})
            cells, _ = trace(n, src, mirrors, pillars)
            pts = [edge_point(sr, sc, back, 0.0)]
            pts += [(g.cx(col), g.cy(r)) for r, col in cells]
            pts.append(edge_point(er, ec, ed, 0.3))
            polyline(c, pts, lw=max(1.5, s * 0.04), color=PEN, join=0)
            for a, b, m in puz["mirrors"]:
                self._mirror(c, g, a, b, m, PEN, fixed_lw + 0.8)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        polyline(c, [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)],
                 lw=1.4, color=color, close=True)
        line(c, cx - h * 0.1, cy - h * 0.75, cx + h * 0.7, cy + h * 0.05, 2.4, color)
        polyline(c, [(cx - h, cy + h * 0.35), (cx + h * 0.3, cy + h * 0.35),
                     (cx + h * 0.3, cy - h * 0.35), (cx + h * 0.3, cy - h)],
                 lw=1.1, color=color)
        line(c, cx + h * 0.3, cy - h * 0.35, cx + h * 0.3, cy - h * 0.35, 1.1, color)


GAME = Spiegelkamer()
