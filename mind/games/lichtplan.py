"""Lichtplan - Akari: light every room of a dark museum.

Cells are stored as a flat list: -1 is an open (white) cell, 0..4 a black
block with that number, 5 a black block without a number.
"""
import math

from .. import theme
from ..draw import Grid, circle, line, text_mid
from ..theme import INK, MUSTARD, PEN, WHITE
from .base import Game

OPEN, BLOCK = -1, 5
SIZES = {1: 6, 2: 8, 3: 10}
SIZES_COMPACT = {1: 6, 2: 7, 3: 8}          # Paper Pro Move: keep cells large
DENSITY = {1: 0.22, 2: 0.21, 3: 0.20}       # share of black blocks
KEEP = {1: 0.70, 2: 0.55, 3: 0.0}           # share of blocks that keep a number


def _geometry(n, cells):
    """(open cells, vis, blocks): vis[i] lists the cells a lamp on i shines
    on, blocks lists (number, adjacent open cells) per numbered block."""
    size = n * n
    vis = [()] * size
    opens = [i for i in range(size) if cells[i] == OPEN]
    for i in opens:
        r, c = divmod(i, n)
        seen = []
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < n and 0 <= cc < n and cells[rr * n + cc] == OPEN:
                seen.append(rr * n + cc)
                rr += dr
                cc += dc
        vis[i] = tuple(seen)
    blocks = []
    for i in range(size):
        if 0 <= cells[i] <= 4:
            r, c = divmod(i, n)
            adj = [rr * n + cc for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                   if 0 <= rr < n and 0 <= cc < n and cells[rr * n + cc] == OPEN]
            blocks.append((cells[i], tuple(adj)))
    return opens, vis, blocks


def solve(n, cells, limit=2, rng=None):
    """All lamp layouts up to ``limit``: returns (solutions, branches).

    A solution is a sorted list of lamp cells. ``branches`` counts the guesses
    the search needed; 0 means the puzzle falls to plain deduction. With
    ``rng`` the search order is shuffled, which yields a random solution."""
    opens, vis, blocks = _geometry(n, cells)
    sols = []
    branches = 0

    def place(state, lit, i):
        if state[i] != 0:
            return False
        state[i] = 1
        lit[i] = True
        for j in vis[i]:
            if state[j] == 1:
                return False
            state[j] = 2
            lit[j] = True
        return True

    def propagate(state, lit):
        changed = True
        while changed:
            changed = False
            for k, adj in blocks:
                lamps = free = 0
                for j in adj:
                    if state[j] == 1:
                        lamps += 1
                    elif state[j] == 0:
                        free += 1
                if lamps > k or lamps + free < k:
                    return False
                if free:
                    if lamps == k:
                        for j in adj:
                            if state[j] == 0:
                                state[j] = 2
                        changed = True
                    elif lamps + free == k:
                        for j in adj:
                            if state[j] == 0 and not place(state, lit, j):
                                return False
                        changed = True
            for i in opens:
                if lit[i]:
                    continue
                cand, cnt = -1, 0
                if state[i] == 0:
                    cand, cnt = i, 1
                for j in vis[i]:
                    if state[j] == 0:
                        cand = j
                        cnt += 1
                        if cnt > 1:
                            break
                if cnt == 0:
                    return False
                if cnt == 1:
                    if not place(state, lit, cand):
                        return False
                    changed = True
        return True

    def search(state, lit):
        nonlocal branches
        if not propagate(state, lit):
            return
        best = None
        for i in opens:
            if not lit[i]:
                cands = [j for j in vis[i] if state[j] == 0]
                if state[i] == 0:
                    cands.append(i)
                if best is None or len(cands) < len(best):
                    best = cands
        if best is None:                        # every cell lit: a solution
            sols.append(sorted(i for i in opens if state[i] == 1))
            return
        branches += 1
        if rng:
            rng.shuffle(best)
        for idx, cand in enumerate(best):
            s2, l2 = list(state), list(lit)
            for prev in best[:idx]:             # keep the branches disjoint
                if s2[prev] == 0:
                    s2[prev] = 2
            if place(s2, l2, cand):
                search(s2, l2)
            if len(sols) >= limit:
                return

    size = n * n
    state = [0 if cells[i] == OPEN else 2 for i in range(size)]
    lit = [cells[i] != OPEN for i in range(size)]
    search(state, lit)
    return sols, branches


def _layout(rng, n, density):
    """Random black blocks, symmetric under a half turn."""
    size = n * n
    cells = [OPEN] * size
    target = round(size * density)
    order = list(range(size))
    rng.shuffle(order)
    count = 0
    for i in order:
        if count >= target:
            break
        if cells[i] != OPEN:
            continue
        j = size - 1 - i
        cells[i] = cells[j] = BLOCK
        count += 1 if i == j else 2
    return cells


def _numbers(n, cells, lamps):
    lampset = set(lamps)
    out = list(cells)
    for i in range(n * n):
        if cells[i] != OPEN:
            r, c = divmod(i, n)
            out[i] = sum(1 for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                         if 0 <= rr < n and 0 <= cc < n and rr * n + cc in lampset)
    return out


