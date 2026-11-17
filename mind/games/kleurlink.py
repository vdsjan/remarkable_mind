"""Kleurlink - connect each pair of coloured dots; every cell gets used.

Puzzle dict:
    n       grid size
    dots    [[r1, c1, r2, c2], ...]   one entry per colour (A, B, C, ...)
    paths   [[[r, c], ...], ...]      the unique solution, path k joins dots[k]
"""
from ..draw import Grid, circle, line, polyline, text_mid
from ..theme import INK, MUSTARD, PALETTE, WHITE
from .base import Game

SIZES = {1: (5, 4, 5), 2: (6, 5, 6), 3: (7, 6, 7)}      # n, min/max pairs
LETTERS = "ABCDEFGH"
DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))


# --- solver -------------------------------------------------------------------
def count_solutions(n, dots, limit=2, out=None):
    """Count the ways to join every pair with paths that fill the grid.

    Cells are visited in reading order. For each cell the links to the right
    and down are chosen so that dot cells end up with exactly one link and
    all other cells with exactly two; linked cells share a component, which
    may not close into a loop nor join two different colours.
    """
    N = n * n
    colour = [0] * N                     # colour of the cell's component
    for k, (r1, c1, r2, c2) in enumerate(dots):
        colour[r1 * n + c1] = colour[r2 * n + c2] = k + 1
    degree = [1 if colour[i] else 2 for i in range(N)]
    comp = list(range(N))
    right = [False] * N
    down = [False] * N
    found = 0

    def join(a, b):
        """Merge the components of a and b; returns undo info or None."""
        ca, cb = comp[a], comp[b]
        if ca == cb:
            return None                  # would close a loop
        ka, kb = colour[a], colour[b]
        if ka and kb and ka != kb:
            return None
        k = ka or kb
        changed = []
        for i in range(N):
            if comp[i] == cb or comp[i] == ca:
                if comp[i] != ca or colour[i] != k:
                    changed.append((i, comp[i], colour[i]))
                    comp[i] = ca
                    colour[i] = k
        return changed

    def undo(changed):
        for i, cmp_, col in changed:
            comp[i] = cmp_
            colour[i] = col

    def search(i):
        nonlocal found
        if i == N:
            found += 1
            if out is not None and found == 1:
                out["right"], out["down"] = list(right), list(down)
            return
        r, c = divmod(i, n)
        have = (1 if c and right[i - 1] else 0) + (1 if r and down[i - n] else 0)
        need = degree[i] - have
        if need < 0:
            return
        can_r, can_d = c + 1 < n, r + 1 < n
        options = []
        if need == 0:
            options.append((False, False))
        elif need == 1:
            if can_r:
                options.append((True, False))
            if can_d:
                options.append((False, True))
        elif can_r and can_d:
            options.append((True, True))
        for go_r, go_d in options:
            u1 = u2 = None
            ok = True
            if go_r:
                u1 = join(i, i + 1)
                ok = u1 is not None
            if ok and go_d:
                u2 = join(i, i + n)
                ok = u2 is not None
            if ok:
                right[i], down[i] = go_r, go_d
                search(i + 1)
                right[i] = down[i] = False
            if u2 is not None:
                undo(u2)
            if u1 is not None:
                undo(u1)
            if found >= limit:
                return

    search(0)
    return found


# --- generator ----------------------------------------------------------------
def _cover(rng, n):
    """Random partition of the grid into paths, or None when it gets stuck.

    Paths never run alongside themselves (a cell only touches its own path
    at its direct predecessor/successor): that keeps the puzzles free of
    fat U-turns, which are both ugly and rarely unique.
    """
    owner = {}
    paths = []
    cells = [(r, c) for r in range(n) for c in range(n)]

    def free_nb(cell):
        r, c = cell
        return [(r + dr, c + dc) for dr, dc in DIRS
                if 0 <= r + dr < n and 0 <= c + dc < n
                and (r + dr, c + dc) not in owner]

    def touches(cell, pid, allowed):
        r, c = cell
        return any(owner.get((r + dr, c + dc)) == pid and (r + dr, c + dc) != allowed
                   for dr, dc in DIRS)

    while len(owner) < n * n:
        # start in the tightest spot, so no lonely cells are left behind
        open_cells = [cell for cell in cells if cell not in owner]
        tight = min(len(free_nb(cell)) for cell in open_cells)
        start = rng.choice([cell for cell in open_cells if len(free_nb(cell)) == tight])
        pid = len(paths)
        path = [start]
        owner[start] = pid
        want = rng.randint(3, n + 3)
        while len(path) < want:
            options = [nb for nb in free_nb(path[-1]) if not touches(nb, pid, path[-1])]
            if not options:
                break
            # prefer the neighbour with the fewest exits: hugs walls, fills gaps
            options.sort(key=lambda nb: len(free_nb(nb)))
            nxt = options[0] if rng.random() < 0.6 else rng.choice(options)
            path.append(nxt)
            owner[nxt] = pid
        if len(path) < 3:
            return None
        paths.append(path)
    return paths


