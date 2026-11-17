"""Doolhof - perfect mazes: rectangular for levels 1-2, circular for level 3.

A maze is stored as a graph: the cells are numbered, ``open`` lists the pairs
of neighbouring cells without a wall between them. Every maze is *perfect*
(a spanning tree), so there is exactly one route from start to finish.
"""
import math

from ..draw import circle, line, polyline, star, text
from ..theme import INK, PEN, RED, WHITE
from .base import Game

RECT = {1: (14, 14), 2: (20, 20)}     # (cols, rows)
RINGS = 9                              # level 3
MARK = 17.0                            # space kept free for start/finish marks


# --- topology -----------------------------------------------------------------
def ring_counts(rings):
    """Number of cells in ring 1..rings (ring 0 is the single centre cell).

    A ring doubles its cell count as soon as its cells would get too wide.
    """
    counts = [6]
    for k in range(2, rings + 1):
        prev = counts[-1]
        counts.append(prev * 2 if 2 * math.pi * k / prev > 1.6 else prev)
    return counts


def _ring_offsets(counts):
    offs, total = [], 1
    for n in counts:
        offs.append(total)
        total += n
    return offs, total


def neighbours(puz):
    """Adjacency lists of the cell graph (walls ignored)."""
    if puz["type"] == "rect":
        cols, rows = puz["cols"], puz["rows"]
        adj = [[] for _ in range(cols * rows)]
        for r in range(rows):
            for c in range(cols):
                i = r * cols + c
                if c + 1 < cols:
                    adj[i].append(i + 1)
                    adj[i + 1].append(i)
                if r + 1 < rows:
                    adj[i].append(i + cols)
                    adj[i + cols].append(i)
        return adj
    counts = puz["counts"]
    offs, total = _ring_offsets(counts)
    adj = [[] for _ in range(total)]
    for k, n in enumerate(counts):
        for j in range(n):
            i = offs[k] + j
            nxt = offs[k] + (j + 1) % n
            adj[i].append(nxt)
            adj[nxt].append(i)
            if k == 0:
                inner = 0
            elif counts[k - 1] == n:
                inner = offs[k - 1] + j
            else:
                inner = offs[k - 1] + j // 2
            adj[i].append(inner)
            adj[inner].append(i)
    return adj


def _carve(adj, rng, start, newest=0.78):
    """Growing-tree maze: mostly depth-first (long winding corridors), with
    an occasional random pick for extra side branches."""
    seen = [False] * len(adj)
    seen[start] = True
    active = [start]
    edges = []
    while active:
        k = len(active) - 1 if rng.random() < newest else rng.randrange(len(active))
        cell = active[k]
        free = [n for n in adj[cell] if not seen[n]]
        if not free:
            active.pop(k)
            continue
        nxt = rng.choice(free)
        seen[nxt] = True
        edges.append(sorted((cell, nxt)))
        active.append(nxt)
    return sorted(edges)


def _route(n, edges, start, end):
    links = [[] for _ in range(n)]
    for a, b in edges:
        links[a].append(b)
        links[b].append(a)
    prev = {start: None}
    queue = [start]
    for cell in queue:
        if cell == end:
            break
        for nb in links[cell]:
            if nb not in prev:
                prev[nb] = cell
                queue.append(nb)
    path = [end]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    return path[::-1]


# --- geometry helpers for the circular maze -------------------------------------
def _polar(cx, cy, r, a):
    """Angle 0 points up, angles grow clockwise."""
    return (cx + r * math.sin(a), cy + r * math.cos(a))


def _arc_points(cx, cy, r, a1, a2, step=math.radians(3)):
    n = max(1, int(math.ceil(abs(a2 - a1) / step)))
    return [_polar(cx, cy, r, a1 + (a2 - a1) * i / n) for i in range(n + 1)]