class Lichtplan(Game):
    key = "lichtplan"
    name = "Lichtplan"
    category = "logica"
    tagline = "Het museum is donker. Waar hang jij de lampen?"
    rules = [
        "Zet lampen in de open vakjes tot elk open vakje verlicht is. Een lamp "
        "schijnt langs haar rij en kolom, tot aan een zwart blok.",
        "Twee lampen mogen elkaar nooit beschijnen.",
        "Een cijfer op een zwart blok zegt hoeveel lampen er pal naast staan: "
        "boven, onder, links of rechts.",
    ]
    tips = [
        "Begin bij de nullen en bij de cijfers die net zoveel vrije buren "
        "hebben: daar ligt alles vast.",
        "Zet een kruisje waar zeker geen lamp kan. Een vakje dat nog maar "
        "vanuit één plek te verlichten is, verraadt een lamp.",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        n = (SIZES_COMPACT if theme.COMPACT else SIZES)[level]
        best = None
        for attempt in range(400):
            base = _layout(rng, n, DENSITY[level])
            found, _ = solve(n, base, 1, rng)
            if not found:
                continue
            lamps = found[0]
            cells = _numbers(n, base, lamps)
            sols, branches = solve(n, cells, 2)
            if len(sols) != 1:
                continue
            blocks = [i for i in range(n * n) if cells[i] != OPEN]
            rng.shuffle(blocks)
            numbered = len(blocks)
            target = math.ceil(len(blocks) * KEEP[level])
            for i in blocks:
                if numbered <= target:
                    break
                keep, cells[i] = cells[i], BLOCK
                sols, br = solve(n, cells, 2)
                # levels 1 and 2 stay solvable without guessing
                if len(sols) == 1 and (level == 3 or br == 0):
                    numbered -= 1
                    branches = br
                else:
                    cells[i] = keep
            puz = {"n": n, "cells": cells, "lamps": lamps}
            if level < 3 and branches > 0:
                best = best or puz
                continue
            if level == 3 and branches == 0 and attempt < 12:
                best = best or puz              # prefer one that needs thought
                continue
            return puz
        assert best is not None, "could not generate a unique light plan"
        return best

    def verify(self, puz):
        n, cells, lamps = puz["n"], puz["cells"], puz["lamps"]
        assert len(cells) == n * n
        assert all(v == OPEN or 0 <= v <= BLOCK for v in cells)
        assert lamps == sorted(set(lamps))
        lampset = set(lamps)
        lit = set()
        for i in lamps:
            assert cells[i] == OPEN, "a lamp stands on a block"
            lit.add(i)
            r, c = divmod(i, n)
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                rr, cc = r + dr, c + dc
                while 0 <= rr < n and 0 <= cc < n and cells[rr * n + cc] == OPEN:
                    assert rr * n + cc not in lampset, "two lamps see each other"
                    lit.add(rr * n + cc)
                    rr += dr
                    cc += dc
        for i in range(n * n):
            r, c = divmod(i, n)
            if cells[i] == OPEN:
                assert i in lit, "an open cell stays dark"
            elif cells[i] != BLOCK:
                near = sum(1 for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                           if 0 <= rr < n and 0 <= cc < n and rr * n + cc in lampset)
                assert near == cells[i], "a number does not match its lamps"
        sols, _ = solve(n, cells, 2)
        assert len(sols) == 1, "light plan must be unique"
        assert sols[0] == lamps, "stored solution differs from solver"

    def instruction(self, puz, part=0):
        return ("Zet lampen tot elk open vakje verlicht is. Lampen beschijnen "
                "elkaar niet; een cijfer telt de lampen ernaast.")

    @staticmethod
    def _lamp(c, cx, cy, s):
        """A lamp of about s x s: bulb with eight short rays, in pen ink."""
        r = s * 0.20
        lw = max(1.1, s * 0.045)
        for k in range(8):
            a = k * math.pi / 4
            line(c, cx + math.cos(a) * r * 1.45, cy + math.sin(a) * r * 1.45,
                 cx + math.cos(a) * r * 2.05, cy + math.sin(a) * r * 2.05, lw, PEN)
        circle(c, cx, cy, r, fill=MUSTARD, stroke=PEN, lw=lw * 1.2)

    def draw(self, c, box, puz, solved=False, part=0):
        n, cells = puz["n"], puz["cells"]
        g = Grid(box, n, n, max_cell=60)
        for i, v in enumerate(cells):
            if v != OPEN:
                r, col = divmod(i, n)
                g.fill(c, r, col, INK)
                if v != BLOCK:
                    text_mid(c, g.cx(col), g.cy(r), v, "SansB", g.cell * 0.56, WHITE)
        g.lines(c, lw=0.7, outer=2.2)
        if solved:
            for i in puz["lamps"]:
                r, col = divmod(i, n)
                self._lamp(c, g.cx(col), g.cy(r), g.cell)

    def icon(self, c, cx, cy, s, color):
        r = s * 0.21
        y = cy + s * 0.12
        circle(c, cx, y, r, stroke=color, lw=1.6)
        for k in range(5):                      # rays over the top half
            a = math.pi * k / 4
            line(c, cx + math.cos(a) * r * 1.5, y + math.sin(a) * r * 1.5,
                 cx + math.cos(a) * r * 2.1, y + math.sin(a) * r * 2.1, 1.5, color)
        for dy in (0.30, 0.42):                 # the fitting
            line(c, cx - r * 0.55, cy - s * dy, cx + r * 0.55, cy - s * dy, 1.5, color)


GAME = Lichtplan()
