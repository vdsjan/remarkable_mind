"""Dominodetective - find the hidden dominoes; every pair occurs exactly once.

Puzzle dict:
    n          highest number of the set (double-n: pairs 0-0 ... n-n)
    grid       rows x cols numbers, rows = n + 1, cols = n + 2
    dominoes   [[r1, c1, r2, c2], ...]   the unique solution
"""
from .. import theme
from ..draw import Grid, circle, line, rrect, text_mid
from ..theme import GREY, INK, MID, PEN
from .base import Game

# level -> highest number of the set, per page type
SETS = {1: 3, 2: 4, 3: 6}
SETS_COMPACT = {1: 3, 2: 4, 3: 5}


def all_pairs(n):
    return [(a, b) for a in range(n + 1) for b in range(a, n + 1)]


# --- solver -------------------------------------------------------------------
def count_solutions(grid, n, limit=2, out=None):
    """Count the ways to cut the grid into the complete double-n set.

    Exact cover: every cell lies in one domino and every pair of numbers is
    used once. Each step branches on the cell or the pair with the fewest
    possible places, so forced dominoes are placed without guessing.
    """
    R, C = len(grid), len(grid[0])
    pid = {p: i for i, p in enumerate(all_pairs(n))}
    N, P = R * C, len(pid)
    if N != 2 * P:
        return 0
    edges = []
    by_cell = [[] for _ in range(N)]
    by_pair = [[] for _ in range(P)]
    for r in range(R):
        for c in range(C):
            for r2, c2 in ((r, c + 1), (r + 1, c)):
                if r2 < R and c2 < C:
                    a, b = sorted((grid[r][c], grid[r2][c2]))
                    if (a, b) not in pid:
                        return 0
                    e = len(edges)
                    edges.append((r * C + c, r2 * C + c2, pid[(a, b)]))
                    by_cell[r * C + c].append(e)
                    by_cell[r2 * C + c2].append(e)
                    by_pair[pid[(a, b)]].append(e)
    covered = [False] * N
    used = [False] * P
    chosen = []
    found = 0

    def options(cands):
        return [e for e in cands
                if not covered[edges[e][0]] and not covered[edges[e][1]]
                and not used[edges[e][2]]]

    def search():
        nonlocal found
        best, best_n = None, 99
        for i in range(N):
            if not covered[i]:
                opts = options(by_cell[i])
                if len(opts) < best_n:
                    best, best_n = opts, len(opts)
                    if best_n <= 1:
                        break
        if best is None:
            found += 1
            if out is not None and found == 1:
                out[:] = [[edges[e][0] // C, edges[e][0] % C,
                           edges[e][1] // C, edges[e][1] % C] for e in chosen]
            return
        if best_n > 1:
            for p in range(P):
                if not used[p]:
                    opts = options(by_pair[p])
                    if len(opts) < best_n:
                        best, best_n = opts, len(opts)
                        if best_n <= 1:
                            break
        for e in best:
            i, j, p = edges[e]
            covered[i] = covered[j] = used[p] = True
            chosen.append(e)
            search()
            chosen.pop()
            covered[i] = covered[j] = used[p] = False
            if found >= limit:
                return

    search()
    return found


# --- generator ----------------------------------------------------------------
def random_tiling(rng, R, C):
    """A random way to cover an R x C rectangle with dominoes."""
    owner = [[False] * C for _ in range(R)]
    doms = []

    def fill():
        for r in range(R):
            for c in range(C):
                if not owner[r][c]:
                    opts = []
                    if c + 1 < C and not owner[r][c + 1]:
                        opts.append((r, c + 1))
                    if r + 1 < R and not owner[r + 1][c]:
                        opts.append((r + 1, c))
                    rng.shuffle(opts)
                    for r2, c2 in opts:
                        owner[r][c] = owner[r2][c2] = True
                        doms.append([r, c, r2, c2])
                        if fill():
                            return True
                        doms.pop()
                        owner[r][c] = owner[r2][c2] = False
                    return False
        return True

    assert fill()
    return doms


class Dominodetective(Game):
    key = "dominodetective"
    name = "Dominodetective"
    category = "getallen"
    tagline = "De stenen liggen er nog, alleen hun randen zijn verdwenen."
    rules = [
        "In het rooster ligt een volledig dominospel, maar de randen van de "
        "stenen zijn weg. Teken ze terug: elke steen bedekt twee vakjes naast elkaar.",
        "Elke combinatie van twee cijfers komt precies één keer voor, ook de dubbele.",
        "Onder het rooster staan alle stenen; streep af wat je gevonden hebt.",
    ]
    tips = [
        "Zoek een combinatie die maar op één plek kan liggen, zoals een dubbele.",
        "Ligt een steen vast, dan zijn alle andere plekken van die combinatie een grens.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n = (SETS_COMPACT if theme.COMPACT else SETS)[level]
        R, C = n + 1, n + 2
        pairs = all_pairs(n)
        for _ in range(100000):
            doms = random_tiling(rng, R, C)
            order = pairs[:]
            rng.shuffle(order)
            grid = [[0] * C for _ in range(R)]
            for (r1, c1, r2, c2), (a, b) in zip(doms, order):
                if rng.random() < 0.5:
                    a, b = b, a
                grid[r1][c1], grid[r2][c2] = a, b
            if count_solutions(grid, n, 2) == 1:
                return {"n": n, "grid": grid, "dominoes": sorted(doms)}
        raise AssertionError("could not generate a unique domino puzzle")

    def verify(self, puz):
        n, grid, doms = puz["n"], puz["grid"], puz["dominoes"]
        R, C = n + 1, n + 2
        assert len(grid) == R and all(len(row) == C for row in grid)
        assert all(0 <= v <= n for row in grid for v in row)
        seen, found = set(), []
        for r1, c1, r2, c2 in doms:
            assert 0 <= r1 < R and 0 <= r2 < R and 0 <= c1 < C and 0 <= c2 < C
            assert abs(r1 - r2) + abs(c1 - c2) == 1, "a domino covers two neighbours"
            for cell in ((r1, c1), (r2, c2)):
                assert cell not in seen, "dominoes overlap"
                seen.add(cell)
            found.append(tuple(sorted((grid[r1][c1], grid[r2][c2]))))
        assert len(seen) == R * C, "every cell is covered"
        assert sorted(found) == all_pairs(n), "every pair occurs exactly once"
        assert count_solutions(grid, n, 2) == 1, "the domino puzzle must be unique"

    def instruction(self, puz, part=0):
        n = puz["n"]
        return (f"Teken de randen van de {len(all_pairs(n))} dominostenen "
                f"(0 tot en met {n}); elke combinatie komt één keer voor.")

    # -- drawing -----------------------------------------------------------------
    def draw(self, c, box, puz, solved=False, part=0):
        n, grid = puz["n"], puz["grid"]
        R, C = n + 1, n + 2
        x, y, w, h = box
        compact = w < 360
        # checklist of all pairs, a triangle under the grid
        tw, th = (23.0, 12.0) if compact else (30.0, 15.0)
        gx, gy = (3.0, 2.6) if compact else (4.0, 3.5)
        list_h = (n + 1) * (th + gy) - gy
        gap = 14 if compact else 20
        cell = min(46 if compact else 62, w / C, (h - list_h - gap) / R)
        block = R * cell + gap + list_h          # grid + checklist, centred
        y = y + (h - block) / 2
        g = Grid((x, y + list_h + gap, w, R * cell), C, R, max_cell=cell)
        # faint cell guides, strong outer border
        for i in range(1, C):
            line(c, g.x(i), g.y(0), g.x(i), g.y(R), 0.6, MID, dash=(1.2, 2.6))
        for j in range(1, R):
            line(c, g.x(0), g.y(j), g.x(C), g.y(j), 0.6, MID, dash=(1.2, 2.6))
        rrect(c, g.x(0), g.y(R), g.w, g.h, 3, stroke=INK, lw=2.0)
        for r in range(R):
            for col in range(C):
                g.given(c, r, col, grid[r][col], scale=0.5)
        if solved:
            inset = max(2.5, g.cell * 0.085)
            for r1, c1, r2, c2 in puz["dominoes"]:
                x0, y0 = g.x(min(c1, c2)), g.y(max(r1, r2) + 1)
                ww = g.cell * (2 if r1 == r2 else 1)
                hh = g.cell * (2 if c1 == c2 else 1)
                rrect(c, x0 + inset, y0 + inset, ww - 2 * inset, hh - 2 * inset,
                      g.cell * 0.2, stroke=PEN, lw=2.0)
        # the set: row a holds a-a, a-(a+1), ... a-n
        top = y + list_h
        fs = 8.0 if compact else 9.6
        full = (n + 1) * (tw + gx) - gx
        for a in range(n + 1):
            ry = top - a * (th + gy) - th
            x0 = x + (w - full) / 2 + a * (tw + gx) / 2
            for k, b in enumerate(range(a, n + 1)):
                tx = x0 + k * (tw + gx)
                rrect(c, tx, ry, tw, th, 2.5, stroke=GREY, lw=0.8)
                line(c, tx + tw / 2, ry + 2, tx + tw / 2, ry + th - 2, 0.6, GREY)
                text_mid(c, tx + tw / 4, ry + th / 2, a, "SansS", fs, INK)
                text_mid(c, tx + 3 * tw / 4, ry + th / 2, b, "SansS", fs, INK)

    def icon(self, c, cx, cy, s, color):
        w, h = s * 0.9, s * 0.5
        rrect(c, cx - w / 2, cy - h / 2, w, h, s * 0.09, stroke=color, lw=1.6)
        line(c, cx, cy - h / 2, cx, cy + h / 2, 1.3, color)
        r = s * 0.055
        for dx, dy in ((-0.31, 0.12), (-0.14, -0.12)):
            circle(c, cx + dx * s, cy + dy * s, r, fill=color, stroke=None)
        for dx, dy in ((0.13, 0.12), (0.225, 0.0), (0.32, -0.12)):
            circle(c, cx + dx * s, cy + dy * s, r, fill=color, stroke=None)


GAME = Dominodetective()