class Doolhof(Game):
    key = "doolhof"
    name = "Doolhof"
    category = "ruimte"
    tagline = "Eén weg leidt naar het doel. Vind hem zonder vast te lopen."
    rules = [
        "Teken met je pen de weg van de rode pijl naar de ster.",
        "Je mag nergens door een muur gaan.",
        "Er is precies één route; alle andere gangen lopen dood.",
    ]
    tips = [
        "Kijk eerst met je ogen vooruit en teken pas daarna.",
        "Vanaf de ster terugwerken is vaak verrassend makkelijk.",
    ]
    counts = (9, 8, 8)
    example = False

    # -- logic -------------------------------------------------------------------
    def generate(self, rng, level):
        if level in RECT:
            cols, rows = RECT[level]
            puz = {"type": "rect", "cols": cols, "rows": rows}
            end = (rows - 1) * cols + rng.randrange(cols - cols // 3, cols)
            starts = list(range(cols))
        else:
            counts = ring_counts(RINGS)
            offs, total = _ring_offsets(counts)
            puz = {"type": "circle", "rings": RINGS, "counts": counts}
            end = 0
            starts = list(range(offs[-1], total))
        adj = neighbours(puz)
        # Carving depth-first from the goal makes routes *to* the goal long;
        # the entrance is one of the border cells farthest from it.
        puz["open"] = _carve(adj, rng, end)
        routes = sorted((_route(len(adj), puz["open"], s, end) for s in starts),
                        key=len, reverse=True)
        path = rng.choice(routes[:3])
        puz["start"], puz["end"] = path[0], end
        puz["path"] = path
        return puz

    def verify(self, puz):
        adj = neighbours(puz)
        n = len(adj)
        edges = puz["open"]
        assert len(edges) == n - 1, "a perfect maze has n-1 passages"
        assert len({tuple(e) for e in edges}) == len(edges)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            assert b in adj[a], "passage between cells that are not neighbours"
            ra, rb = find(a), find(b)
            assert ra != rb, "maze contains a loop"
            parent[ra] = rb
        assert len({find(i) for i in range(n)}) == 1, "maze is not connected"
        path = puz["path"]
        assert path[0] == puz["start"] and path[-1] == puz["end"]
        assert len(set(path)) == len(path)
        passages = {tuple(e) for e in edges}
        for a, b in zip(path, path[1:]):
            assert (min(a, b), max(a, b)) in passages, "route crosses a wall"
        if puz["type"] == "rect":
            assert puz["start"] < puz["cols"]
            assert puz["end"] >= (puz["rows"] - 1) * puz["cols"]
        else:
            assert puz["end"] == 0 and puz["start"] >= n - puz["counts"][-1]

    # -- presentation --------------------------------------------------------------
    def instruction(self, puz, part=0):
        if puz["type"] == "circle":
            return "Teken de weg van de rode pijl aan de buitenrand naar de ster in het midden."
        return "Teken de weg van de rode pijl bovenaan naar de ster onderaan."

    def draw(self, c, box, puz, solved=False, part=0):
        if puz["type"] == "rect":
            self._draw_rect(c, box, puz, solved)
        else:
            self._draw_circle(c, box, puz, solved)

    @staticmethod
    def _arrow(c, x, y, angle, size=6.5):
        """Filled red triangle whose tip is at (x, y), pointing along angle
        (0 = down the page, measured like _polar's inward direction)."""
        dx, dy = math.sin(angle), math.cos(angle)      # unit vector tip -> base
        px, py = dy, -dx
        base = (x + dx * size * 1.5, y + dy * size * 1.5)
        polyline(c, [(x, y), (base[0] + px * size, base[1] + py * size),
                     (base[0] - px * size, base[1] - py * size)],
                 lw=0.6, color=RED, close=True, fill=RED)

    def _draw_rect(self, c, box, puz, solved):
        x, y, w, h = box
        cols, rows = puz["cols"], puz["rows"]
        cell = min(w / cols, (h - 2 * MARK) / rows, 40)
        x0 = x + (w - cols * cell) / 2
        ytop = y + h - (h - rows * cell) / 2
        passages = {tuple(e) for e in puz["open"]}
        s_col = puz["start"]
        e_col = puz["end"] - (rows - 1) * cols

        def X(col):
            return x0 + col * cell

        def Y(row):
            return ytop - row * cell

        lw = 1.7
        # horizontal wall runs (row boundary j lies above row j)
        for j in range(rows + 1):
            run = None
            for col in range(cols + 1):
                wall = False
                if col < cols:
                    if j == 0:
                        wall = col != s_col
                    elif j == rows:
                        wall = col != e_col
                    else:
                        a = (j - 1) * cols + col
                        wall = (a, a + cols) not in passages
                if wall and run is None:
                    run = col
                elif not wall and run is not None:
                    line(c, X(run), Y(j), X(col), Y(j), lw, INK, cap=1)
                    run = None
        # vertical wall runs (column boundary i lies left of column i)
        for i in range(cols + 1):
            run = None
            for row in range(rows + 1):
                wall = False
                if row < rows:
                    if i in (0, cols):
                        wall = True
                    else:
                        a = row * cols + i - 1
                        wall = (a, a + 1) not in passages
                if wall and run is None:
                    run = row
                elif not wall and run is not None:
                    line(c, X(i), Y(run), X(i), Y(row), lw, INK, cap=1)
                    run = None
        sx, ex = X(s_col) + cell / 2, X(e_col) + cell / 2
        self._arrow(c, sx, Y(0) + 3, 0)
        star(c, ex, Y(rows) - 9, 7.5, fill=INK)
        if solved:
            pts = [(sx, Y(0) + 3)]
            for i in puz["path"]:
                r, col = divmod(i, cols)
                pts.append((X(col) + cell / 2, Y(r) - cell / 2))
            pts.append((ex, Y(rows) - 2))
            polyline(c, pts, lw=max(1.8, cell * 0.11), color=PEN)

    def _draw_circle(self, c, box, puz, solved):
        x, y, w, h = box
        counts = puz["counts"]
        rings = len(counts)
        offs, total = _ring_offsets(counts)
        cx, cy = x + w / 2, y + h / 2
        R = min(w, h) / 2 - MARK
        rw = R / (rings + 1)                     # ring width; centre radius = rw
        passages = {tuple(e) for e in puz["open"]}
        start = puz["start"]
        lw = 1.7

        def is_open(a, b):
            return (min(a, b), max(a, b)) in passages

        def arc(r, a1, a2):
            polyline(c, _arc_points(cx, cy, r, a1, a2), lw=lw, color=INK)

        for k, n in enumerate(counts):
            r_in, r_out = rw * (k + 1), rw * (k + 2)
            da = 2 * math.pi / n
            for j in range(n):
                i = offs[k] + j
                a1, a2 = j * da, (j + 1) * da
                if k == 0:
                    inner = 0
                elif counts[k - 1] == n:
                    inner = offs[k - 1] + j
                else:
                    inner = offs[k - 1] + j // 2
                if not is_open(i, inner):
                    arc(r_in, a1, a2)
                if not is_open(i, offs[k] + (j + 1) % n):
                    p1, p2 = _polar(cx, cy, r_in, a2), _polar(cx, cy, r_out, a2)
                    line(c, p1[0], p1[1], p2[0], p2[1], lw, INK, cap=1)
                if k == rings - 1 and i != start:
                    arc(r_out, a1, a2)
        star(c, cx, cy, rw * 0.55, fill=INK)

        # start marker just outside the entrance
        n_out = counts[-1]
        a_start = (start - offs[-1] + 0.5) * 2 * math.pi / n_out
        tip = _polar(cx, cy, R + 3, a_start)
        self._arrow(c, tip[0], tip[1], a_start)

        if solved:
            def where(i):
                """(ring index, mid radius, centre angle, cells in ring)."""
                for k in range(rings - 1, -1, -1):
                    if i >= offs[k]:
                        n = counts[k]
                        return k, rw * (k + 1.5), (i - offs[k] + 0.5) * 2 * math.pi / n, n
                return -1, 0.0, 0.0, 1

            def turn(a_from, a_to):
                """a_to shifted by a multiple of 2*pi to be nearest to a_from."""
                d = (a_to - a_from + math.pi) % (2 * math.pi) - math.pi
                return a_from + d

            # The pen line only bends where the route changes ring: it runs
            # along the middle of a ring up to the crossing point, then
            # straight through the gap (centred on the narrower cell).
            path = puz["path"]
            _, r, a_cell, _ = where(path[0])
            a_pen = a_cell
            pts = [_polar(cx, cy, R + 3, a_pen), _polar(cx, cy, r, a_pen)]
            for cur, nxt in zip(path, path[1:]):
                k2, r2, a2, n2 = where(nxt)
                if k2 >= 0 and abs(r2 - r) < 1e-6:        # along the ring
                    a_cell = turn(a_cell, a2)
                    continue
                n1 = where(cur)[3]
                cross = turn(a_cell, a2) if (k2 >= 0 and n2 >= n1) else a_cell
                if abs(cross - a_pen) > 1e-9:
                    pts += _arc_points(cx, cy, r, a_pen, cross)[1:]
                if k2 < 0:                               # into the centre
                    pts.append(_polar(cx, cy, rw * 0.62, cross))
                    break
                pts.append(_polar(cx, cy, r2, cross))
                r, a_pen = r2, cross
                a_cell = turn(cross, a2)
            polyline(c, pts, lw=2.2, color=PEN)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        lw = 1.5
        polyline(c, [(cx - h * 0.3, cy + h), (cx - h, cy + h), (cx - h, cy - h),
                     (cx + h, cy - h), (cx + h, cy + h), (cx + h * 0.2, cy + h)],
                 lw, color)
        polyline(c, [(cx - h * 0.3, cy + h), (cx - h * 0.3, cy + h * 0.35),
                     (cx + h * 0.45, cy + h * 0.35)], lw, color)
        polyline(c, [(cx - h, cy - h * 0.25), (cx - h * 0.35, cy - h * 0.25)],
                 lw, color)
        polyline(c, [(cx + h * 0.35, cy - h), (cx + h * 0.35, cy - h * 0.3),
                     (cx - h * 0.0, cy - h * 0.3)], lw, color)


GAME = Doolhof()
