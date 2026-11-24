"""Eilandenrijk - Nurikabe: islands in one connected sea.

The solver works on bitmasks. A board of n x n cells is stored with one
padding column (width n + 1), so shifting a mask by 1 or by the width moves
every cell to a neighbour without wrapping around the edges.
"""
from .. import theme
from ..draw import Grid, circle, line, rrect, text, text_mid
from ..theme import GREY, INK, PEN, WHITE
from .base import Game

SIZES = {1: 5, 2: 6, 3: 7}
MAX_ISLAND = {1: 4, 2: 5, 3: 6}
SEA_SHARE = {1: (0.48, 0.64), 2: (0.50, 0.64), 3: (0.50, 0.64)}


def _bits(m):
    return bin(m).count("1")


class _Board:
    """Bitmask helpers for an n x n board."""

    def __init__(self, n):
        self.n = n
        self.w = w = n + 1
        self.full = sum(1 << (r * w + c) for r in range(n) for c in range(n))
        # top-left corners of all 2 x 2 blocks
        self.anchors = sum(1 << (r * w + c) for r in range(n - 1) for c in range(n - 1))

    def bit(self, r, c):
        return 1 << (r * self.w + c)

    def grow(self, m):
        w = self.w
        return (m | m << 1 | m >> 1 | m << w | m >> w) & self.full

    def flood(self, seed, allowed):
        f = seed & allowed
        while True:
            g = self.grow(f) & allowed
            if g == f:
                return f
            f = g

    def cells(self, m):
        w = self.w
        return [divmod(i, w) for i in range(self.n * w) if m >> i & 1]


def solve(n, clues, limit=2):
    """Count solutions: returns (list of sea masks as flat 0/1 lists, branches).

    clues: [[row, col, size], ...]. ``branches`` is the number of guesses the
    search needed; 0 means the puzzle falls to plain deduction."""
    b = _Board(n)
    w, full, anchors = b.w, b.full, b.anchors
    grow, flood = b.grow, b.flood
    nums = [(b.bit(r, c), k) for r, c, k in clues]
    numbits = 0
    for bit, _ in nums:
        numbits |= bit
    total = sum(k for _, k in nums)
    sols = []
    branches = 0

    def propagate(sea, land):
        """Deduce until nothing changes: (sea, land, frontier) or None."""
        while True:
            unknown = full & ~(sea | land)
            # no 2 x 2 block of sea
            if sea & sea >> 1 & sea >> w & sea >> (w + 1) & anchors:
                return None
            # the sea must be able to stay in one piece
            if sea:
                reach = flood(sea & -sea, full & ~land)
                if sea & ~reach:
                    return None
            n_land = _bits(land)
            if n_land > total or n_land + _bits(unknown) < total:
                return None
            new_sea = new_land = 0
            comps = []
            allcomp = 0
            for bit, k in nums:
                comp = flood(bit, land)
                if comp & numbits & ~bit:        # two numbers on one island
                    return None
                if _bits(comp) > k:
                    return None
                comps.append(comp)
                allcomp |= comp
            orphan = land & ~allcomp             # land not yet tied to a number
            claimed = 0
            once = twice = 0
            frontier = 0
            for (bit, k), comp in zip(nums, comps):
                size = _bits(comp)
                ring = grow(comp) & ~comp
                twice |= once & ring
                once |= ring
                if size == k:                    # finished: surrounded by sea
                    new_sea |= ring & unknown
                    claimed |= comp
                    continue
                frontier |= ring & unknown
                # cells this island could still reach with its spare cells
                allowed = full & ~(sea | grow(allcomp & ~comp))
                pot = comp
                for _ in range(k - size):
                    nxt = grow(pot) & allowed | comp
                    if nxt == pot:
                        break
                    pot = nxt
                if _bits(pot) < k:
                    return None
                if _bits(pot) == k:
                    new_land |= pot & unknown
                claimed |= pot
            if orphan & ~claimed or twice & land:
                return None
            new_sea |= unknown & ~claimed        # no island reaches this cell
            new_sea |= twice & unknown           # would join two islands
            # three sea cells of a 2 x 2 block force the fourth to be land
            s = sea
            new_land |= unknown & s >> 1 & s >> w & s >> (w + 1) & anchors
            new_land |= (s & unknown >> 1 & s >> w & s >> (w + 1) & anchors) << 1
            new_land |= (s & s >> 1 & unknown >> w & s >> (w + 1) & anchors) << w
            new_land |= (s & s >> 1 & s >> w & unknown >> (w + 1) & anchors) << (w + 1)
            if n_land == total:
                new_sea |= unknown
            elif n_land + _bits(unknown) == total:
                new_land |= unknown
            new_sea &= ~sea
            new_land &= ~land
            if new_sea & new_land:
                return None
            if not (new_sea | new_land):
                return sea, land, frontier
            sea |= new_sea
            land |= new_land

    def search(sea, land):
        nonlocal branches
        res = propagate(sea, land)
        if res is None:
            return
        sea, land, frontier = res
        unknown = full & ~(sea | land)
        if not unknown:
            sols.append(sea)
            return
        branches += 1
        pick = frontier or unknown
        pick &= -pick
        search(sea, land | pick)
        if len(sols) >= limit:
            return
        search(sea | pick, land)

    search(0, numbits)
    flat = [[1 if s >> (r * w + c) & 1 else 0 for r in range(n) for c in range(n)]
            for s in sols]
    return flat, branches


