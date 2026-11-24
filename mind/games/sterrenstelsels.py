"""Sterrenstelsels - cut the grid into regions that are symmetric around a dot.

Puzzle dict:
    n         grid size
    dots      [[y, x], ...] in half-cell coordinates: the centre of cell
              (r, c) is (2r + 1, 2c + 1), so even values lie on grid lines
    regions   n x n grid; regions[r][c] = index of the dot that owns the cell
"""
from .. import theme
from ..draw import Grid, circle, line, polyline, rrect
from ..theme import GREY, INK, PEN, WHITE
from .base import Game

# level -> grid size and the range of region sizes the generator aims for
SIZES = {1: (5, 2, 6), 2: (7, 2, 9), 3: (9, 3, 12)}
SIZES_COMPACT = {1: (5, 2, 6), 2: (6, 2, 8), 3: (7, 3, 10)}
CANDIDATES = {1: 2, 2: 3, 3: 3}       # unique puzzles to choose from, per level
DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def core_cells(dot):
    """The 1, 2 or 4 cells that touch a dot."""
    y, x = dot
    rows = [(y - 1) // 2] if y % 2 else [y // 2 - 1, y // 2]
    cols = [(x - 1) // 2] if x % 2 else [x // 2 - 1, x // 2]
    return [(r, c) for r in rows for c in cols]


def mirror(dot, r, c):
    """The cell that (r, c) lands on after a half turn around the dot."""
    return dot[0] - r - 1, dot[1] - c - 1


# --- solver -------------------------------------------------------------------
def count_solutions(n, dots, limit=2, out=None):
    """Count the valid divisions. Every cell keeps a bit set of dots it may
    still belong to; three rules shrink the sets until they stop changing:

    * a cell can only belong to a dot if its mirror cell can too,
    * a decided cell decides its mirror cell,
    * a cell must be reachable from the dot through cells of that dot.
    """
    N, K = n * n, len(dots)
    mir = []
    for d in dots:
        row = []
        for i in range(N):
            r, c = mirror(d, i // n, i % n)
            row.append(r * n + c if 0 <= r < n and 0 <= c < n else -1)
        mir.append(row)
    forced = [-1] * N
    cores = []
    for k, d in enumerate(dots):
        cells = [r * n + c for r, c in core_cells(d)]
        for i in cells:
            if forced[i] != -1:
                return 0                      # two dots claim the same cell
            forced[i] = k
        cores.append(cells)
    nbrs = [[(r + dr) * n + c + dc for dr, dc in DIRS
             if 0 <= r + dr < n and 0 <= c + dc < n]
            for r in range(n) for c in range(n)]
    cand = []
    for i in range(N):
        if forced[i] >= 0:
            cand.append(1 << forced[i])
        else:
            m = 0
            for k in range(K):
                j = mir[k][i]
                if j >= 0 and forced[j] in (-1, k):
                    m |= 1 << k
            cand.append(m)
    found = 0

    def propagate(cand):
        changed = True
        while changed:
            changed = False
            for i in range(N):
                m = cand[i]
                bits = m
                while bits:
                    b = bits & -bits
                    bits ^= b
                    j = mir[b.bit_length() - 1][i]
                    if j < 0 or not cand[j] & b:
                        m ^= b
                if m != cand[i]:
                    cand[i] = m
                    changed = True
                if m == 0:
                    return False
                if m & (m - 1) == 0:
                    j = mir[m.bit_length() - 1][i]
                    if cand[j] != m:
                        cand[j] = m
                        changed = True
            for k in range(K):
                b = 1 << k
                seen = set(cores[k])
                stack = list(cores[k])
                while stack:
                    i = stack.pop()
                    for j in nbrs[i]:
                        if j not in seen and cand[j] & b:
                            seen.add(j)
                            stack.append(j)
                for i in range(N):
                    if cand[i] & b and i not in seen:
                        cand[i] ^= b
                        changed = True
                        if cand[i] == 0:
                            return False
        return True

    def search(cand):
        nonlocal found
        if not propagate(cand):
            return
        best, best_n = -1, 99
        for i in range(N):
            m = cand[i]
            if m & (m - 1):
                cnt = bin(m).count("1")
                if cnt < best_n:
                    best, best_n = i, cnt
        if best < 0:
            found += 1
            if out is not None and found == 1:
                out[:] = [[cand[r * n + c].bit_length() - 1 for c in range(n)]
                          for r in range(n)]
            return
        bits = cand[best]
        while bits:
            b = bits & -bits
            bits ^= b
            nxt = cand[:]
            nxt[best] = b
            search(nxt)
            if found >= limit:
                return

    search(cand)
    return found


# --- generator ----------------------------------------------------------------
def random_division(rng, n, lo, hi):
    """Grow random symmetric regions until the grid is full.

    Returns (dots, owner) or None when too many one-cell regions are left."""
    owner = [[-1] * n for _ in range(n)]
    positions = [(y, x) for y in range(1, 2 * n) for x in range(1, 2 * n)]
    rng.shuffle(positions)
    dots = []
    singles = 0
    for dot in positions:
        cells = core_cells(dot)
        if any(owner[r][c] != -1 for r, c in cells):
            continue
        k = len(dots)
        for r, c in cells:
            owner[r][c] = k
        region = list(cells)
        target = rng.randint(lo, hi)
        while len(region) < target:
            options = set()
            for r, c in region:
                for dr, dc in DIRS:
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < n and 0 <= c2 < n and owner[r2][c2] == -1:
                        r3, c3 = mirror(dot, r2, c2)
                        if 0 <= r3 < n and 0 <= c3 < n and owner[r3][c3] == -1:
                            options.add((r2, c2))
            if not options:
                break
            r2, c2 = rng.choice(sorted(options))
            for cell in {(r2, c2), mirror(dot, r2, c2)}:
                owner[cell[0]][cell[1]] = k
                region.append(cell)
        singles += len(region) == 1
        dots.append(dot)
    if singles > max(1, n * n // 14):
        return None
    return dots, owner


class Sterrenstelsels(Game):
    key = "sterrenstelsels"
    name = "Sterrenstelsels"
    category = "ruimte"
    tagline = "Elk stelsel draait om zijn eigen ster."
    rules = [
        "Verdeel het rooster langs de lijnen in gebieden; elk vakje hoort bij "
        "precies één gebied.",
        "Elk gebied bevat precies één stip, en die ligt in het midden ervan.",
        "Draai je een gebied een halve slag om zijn stip, dan past het precies "
        "op zichzelf.",
    ]
    tips = [
        "De vakjes die een stip raken horen er zeker bij. Trek daar eerst de "
        "grenzen tussen buren met een andere stip.",
        "Hoort een vakje bij een stip, dan ook het vakje recht tegenover die stip.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n, lo, hi = (SIZES_COMPACT if theme.COMPACT else SIZES)[level]
        # of a few unique candidates keep the one with the fewest dots: larger
        # regions give more surprising shapes and a harder puzzle
        best, unique = None, 0
        for _ in range(100000):
            made = random_division(rng, n, lo, hi)
            if made is None or count_solutions(n, made[0], 2) != 1:
                continue
            if best is None or len(made[0]) < len(best[0]):
                best = made
            unique += 1
            if unique == CANDIDATES[level]:
                break
        else:
            raise AssertionError("could not generate a unique Sterrenstelsels puzzle")
        dots, owner = best
        order = sorted(range(len(dots)), key=lambda k: dots[k])
        rank = {k: i for i, k in enumerate(order)}
        return {"n": n, "dots": [list(dots[k]) for k in order],
                "regions": [[rank[k] for k in row] for row in owner]}

    def verify(self, puz):
        n, dots, regions = puz["n"], puz["dots"], puz["regions"]
        assert len(regions) == n and all(len(row) == n for row in regions)
        assert len({tuple(d) for d in dots}) == len(dots)
        cells = {k: [] for k in range(len(dots))}
        for r in range(n):
            for c in range(n):
                cells[regions[r][c]].append((r, c))
        for k, dot in enumerate(dots):
            assert 1 <= dot[0] <= 2 * n - 1 and 1 <= dot[1] <= 2 * n - 1
            mine = set(cells[k])
            assert mine, "every dot owns a region"
            assert set(core_cells(dot)) <= mine, "the dot lies inside its region"
            for r, c in mine:
                assert mirror(dot, r, c) in mine, "region is not symmetric"
            start = core_cells(dot)[0]
            seen, stack = {start}, [start]
            while stack:
                r, c = stack.pop()
                for dr, dc in DIRS:
                    nb = (r + dr, c + dc)
                    if nb in mine and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
            assert seen == mine, "region is not connected"
        assert count_solutions(n, dots, 2) == 1, "Sterrenstelsels must be unique"

    def instruction(self, puz, part=0):
        return ("Verdeel het rooster in gebieden met elk één stip in het midden; "
                "na een halve draai past elk gebied op zichzelf.")

    # -- drawing -----------------------------------------------------------------
    def draw(self, c, box, puz, solved=False, part=0):
        n, regions = puz["n"], puz["regions"]
        g = Grid(box, n, n, max_cell=62)
        for i in range(1, n):
            line(c, g.x(i), g.y(0), g.x(i), g.y(n), 0.5, GREY)
            line(c, g.x(0), g.y(i), g.x(n), g.y(i), 0.5, GREY)
        if solved:
            lw = max(2.2, g.cell * 0.075)
            c.saveState()                        # keep line ends inside the frame
            clip = c.beginPath()
            clip.rect(g.x(0), g.y(n), g.w, g.h)
            c.clipPath(clip, stroke=0, fill=0)
            for r in range(n):
                for col in range(n):
                    if col + 1 < n and regions[r][col] != regions[r][col + 1]:
                        line(c, g.x(col + 1), g.y(r), g.x(col + 1), g.y(r + 1), lw, PEN)
                    if r + 1 < n and regions[r][col] != regions[r + 1][col]:
                        line(c, g.x(col), g.y(r + 1), g.x(col + 1), g.y(r + 1), lw, PEN)
            c.restoreState()
        rrect(c, g.x(0), g.y(n), g.w, g.h, 0, stroke=INK, lw=2.2)
        rad = max(3.2, g.cell * 0.13)
        for y, x in puz["dots"]:
            circle(c, g.x0 + x * g.cell / 2, g.ytop - y * g.cell / 2, rad,
                   fill=WHITE, stroke=INK, lw=1.5)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        rrect(c, cx - h, cy - h, s, s, s * 0.08, stroke=color, lw=1.6)
        t = s / 3
        polyline(c, [(cx - h + t, cy + h), (cx - h + t, cy + h - t),
                     (cx + h - t, cy + h - t), (cx + h - t, cy - h + t),
                     (cx + h, cy - h + t)], lw=1.3, color=color)
        circle(c, cx - h + t / 2, cy, s * 0.07, fill=color, stroke=None)
        circle(c, cx + h - t / 2, cy + h - t / 2, s * 0.07, fill=color, stroke=None)


GAME = Sterrenstelsels()
