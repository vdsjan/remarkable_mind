"""Calcudoku - a Latin square with arithmetic cages (KenKen style)."""
from ..draw import Grid, line, rrect, text, text_mid
from ..theme import INK, PEN
from .base import Game

SIZES = {1: 4, 2: 5, 3: 6}
# cage size weights per level
WEIGHTS = {
    1: {1: 1, 2: 6, 3: 3},
    2: {1: 1, 2: 5, 3: 4, 4: 1},
    3: {1: 1, 2: 4, 3: 5, 4: 3},
}
MAX_SINGLES = {1: 2, 2: 2, 3: 2}
SYMBOL = {"+": "+", "-": "−", "*": "×", "/": "÷"}


def latin(rng, n):
    rows, cols, syms = list(range(n)), list(range(n)), list(range(1, n + 1))
    rng.shuffle(rows)
    rng.shuffle(cols)
    rng.shuffle(syms)
    return [syms[(r + c) % n] for r in rows for c in cols]


def _neighbours(i, n):
    r, c = divmod(i, n)
    if r:
        yield i - n
    if r < n - 1:
        yield i + n
    if c:
        yield i - 1
    if c < n - 1:
        yield i + 1


def make_cages(rng, n, sol, level):
    weights = WEIGHTS[level]
    sizes, wts = list(weights), list(weights.values())
    owner = [-1] * (n * n)
    groups = []
    cells = list(range(n * n))
    rng.shuffle(cells)
    for cell in cells:
        if owner[cell] >= 0:
            continue
        size = rng.choices(sizes, wts)[0]
        group = [cell]
        owner[cell] = len(groups)
        while len(group) < size:
            free = sorted({m for g in group for m in _neighbours(g, n)
                           if owner[m] < 0})
            if not free:
                break
            m = rng.choice(free)
            owner[m] = len(groups)
            group.append(m)
        groups.append(group)
    # merge surplus single cells into a neighbouring cage
    singles = [g for g in groups if len(g) == 1]
    rng.shuffle(singles)
    for g in singles[MAX_SINGLES[level]:]:
        if len(g) != 1:               # already absorbed another single
            continue
        options = sorted({owner[m] for m in _neighbours(g[0], n)
                          if owner[m] != owner[g[0]]
                          and 0 < len(groups[owner[m]]) < 4})
        if options:
            k = rng.choice(options)
            groups[k].append(g[0])
            owner[g[0]] = k
            g.clear()
    cages = []
    for group in groups:
        if not group:
            continue
        group.sort()
        vals = [sol[i] for i in group]
        if len(group) == 1:
            op, target = "=", vals[0]
        elif len(group) == 2:
            hi, lo = max(vals), min(vals)
            options = ["+", "+", "-", "-", "-", "*", "*"]
            if hi % lo == 0:
                options += ["/", "/", "/"]
            op = rng.choice(options)
            target = {"+": hi + lo, "-": hi - lo, "*": hi * lo,
                      "/": hi // lo}[op]
        else:
            prod = 1
            for v in vals:
                prod *= v
            op = "*" if prod <= 240 and rng.random() < 0.5 else "+"
            target = prod if op == "*" else sum(vals)
        cages.append({"cells": group, "op": op, "target": target})
    cages.sort(key=lambda cg: cg["cells"][0])
    return cages


def _cage_ok(op, target, vals, size, n):
    """Can a cage holding ``vals`` (so far) still reach its target?"""
    full = len(vals) == size
    if op == "=":
        return vals[0] == target
    if op == "+":
        s = sum(vals)
        rest = size - len(vals)
        return s + rest <= target <= s + rest * n if not full else s == target
    if op == "*":
        p = 1
        for v in vals:
            p *= v
        return p == target if full else target % p == 0
    if op == "-":
        if full:
            return abs(vals[0] - vals[1]) == target
        return vals[0] - target >= 1 or vals[0] + target <= n
    if op == "/":
        if full:
            hi, lo = max(vals), min(vals)
            return lo * target == hi
        return vals[0] * target <= n or vals[0] % target == 0
    return False


def count_solutions(n, cages, limit=2, out=None):
    total = n * n
    cage_of = [None] * total
    for cg in cages:
        for i in cg["cells"]:
            cage_of[i] = cg
    grid = [0] * total
    rows, cols = [0] * n, [0] * n
    found = 0

    def search(i):
        nonlocal found
        if i == total:
            found += 1
            if out is not None and found == 1:
                out[:] = grid
            return
        r, c = divmod(i, n)
        cg = cage_of[i]
        prior = [grid[j] for j in cg["cells"] if j < i]
        size = len(cg["cells"])
        for v in range(1, n + 1):
            bit = 1 << v
            if rows[r] & bit or cols[c] & bit:
                continue
            if not _cage_ok(cg["op"], cg["target"], prior + [v], size, n):
                continue
            grid[i] = v
            rows[r] |= bit
            cols[c] |= bit
            search(i + 1)
            rows[r] ^= bit
            cols[c] ^= bit
            if found >= limit:
                break
        grid[i] = 0

    search(0)
    return found


class Calcudoku(Game):
    key = "calcudoku"
    name = "Calcudoku"
    category = "getallen"
    tagline = "Sudoku ontmoet hoofdrekenen."
    rules = [
        "Vul het rooster met de cijfers 1 tot en met de roosterbreedte.",
        "In elke rij en elke kolom komt elk cijfer precies één keer voor.",
        "De cijfers in een dik omlijnd vak leveren met de bewerking het "
        "getal in de hoek op. Bij − en ÷ mag de volgorde vrij gekozen worden.",
        "Een vak van één cel is al ingevuld.",
    ]
    tips = [
        "Begin bij vakken met maar één mogelijke combinatie, zoals 3+ in "
        "twee cellen.",
        "Een cijfer mag binnen een vak wel herhaald worden, zolang het niet "
        "in dezelfde rij of kolom staat.",
    ]

    def generate(self, rng, level):
        n = SIZES[level]
        while True:
            sol = latin(rng, n)
            for _ in range(40):
                cages = make_cages(rng, n, sol, level)
                if count_solutions(n, cages, 2) == 1:
                    return {"n": n, "cages": cages, "solution": sol}

    def verify(self, puz):
        n, cages, sol = puz["n"], puz["cages"], puz["solution"]
        assert len(sol) == n * n
        for k in range(n):
            assert sorted(sol[k * n:(k + 1) * n]) == list(range(1, n + 1))
            assert sorted(sol[k::n]) == list(range(1, n + 1))
        seen = sorted(i for cg in cages for i in cg["cells"])
        assert seen == list(range(n * n)), "cages must partition the grid"
        for cg in cages:
            cells = cg["cells"]
            assert 1 <= len(cells) <= 4
            assert cg["op"] in ("=", "+", "-", "*", "/")
            if cg["op"] in ("-", "/"):
                assert len(cells) == 2
            if cg["op"] == "=":
                assert len(cells) == 1
            # contiguous
            todo, reach = [cells[0]], {cells[0]}
            while todo:
                for m in _neighbours(todo.pop(), n):
                    if m in cells and m not in reach:
                        reach.add(m)
                        todo.append(m)
            assert len(reach) == len(cells), "cage must be connected"
            assert _cage_ok(cg["op"], cg["target"], [sol[i] for i in cells],
                            len(cells), n)
        assert count_solutions(n, cages, 2) == 1, "calcudoku must be unique"

    def instruction(self, puz, part=0):
        n = puz["n"]
        return (f"Vul 1 tot {n} in: elk cijfer één keer per rij en kolom, "
                "en elk vak klopt met zijn rekenopdracht.")

    def draw(self, c, box, puz, solved=False, part=0):
        n = puz["n"]
        g = Grid(box, n, n, max_cell=84)
        cell = g.cell
        thick = min(2.8, max(1.2, cell * 0.045))
        g.lines(c, lw=0.6, outer=thick)
        owner = {}
        for k, cg in enumerate(puz["cages"]):
            for i in cg["cells"]:
                owner[i] = k
        for i in range(n * n):
            r, col = divmod(i, n)
            if col < n - 1 and owner[i] != owner[i + 1]:
                line(c, g.x(col + 1), g.y(r), g.x(col + 1), g.y(r + 1),
                     thick, INK, cap=2)
            if r < n - 1 and owner[i] != owner[i + n]:
                line(c, g.x(col), g.y(r + 1), g.x(col + 1), g.y(r + 1),
                     thick, INK, cap=2)
        for cg in puz["cages"]:
            first = cg["cells"][0]
            r, col = divmod(first, n)
            if cg["op"] == "=":
                g.given(c, r, col, cg["target"], scale=0.5)
                continue
            label = f"{cg['target']}{SYMBOL[cg['op']]}"
            text(c, g.x(col) + cell * 0.08, g.y(r) - cell * 0.27, label,
                 "SansB", cell * 0.205, INK)
        if solved:
            single = {cg["cells"][0] for cg in puz["cages"] if cg["op"] == "="}
            for i in range(n * n):
                if i in single:
                    continue
                r, col = divmod(i, n)
                text_mid(c, g.cx(col), g.cy(r) - cell * 0.09,
                         puz["solution"][i], "Hand", cell * 0.6, PEN)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        rrect(c, cx - h, cy - h, s, s, 2, stroke=color, lw=1.8)
        line(c, cx, cy - h, cx, cy, 1.8, color, cap=2)
        line(c, cx - h, cy, cx + h, cy, 1.8, color, cap=2)
        text_mid(c, cx, cy + s * 0.25, "6×", "SansB", s * 0.3, color)
        text_mid(c, cx - s * 0.25, cy - s * 0.25, "+", "SansB", s * 0.34, color)
        text_mid(c, cx + s * 0.25, cy - s * 0.25, "÷", "SansB", s * 0.34, color)


GAME = Calcudoku()
