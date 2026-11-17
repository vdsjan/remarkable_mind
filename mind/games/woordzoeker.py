"""Woordzoeker - themed word search whose leftover letters spell a solution."""
import math

from ..draw import Grid, circle, line, rrect, text, text_mid
from ..theme import GREY, INK, PEN
from ._woorden import GENERIC_SOLUTIONS, THEMES
from .base import Game

E, S, SE, NE, W_, N, NW, SW = ((0, 1), (1, 0), (1, 1), (-1, 1),
                               (0, -1), (-1, 0), (-1, -1), (1, -1))
ALL_DIRS = (E, S, SE, NE, W_, N, NW, SW)
LEVELS = {
    # size, directions, word lengths, most leftover letters allowed
    1: (11, (E, S, SE), (4, 8), 22),
    2: (13, (E, S, SE, NE, W_, N), (4, 10), 28),
    3: (15, ALL_DIRS, (5, 12), 36),
}


def letters(phrase):
    return phrase.replace(" ", "")


def occurrences(rows, word):
    """Number of distinct places where word can be read in any direction."""
    n = len(rows)
    L = len(word)
    found = set()
    for r in range(n):
        for c in range(n):
            if rows[r][c] != word[0]:
                continue
            for dr, dc in ALL_DIRS:
                er, ec = r + dr * (L - 1), c + dc * (L - 1)
                if not (0 <= er < n and 0 <= ec < n):
                    continue
                if all(rows[r + dr * k][c + dc * k] == word[k] for k in range(L)):
                    found.add(frozenset(((r, c), (er, ec))))
    return len(found)


def _placements(grid, n, word, dirs):
    """All (new_cells, overlaps, r, c, dr, dc) where word fits."""
    L = len(word)
    out = []
    for dr, dc in dirs:
        r_lo = (L - 1) if dr < 0 else 0
        r_hi = n - (L - 1) if dr > 0 else n
        c_lo = (L - 1) if dc < 0 else 0
        c_hi = n - (L - 1) if dc > 0 else n
        for r in range(r_lo, r_hi):
            for c in range(c_lo, c_hi):
                new = 0
                rr, cc = r, c
                for ch in word:
                    g = grid[rr][cc]
                    if g is None:
                        new += 1
                    elif g != ch:
                        new = -1
                        break
                    rr += dr
                    cc += dc
                if new > 0:
                    out.append((new, L - new, r, c, dr, dc))
    return out


def _attempt(rng, words, n, dirs, targets, max_left):
    grid = [[None] * n for _ in range(n)]
    left = n * n
    placed = []
    lo = min(targets)
    order = list(words)
    rng.shuffle(order)
    order.sort(key=lambda w: -len(w) + rng.random() * 3)   # long words first
    for word in order:
        if left in targets and left <= max_left:
            break
        if any(word in p[0] or p[0] in word or word[::-1] in p[0]
               or p[0][::-1] in word for p in placed):
            continue
        cand = [p for p in _placements(grid, n, word, dirs) if left - p[0] >= lo]
        if not cand:
            continue
        hits = [p for p in cand if left - p[0] in targets and left - p[0] <= max_left]
        if hits:
            choice = rng.choice(hits)
        else:
            # prefer crossings: they knit the grid together and keep it dense
            best = max(p[1] for p in cand)
            pool = [p for p in cand if p[1] >= best - 1]
            choice = rng.choice(pool)
        new, _, r, c, dr, dc = choice
        for k, ch in enumerate(word):
            grid[r + dr * k][c + dc * k] = ch
        left -= new
        placed.append([word, r, c, dr, dc])
    if left in targets and left <= max_left:
        return grid, placed, left
    return None


