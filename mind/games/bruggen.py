"""Bruggen (Hashiwokakero) - connect numbered islands with bridges.

Puzzle dict:
    size      grid size n (islands sit on an n x n lattice)
    islands   [[row, col, number], ...]
    bridges   [[i, j, count], ...]  the unique solution (i < j island indices)
"""
from ..draw import Grid, circle, line, text_mid
from ..theme import INK, PEN, WHITE
from .base import Game

SIZES = {1: (7, 8, 10), 2: (9, 12, 16), 3: (11, 18, 24)}   # n, min/max islands


# --- solver -------------------------------------------------------------------
def _edges(islands):
    """Pairs of islands that see each other along a row or column."""
    at = {(r, c): i for i, (r, c, _) in enumerate(islands)}
    far = max(max(r, c) for r, c, _ in islands)
    edges = []
    for i, (r, c, _) in enumerate(islands):
        for dr, dc in ((0, 1), (1, 0)):
            rr, cc = r + dr, c + dc
            cells = []
            while (rr, cc) not in at and rr <= far and cc <= far:
                cells.append((rr, cc))
                rr, cc = rr + dr, cc + dc
            if (rr, cc) in at:
                edges.append((i, at[(rr, cc)], dr == 0, cells))
    return edges


def _crossings(edges):
    cross = [[] for _ in edges]
    cellsets = [set(e[3]) for e in edges]
    for a in range(len(edges)):
        for b in range(a + 1, len(edges)):
            if edges[a][2] != edges[b][2] and cellsets[a] & cellsets[b]:
                cross[a].append(b)
                cross[b].append(a)
    return cross


def solve(islands, limit=2):
    """Return (solutions, branch_count); solutions is a list (max `limit`)
    of bridge-count lists aligned with ``_edges(islands)``."""
    edges = _edges(islands)
    cross = _crossings(edges)
    n = len(islands)
    need = [isl[2] for isl in islands]
    at_island = [[] for _ in range(n)]
    for k, (a, b, _, _) in enumerate(edges):
        at_island[a].append(k)
        at_island[b].append(k)
    solutions = []
    branches = 0

    def propagate(lo, hi):
        changed = True
        while changed:
            changed = False
            for k in range(len(edges)):
                if lo[k] > 0:
                    for x in cross[k]:
                        if hi[x] > 0:
                            if lo[x] > 0:
                                return False
                            hi[x] = 0
                            changed = True
            for i in range(n):
                ks = at_island[i]
                slo = sum(lo[k] for k in ks)
                shi = sum(hi[k] for k in ks)
                if slo > need[i] or shi < need[i]:
                    return False
                for k in ks:
                    new_hi = min(hi[k], need[i] - (slo - lo[k]))
                    new_lo = max(lo[k], need[i] - (shi - hi[k]))
                    if new_lo > new_hi:
                        return False
                    if new_hi != hi[k] or new_lo != lo[k]:
                        slo += new_lo - lo[k]
                        shi += new_hi - hi[k]
                        lo[k], hi[k] = new_lo, new_hi
                        changed = True
        return True

    def connected(bound):
        """Is the island graph connected using edges with bound[k] > 0?"""
        seen = [False] * n
        seen[0] = True
        stack = [0]
        count = 1
        while stack:
            i = stack.pop()
            for k in at_island[i]:
                if bound[k] > 0:
                    j = edges[k][0] if edges[k][1] == i else edges[k][1]
                    if not seen[j]:
                        seen[j] = True
                        count += 1
                        stack.append(j)
        return count == n

    def search(lo, hi):
        nonlocal branches
        if not propagate(lo, hi) or not connected(hi):
            return
        best, best_w = -1, 9
        for k in range(len(edges)):
            w = hi[k] - lo[k]
            if 0 < w < best_w:
                best, best_w = k, w
        if best < 0:
            if connected(lo):
                solutions.append(list(lo))
            return
        branches += 1
        for v in range(lo[best], hi[best] + 1):
            l2, h2 = list(lo), list(hi)
            l2[best] = h2[best] = v
            search(l2, h2)
            if len(solutions) >= limit:
                return

    search([0] * len(edges), [2] * len(edges))
    return solutions, branches, edges