class Kleurlink(Game):
    key = "kleurlink"
    name = "Kleurlink"
    category = "ruimte"
    tagline = "Verbind de kleuren en laat geen vakje leeg."
    rules = [
        "Verbind de twee stippen met dezelfde letter en kleur door een lijn "
        "van vakje naar vakje, horizontaal of verticaal.",
        "Lijnen kruisen of raken elkaar nooit: in elk vakje loopt precies één lijn.",
        "Alle vakjes van het rooster worden gebruikt.",
    ]
    tips = [
        "Begin met stippen in de hoeken en langs de rand: daar is weinig keuze.",
        "Blijft er een vakje leeg, dan moet een lijn een omweg maken.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n, lo, hi = SIZES[level]
        for _ in range(200000):
            paths = _cover(rng, n)
            if paths is None or not lo <= len(paths) <= hi:
                continue
            rng.shuffle(paths)
            dots = [[p[0][0], p[0][1], p[-1][0], p[-1][1]] for p in paths]
            if count_solutions(n, dots, 2) != 1:
                continue
            return {"n": n, "dots": dots,
                    "paths": [[list(cell) for cell in p] for p in paths]}
        raise AssertionError("could not generate a unique Kleurlink puzzle")

    def verify(self, puz):
        n, dots, paths = puz["n"], puz["dots"], puz["paths"]
        assert len(dots) == len(paths) <= len(PALETTE)
        seen = set()
        for (r1, c1, r2, c2), path in zip(dots, paths):
            assert path[0] == [r1, c1] and path[-1] == [r2, c2]
            assert len(path) >= 2
            for (ra, ca), (rb, cb) in zip(path, path[1:]):
                assert abs(ra - rb) + abs(ca - cb) == 1, "path must move to a neighbour"
            for r, c in path:
                assert 0 <= r < n and 0 <= c < n
                assert (r, c) not in seen, "paths overlap"
                seen.add((r, c))
        assert len(seen) == n * n, "every cell must be used"
        assert count_solutions(n, dots, 2) == 1, "Kleurlink must be unique"

    def instruction(self, puz, part=0):
        return ("Verbind gelijke letters en vul elk vakje. "
                "Pak er gerust de kleurpennen van je Paper Pro bij.")

    @staticmethod
    def _ink(k):
        colour = PALETTE[k % len(PALETTE)]
        return colour, (INK if colour == MUSTARD else WHITE)

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        g = Grid(box, n, n, max_cell=78)
        g.lines(c, lw=0.7, outer=2.0)
        if solved:
            for k, path in enumerate(puz["paths"]):
                colour, _ = self._ink(k)
                pts = [(g.cx(col), g.cy(r)) for r, col in path]
                polyline(c, pts, lw=g.cell * 0.26, color=colour)
        for k, (r1, c1, r2, c2) in enumerate(puz["dots"]):
            colour, on = self._ink(k)
            for r, col in ((r1, c1), (r2, c2)):
                circle(c, g.cx(col), g.cy(r), g.cell * 0.33, fill=colour, stroke=None)
                text_mid(c, g.cx(col), g.cy(r), LETTERS[k], "SansB", g.cell * 0.36, on)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        r = s * 0.16
        polyline(c, [(cx - h + r, cy + h - r), (cx - h + r, cy - h + r),
                     (cx + h - r, cy - h + r)], lw=2.2, color=color)
        circle(c, cx - h + r, cy + h - r, r, fill=color, stroke=None)
        circle(c, cx + h - r, cy - h + r, r, fill=color, stroke=None)
        circle(c, cx + h - r, cy + h - r, r, stroke=color, lw=1.5)
        circle(c, cx, cy, r, stroke=color, lw=1.5)


GAME = Kleurlink()