class Woordzoeker(Game):
    key = "woordzoeker"
    name = "Woordzoeker"
    category = "taal"
    tagline = "Speur alle woorden op en ontdek de verborgen oplossing."
    rules = [
        "Zoek alle woorden uit de lijst in het letterveld en streep ze door.",
        "Woorden staan horizontaal, verticaal of diagonaal; op de hogere "
        "niveaus ook achterstevoren.",
        "Letters mogen in meer dan één woord gebruikt worden.",
        "De overgebleven letters vormen, van links naar rechts gelezen, de oplossing.",
    ]
    tips = [
        "Begin met de langste woorden: die vallen het snelst op.",
        "Zoek naar opvallende letters zoals de J, de Z of een dubbele klinker.",
    ]
    counts = (9, 8, 8)
    example = False

    def generate(self, rng, level):
        n, dirs, (lo, hi), max_left = LEVELS[level]
        for attempt in range(400):
            title, words, phrases = rng.choice(THEMES)
            pool = [w for w in words if lo <= len(w) <= hi]
            cands = [p for p in phrases if len(letters(p)) <= max_left]
            if attempt >= 150:                      # last resort
                cands = cands + [p for p in GENERIC_SOLUTIONS
                                 if 6 <= len(letters(p)) <= max_left]
            targets = {len(letters(p)) for p in cands}
            if not targets:
                continue
            res = _attempt(rng, pool, n, dirs, targets, max_left)
            if not res:
                continue
            grid, placed, left = res
            phrase = rng.choice([p for p in cands if len(letters(p)) == left])
            fill = iter(letters(phrase))
            rows = ["".join(ch if ch else next(fill) for ch in row) for row in grid]
            if all(occurrences(rows, p[0]) == 1 for p in placed):
                placed.sort(key=lambda p: p[0])
                return {"theme": title, "size": n, "grid": rows,
                        "words": placed, "solution": phrase}
        raise RuntimeError("woordzoeker: geen passend rooster gevonden")

    def verify(self, puz):
        rows, n = puz["grid"], puz["size"]
        assert len(rows) == n and all(len(r) == n and r.isalpha() and r.isupper()
                                      for r in rows)
        used = [[False] * n for _ in range(n)]
        names = [p[0] for p in puz["words"]]
        assert len(set(names)) == len(names)
        for word, r, c, dr, dc in puz["words"]:
            assert (dr, dc) in ALL_DIRS
            for k, ch in enumerate(word):
                rr, cc = r + dr * k, c + dc * k
                assert 0 <= rr < n and 0 <= cc < n and rows[rr][cc] == ch
                used[rr][cc] = True
            assert occurrences(rows, word) == 1, f"{word} staat er niet precies 1 keer"
        rest = "".join(rows[r][c] for r in range(n) for c in range(n)
                       if not used[r][c])
        assert rest == letters(puz["solution"]), (rest, puz["solution"])
        assert len(rest) >= 4

    def instruction(self, puz, part=0):
        return (f"Thema: {puz['theme']}. Streep alle woorden door; de "
                "overgebleven letters vormen de oplossing.")

    # -- drawing ----------------------------------------------------------------
    def _slots(self, phrase, width, slot=13.0, gap=3.0, word_gap=9.0):
        """Lay the answer blanks out in lines; returns list of lines of words."""
        lines, cur, cur_w = [], [], 0.0
        for word in phrase.split():
            ww = len(word) * (slot + gap) - gap
            if cur and cur_w + word_gap + ww > width:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur_w += (word_gap if cur else 0) + ww
            cur.append(word)
        lines.append(cur)
        return lines

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        n = puz["size"]
        words = [p[0] for p in puz["words"]]
        cols = 4
        nrows = math.ceil(len(words) / cols)
        lead = 11.6
        list_h = nrows * lead + 4
        slot, gap, word_gap = 13.0, 3.0, 9.0
        label_w = 62.0
        lines = self._slots(puz["solution"], w - label_w, slot, gap, word_gap)
        sol_h = len(lines) * 22.0 + 4
        g = Grid((x, y + sol_h + list_h + 12, w, h - sol_h - list_h - 12), n, n,
                 max_cell=36, valign="top")
        pad = 5
        rrect(c, g.x(0) - pad, g.y(n) - pad, g.w + 2 * pad, g.h + 2 * pad, 8,
              stroke=INK, lw=1.6)
        used = set()
        for word, r, col, dr, dc in puz["words"]:
            for k in range(len(word)):
                used.add((r + dr * k, col + dc * k))
        for r in range(n):
            for col in range(n):
                rest = solved and (r, col) not in used
                g.put(c, r, col, puz["grid"][r][col],
                      "SansB" if rest else "SansM", 0.58, PEN if rest else INK)
        if solved:
            rad = g.cell * 0.40
            for word, r, col, dr, dc in puz["words"]:
                length = (len(word) - 1) * g.cell * math.hypot(dr, dc)
                c.saveState()
                c.translate(g.cx(col), g.cy(r))
                c.rotate(math.degrees(math.atan2(-dr, dc)))
                c.setStrokeColor(PEN)
                c.setLineWidth(1.1)
                c.roundRect(-rad, -rad, length + 2 * rad, 2 * rad, rad,
                            stroke=1, fill=0)
                c.restoreState()
        # word list
        top = g.y(n) - pad - 14
        col_w = w / cols
        for i, word in enumerate(words):
            ci, ri = divmod(i, nrows)
            wx, wy = x + ci * col_w + 4, top - ri * lead
            text(c, wx, wy, word, "SansM", 8.6, GREY if solved else INK)
            if solved:
                from reportlab.pdfbase.pdfmetrics import stringWidth
                line(c, wx - 1, wy + 3, wx + stringWidth(word, "SansM", 8.6) + 1,
                     wy + 3, 0.8, PEN)
        # answer blanks
        sy = top - nrows * lead - 16
        text(c, x, sy + 2, "Oplossing", "SansS", 9.5, INK)
        for ln in lines:
            sx = x + label_w
            for word in ln:
                for ch in word:
                    line(c, sx, sy, sx + slot, sy, 1.0, INK)
                    if solved:
                        text_mid(c, sx + slot / 2, sy + 7.5, ch, "Hand", 17, PEN)
                    sx += slot + gap
                sx += word_gap - gap
            sy -= 22.0

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        for i, ch in enumerate("AZ"):
            text_mid(c, cx - h * 0.55 + i * h * 0.75, cy + h * 0.5, ch, "SansB",
                     s * 0.30, color)
        text_mid(c, cx - h * 0.55, cy - h * 0.35, "W", "SansB", s * 0.30, color)
        r = s * 0.23
        circle(c, cx + h * 0.25, cy - h * 0.2, r, stroke=color, lw=1.6)
        line(c, cx + h * 0.25 + r * 0.72, cy - h * 0.2 - r * 0.72,
             cx + h * 0.95, cy - h * 0.95, 2.0, color)


GAME = Woordzoeker()