# --- generator ----------------------------------------------------------------
def _layout(rng, n, target):
    """Grow a random connected set of islands and bridges on an n x n grid."""
    occupied = {}                       # cell -> ("i", idx) | ("h"|"v", None)
    islands = []
    bridges = {}

    def add_island(r, c):
        occupied[(r, c)] = ("i", len(islands))
        islands.append((r, c))

    add_island(rng.randrange(n), rng.randrange(n))
    fails = 0
    while len(islands) < target and fails < 300:
        i = rng.randrange(len(islands))
        r, c = islands[i]
        dr, dc = rng.choice(((0, 1), (0, -1), (1, 0), (-1, 0)))
        dist = rng.choice((2, 2, 3, 3, 4, 5))
        tr, tc = r + dr * dist, c + dc * dist
        ok = 0 <= tr < n and 0 <= tc < n and (tr, tc) not in occupied
        if ok:
            for s in range(1, dist):
                if (r + dr * s, c + dc * s) in occupied:
                    ok = False
                    break
        if ok:
            # keep islands from sitting shoulder to shoulder
            for ar, ac in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if occupied.get((tr + ar, tc + ac), ("", 0))[0] == "i":
                    ok = False
                    break
        if not ok:
            fails += 1
            continue
        for s in range(1, dist):
            occupied[(r + dr * s, c + dc * s)] = ("h" if dr == 0 else "v", None)
        add_island(tr, tc)
        bridges[(i, len(islands) - 1)] = rng.choice((1, 1, 2))
    # a few extra bridges between islands that already face each other
    full = [(r, c, 0) for r, c in islands]
    for a, b, horiz, cells in _edges(full):
        if (a, b) in bridges or (b, a) in bridges:
            continue
        if any(cell in occupied for cell in cells):
            continue
        if rng.random() < 0.35:
            for cell in cells:
                occupied[cell] = ("h" if horiz else "v", None)
            bridges[(a, b)] = rng.choice((1, 2))
    return islands, bridges


