"""Sudoku - classic 9x9, every puzzle has exactly one solution."""
from ..draw import Grid, line
from ..theme import INK
from .base import Game

ROWS = [[r * 9 + c for c in range(9)] for r in range(9)]
PEERS = []
for i in range(81):
    r, c = divmod(i, 9)
    b = (r // 3) * 3, (c // 3) * 3
    p = {r * 9 + k for k in range(9)} | {k * 9 + c for k in range(9)}
    p |= {(b[0] + dr) * 9 + b[1] + dc for dr in range(3) for dc in range(3)}
    p.discard(i)
    PEERS.append(sorted(p))
FULL = 0x1FF


def _candidates(grid, i):
    used = 0
    for p in PEERS[i]:
        if grid[p]:
            used |= 1 << (grid[p] - 1)
    return FULL & ~used


def count_solutions(grid, limit=2, rng=None, out=None):
    """Count solutions of grid (list of 81 ints, 0 = empty) up to limit."""
    grid = list(grid)
    found = 0

    def search():
        nonlocal found
        best, best_mask, best_n = -1, 0, 10
        for i in range(81):
            if grid[i] == 0:
                m = _candidates(grid, i)
                n = bin(m).count("1")
                if n == 0:
                    return
                if n < best_n:
                    best, best_mask, best_n = i, m, n
                    if n == 1:
                        break
        if best < 0:
            found += 1
            if out is not None and found == 1:
                out[:] = grid
            return
        digits = [d for d in range(1, 10) if best_mask >> (d - 1) & 1]
        if rng:
            rng.shuffle(digits)
        for d in digits:
            grid[best] = d
            search()
            if found >= limit:
                break
        grid[best] = 0

    search()
    return found


class Sudoku(Game):
    key = "sudoku"
    name = "Sudoku"
    category = "getallen"
    tagline = "De klassieker: negen cijfers, één oplossing."
    rules = [
        "Vul elk leeg vakje met een cijfer van 1 tot 9.",
        "In elke rij, elke kolom en elk blok van 3 × 3 komt elk cijfer precies één keer voor.",
        "Gokken hoeft nooit: elke puzzel heeft exact één oplossing.",
    ]
    tips = [
        "Zoek eerst het cijfer dat al het vaakst in het rooster staat.",
        "Noteer kandidaten klein in de hoek van een vakje.",
    ]
    counts = (9, 8, 8)
    CLUES = {1: 40, 2: 32, 3: 26}

    def generate(self, rng, level):
        full = [0] * 81
        count_solutions([0] * 81, limit=1, rng=rng, out=full)
        grid = list(full)
        target = self.CLUES[level]
        cells = list(range(41))            # remove in 180-degree symmetric pairs
        rng.shuffle(cells)
        clues = 81
        for i in cells:
            if clues <= target:
                break
            j = 80 - i
            keep = grid[i], grid[j]
            grid[i] = grid[j] = 0
            if count_solutions(grid, 2) != 1:
                grid[i], grid[j] = keep
            else:
                clues -= 1 if i == j else 2
        if clues > target:                 # symmetry exhausted: remove singles
            cells = [i for i in range(81) if grid[i]]
            rng.shuffle(cells)
            for i in cells:
                if clues <= target:
                    break
                keep, grid[i] = grid[i], 0
                if count_solutions(grid, 2) != 1:
                    grid[i] = keep
                else:
                    clues -= 1
        return {"grid": grid, "solution": full}

    def verify(self, puz):
        grid, sol = puz["grid"], puz["solution"]
        assert len(grid) == 81 and len(sol) == 81
        for i in range(81):
            assert 1 <= sol[i] <= 9
            assert grid[i] in (0, sol[i])
            assert all(sol[p] != sol[i] for p in PEERS[i])
        assert count_solutions(grid, 2) == 1, "sudoku must be unique"

    def draw(self, c, box, puz, solved=False, part=0):
        g = Grid(box, 9, 9, max_cell=50)
        g.lines(c, lw=0.6, outer=2.4, block=(3, 3), block_lw=2.0)
        for i in range(81):
            r, col = divmod(i, 9)
            if puz["grid"][i]:
                g.given(c, r, col, puz["grid"][i])
            elif solved:
                g.answer(c, r, col, puz["solution"][i])

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        for k in range(4):
            lw = 1.8 if k in (0, 3) else 1.0
            line(c, cx - h + k * s / 3, cy - h, cx - h + k * s / 3, cy + h, lw, color, cap=2)
            line(c, cx - h, cy - h + k * s / 3, cx + h, cy - h + k * s / 3, lw, color, cap=2)
        from ..draw import text_mid
        text_mid(c, cx - s / 3, cy + s / 3, "5", "SansB", s * 0.26, color)
        text_mid(c, cx, cy, "3", "SansB", s * 0.26, color)
        text_mid(c, cx + s / 3, cy - s / 3, "7", "SansB", s * 0.26, color)


GAME = Sudoku()