def _components(n, cells):
    """Orthogonally connected groups of the given set of (r, c) cells."""
    left = set(cells)
    out = []
    while left:
        start = left.pop()
        comp, stack = [start], [start]
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in left:
                    left.remove(nb)
                    comp.append(nb)
                    stack.append(nb)
        out.append(sorted(comp))
    return out


def _square(sea, r, c):
    """Would (r, c) complete a 2 x 2 block of sea?"""
    for dr in (-1, 0):
        for dc in (-1, 0):
            if all((r + dr + a, c + dc + b) in sea or (a == -dr and b == -dc)
                   for a in (0, 1) for b in (0, 1)):
                return True
    return False


def _layout(rng, n, max_island, share):
    """A random sea: connected, without 2 x 2 blocks, leaving small islands.

    Returns (sea set, islands) or None when the walk gets stuck."""
    every = [(r, c) for r in range(n) for c in range(n)]
    sea = {rng.choice(every)}
    lo, hi = share
    target = rng.uniform(lo, hi) * n * n
    while True:
        land = [p for p in every if p not in sea]
        islands = _components(n, land)
        big = [isl for isl in islands if len(isl) > max_island]
        if not big and len(sea) >= target:
            return sea, islands
        if len(sea) > hi * n * n + 1:
            return None
        pool = [p for isl in big for p in isl] if big else land
        cands = [(r, c) for r, c in pool
                 if any(nb in sea for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
                 and not _square(sea, r, c)]
        if not cands:
            return None
        sea.add(rng.choice(cands))


class Eilandenrijk(Game):
    key = "eilandenrijk"
    name = "Eilandenrijk"
    category = "logica"
    tagline = "Kleur de zee in en laat een landkaart ontstaan."
    rules = [
        "Kleur vakjes in tot zee. Elk getal ligt op een eiland van precies "
        "zoveel vakjes, en op elk eiland ligt precies één getal.",
        "Eilanden raken elkaar nooit langs een zijde; schuin mag wel.",
        "De zee is één aaneengesloten geheel en vult nergens een blok van "
        "2 × 2 vakjes.",
    ]
    tips = [
        "Een 1 is meteen klaar: de vier vakjes ernaast zijn zee. Ook een "
        "vakje tussen twee getallen is altijd zee.",
        "Zet een stip in vakjes die zeker land zijn. Dreigt er een blok van "
        "2 × 2 zee, dan is het vierde vakje land.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n = SIZES[level]
        best = None
        for attempt in range(3000):
            made = _layout(rng, n, MAX_ISLAND[level], SEA_SHARE[level])
            if made is None:
                continue
            sea, islands = made
            sizes = [len(isl) for isl in islands]
            # a map worth drawing: several islands, not too many single cells
            if len(islands) < n - 2 or sizes.count(1) > 2 or max(sizes) < 3:
                continue
            clues = sorted([*rng.choice(isl), len(isl)] for isl in islands)
            sols, branches = solve(n, clues, 2)
            if len(sols) != 1:
                continue
            puz = {"n": n, "clues": clues,
                   "sea": [1 if (r, c) in sea else 0 for r in range(n) for c in range(n)]}
            # level 1 falls to plain deduction; level 3 asks for a real think
            if level == 1 and branches > 0:
                best = best or puz
                continue
            if level == 3 and branches == 0 and attempt < 400:
                best = best or puz
                continue
            return puz
        assert best is not None, "could not generate a unique island map"
        return best

    def verify(self, puz):
        n, clues, sea = puz["n"], puz["clues"], puz["sea"]
        assert len(sea) == n * n and set(sea) <= {0, 1}
        water = {(r, c) for r in range(n) for c in range(n) if sea[r * n + c]}
        land = {(r, c) for r in range(n) for c in range(n)} - water
        at = {(r, c): k for r, c, k in clues}
        assert len(at) == len(clues), "two numbers on one cell"
        assert water, "there must be a sea"
        assert len(_components(n, water)) == 1, "the sea is not connected"
        for r in range(n - 1):
            for c in range(n - 1):
                assert not all((r + a, c + b) in water for a in (0, 1) for b in (0, 1)), \
                    "a 2 x 2 block of sea"
        islands = _components(n, land)
        assert len(islands) == len(clues), "islands and numbers do not match"
        for isl in islands:
            nums = [at[p] for p in isl if p in at]
            assert len(nums) == 1, "an island needs exactly one number"
            assert nums[0] == len(isl), "island size differs from its number"
        sols, _ = solve(n, clues, 2)
        assert len(sols) == 1, "island map must be unique"
        assert sols[0] == sea, "stored solution differs from solver"

    def instruction(self, puz, part=0):
        return ("Kleur de zee in: elk getal telt de vakjes van zijn eiland, en "
                "de zee blijft één geheel zonder blok van 2 × 2.")

    @staticmethod
    def _water(c, x, y, s):
        """Shade one sea cell: a light wash with pen strokes over it."""
        r, g, b = PEN.rgb()
        k = 0.80                                  # mostly paper, a little ink
        c.saveState()
        c.setFillColorRGB(r + (1 - r) * k, g + (1 - g) * k, b + (1 - b) * k)
        c.rect(x, y, s, s, stroke=0, fill=1)
        c.setStrokeColor(PEN)
        c.setLineWidth(max(0.7, s * 0.028))
        c.setLineCap(1)
        d = s / 4
        t = d / 2
        while t < 2 * s:                          # diagonal hatching, clipped
            c.line(x + max(0.0, t - s), y + min(t, s), x + min(t, s), y + max(0.0, t - s))
            t += d
        c.restoreState()

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        g = Grid(box, n, n, max_cell=62)
        if solved:
            for i, v in enumerate(puz["sea"]):
                if v:
                    r, col = divmod(i, n)
                    x, y, s, _ = g.rect(r, col)
                    self._water(c, x, y, s)
        g.lines(c, lw=0.7, outer=2.2)
        for r, col, k in puz["clues"]:
            if solved:                            # keep the number readable
                circle(c, g.cx(col), g.cy(r), g.cell * 0.30, fill=WHITE, stroke=None)
            text_mid(c, g.cx(col), g.cy(r), k, "SansB", g.cell * 0.50, INK)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        q = s / 3
        c.saveState()
        c.setFillColor(color)
        for r, col in ((0, 0), (0, 1), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2)):
            c.rect(cx - h + col * q, cy + h - (r + 1) * q, q, q, stroke=0, fill=1)
        c.restoreState()
        for k in range(4):
            line(c, cx - h + k * q, cy - h, cx - h + k * q, cy + h, 1.1, color, cap=2)
            line(c, cx - h, cy - h + k * q, cx + h, cy - h + k * q, 1.1, color, cap=2)
        text_mid(c, cx - q, cy, "2", "SansB", q * 0.8, color)


GAME = Eilandenrijk()