class Bruggen(Game):
    key = "bruggen"
    name = "Bruggen"
    category = "logica"
    tagline = "Verbind alle eilanden tot één geheel."
    rules = [
        "Verbind de eilanden met rechte bruggen, horizontaal of verticaal.",
        "Het getal op een eiland is het aantal bruggen dat er vertrekt; "
        "tussen twee eilanden liggen hoogstens twee bruggen.",
        "Bruggen kruisen elkaar nooit en lopen niet over een ander eiland.",
        "Op het einde is elk eiland via bruggen bereikbaar vanaf elk ander eiland.",
    ]
    tips = [
        "Een 8 in het midden, een 6 aan de rand of een 4 in een hoek heeft "
        "overal dubbele bruggen.",
        "Een eiland met een 1 mag nooit alleen met een andere 1 verbonden zijn.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n, lo, hi = SIZES[level]
        best = None
        for attempt in range(4000):
            target = rng.randint(lo, hi)
            cells, bridges = _layout(rng, n, target)
            if len(cells) < lo:
                continue
            number = [0] * len(cells)
            for (a, b), k in bridges.items():
                number[a] += k
                number[b] += k
            order = sorted(range(len(cells)), key=lambda i: cells[i])
            pos = {old: new for new, old in enumerate(order)}
            islands = [[cells[i][0], cells[i][1], number[i]] for i in order]
            # stretch the layout over the whole board
            rows = [i[0] for i in islands]
            cols = [i[1] for i in islands]
            if max(rows) - min(rows) < n - 2 or max(cols) - min(cols) < n - 2:
                continue
            sols, branches, _ = solve(islands, 2)
            if len(sols) != 1:
                continue
            sol = sorted([min(pos[a], pos[b]), max(pos[a], pos[b]), k]
                         for (a, b), k in bridges.items())
            puz = {"size": n, "islands": islands, "bridges": sol}
            # level 1: solvable by counting alone; level 3: needs real thought
            if level == 1 and branches > 0:
                best = best or puz
                continue
            if level == 3 and branches == 0 and attempt < 600:
                best = best or puz
                continue
            return puz
        assert best is not None, "could not generate a unique bridges puzzle"
        return best

    def verify(self, puz):
        n, islands, bridges = puz["size"], puz["islands"], puz["bridges"]
        at = {(r, c): i for i, (r, c, _) in enumerate(islands)}
        assert len(at) == len(islands)
        total = [0] * len(islands)
        used = {}
        links = {i: set() for i in range(len(islands))}
        for a, b, k in bridges:
            assert k in (1, 2) and a < b
            (r1, c1, _), (r2, c2, _) = islands[a], islands[b]
            assert (r1 == r2) != (c1 == c2), "bridge must be straight"
            if r1 == r2:
                cells = [(r1, c) for c in range(min(c1, c2) + 1, max(c1, c2))]
            else:
                cells = [(r, c1) for r in range(min(r1, r2) + 1, max(r1, r2))]
            for cell in cells:
                assert cell not in at, "bridge runs over an island"
                assert cell not in used, "bridges cross"
                used[cell] = (a, b)
            total[a] += k
            total[b] += k
            links[a].add(b)
            links[b].add(a)
        for (r, c, num), t in zip(islands, total):
            assert 0 <= r < n and 0 <= c < n
            assert 1 <= num <= 8 and num == t, "island number mismatch"
        seen, stack = {0}, [0]
        while stack:
            for j in links[stack.pop()]:
                if j not in seen:
                    seen.add(j)
                    stack.append(j)
        assert len(seen) == len(islands), "islands are not all connected"
        sols, _, edges = solve(islands, 2)
        assert len(sols) == 1, "bridges puzzle must be unique"
        found = sorted([min(a, b), max(a, b), k]
                       for (a, b, _, _), k in zip(edges, sols[0]) if k)
        assert found == sorted(bridges), "stored solution differs from solver"

    def instruction(self, puz, part=0):
        return "Verbind alle eilanden: elk getal telt de bruggen aan dat eiland."

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["size"]
        g = Grid(box, n, n, max_cell=60)
        rad = g.cell * 0.36
        if solved:
            off = g.cell * 0.10
            lw = max(1.8, g.cell * 0.05)
            for a, b, k in puz["bridges"]:
                (r1, c1, _), (r2, c2, _) = puz["islands"][a], puz["islands"][b]
                x1, y1, x2, y2 = g.cx(c1), g.cy(r1), g.cx(c2), g.cy(r2)
                horiz = r1 == r2
                for d in ((0,) if k == 1 else (-off, off)):
                    if horiz:
                        line(c, x1, y1 + d, x2, y2 + d, lw, PEN)
                    else:
                        line(c, x1 + d, y1, x2 + d, y2, lw, PEN)
        for r, col, num in puz["islands"]:
            circle(c, g.cx(col), g.cy(r), rad, fill=WHITE, stroke=INK,
                   lw=max(1.6, g.cell * 0.045))
            text_mid(c, g.cx(col), g.cy(r), num, "SansB", g.cell * 0.40, INK)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        r = s * 0.17
        a, b, d = (cx - h + r, cy + h - r), (cx + h - r, cy + h - r), (cx + h - r, cy - h + r)
        line(c, a[0] + r, a[1] + r * 0.4, b[0] - r, b[1] + r * 0.4, 1.4, color)
        line(c, a[0] + r, a[1] - r * 0.4, b[0] - r, b[1] - r * 0.4, 1.4, color)
        line(c, b[0], b[1] - r, d[0], d[1] + r, 1.4, color)
        for p in (a, b, d):
            circle(c, p[0], p[1], r, stroke=color, lw=1.5)


GAME = Bruggen()
