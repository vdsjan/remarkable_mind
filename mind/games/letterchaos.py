"""Letterchaos - themed anagrams; marked letters reveal a bonus word."""
from ..draw import circle, icon_chevron, rrect, text, text_mid
from ..theme import GREY, INK, MUSTARD, PEN, WHITE
from ._woorden import BONUS, THEMES
from .base import Game

LEVELS = {1: (8, 4, 6), 2: (9, 6, 8), 3: (10, 8, 12)}   # words, min len, max len
ALL_WORDS = {w for _, words, _ in THEMES for w in words}


def _scramble(rng, word):
    """Shuffle so that at most a third of the letters keep their place."""
    letters = list(word)
    best = None
    for _ in range(200):
        rng.shuffle(letters)
        s = "".join(letters)
        same = sum(a == b for a, b in zip(s, word))
        if s in ALL_WORDS:                 # never show another real theme word
            continue
        if best is None or same < best[0]:
            best = (same, s)
            if same * 3 <= len(word) and s[:3] != word[:3]:
                break
    return best[1]


def _match(rng, bonus, pool):
    """Pick, for every bonus letter in order, a different word containing it."""
    chosen = []

    def rec(i):
        if i == len(bonus):
            return True
        cands = [w for w in pool if bonus[i] in w and w not in chosen]
        rng.shuffle(cands)
        for w in cands[:6]:
            chosen.append(w)
            if rec(i + 1):
                return True
            chosen.pop()
        return False

    return chosen if rec(0) else None


class Letterchaos(Game):
    key = "letterchaos"
    name = "Letterchaos"
    category = "taal"
    tagline = "De letters liggen door elkaar. Welke woorden zitten erin?"
    rules = [
        "Elke rij is een woord uit het thema, maar de letters staan door elkaar.",
        "Zet de letters in de juiste volgorde en schrijf het woord in de vakjes.",
        "De letters in de gele vakjes vormen van boven naar beneden het bonuswoord.",
    ]
    tips = [
        "Zoek vaste lettergroepen zoals SCH, IJ, OE, EI of -ING.",
        "Zit je vast? Het bonuswoord verklapt soms een letter.",
    ]
    counts = (9, 8, 8)
    example = False

    def generate(self, rng, level):
        n, lo, hi = LEVELS[level]
        for _ in range(500):
            title, words, _ = rng.choice(THEMES)
            pool = [w for w in words if lo <= len(w) <= hi]
            if len(pool) < n + 2:
                continue
            bonus = rng.choice(BONUS[n])
            chosen = _match(rng, bonus, pool)
            if not chosen:
                continue
            items = []
            for letter, word in zip(bonus, chosen):
                spots = [i for i, ch in enumerate(word) if ch == letter]
                items.append([_scramble(rng, word), word, rng.choice(spots)])
            return {"theme": title, "items": items, "bonus": bonus}
        raise RuntimeError("letterchaos: geen passende woorden gevonden")

    def verify(self, puz):
        theme = [t for t in THEMES if t[0] == puz["theme"]]
        assert theme, "onbekend thema"
        words = theme[0][1]
        answers = [it[1] for it in puz["items"]]
        assert len(set(answers)) == len(answers)
        for scramble, answer, hi in puz["items"]:
            assert answer in words
            assert sorted(scramble) == sorted(answer) and scramble != answer
            twins = [w for w in words if w != answer and sorted(w) == sorted(answer)]
            assert not twins, f"{answer} heeft een anagram in het thema: {twins}"
            assert 0 <= hi < len(answer)
        bonus = "".join(answer[hi] for _, answer, hi in puz["items"])
        assert bonus == puz["bonus"]
        assert bonus in BONUS[len(bonus)]

    def fingerprints(self, puz):
        """Keys that should not repeat within one book (builder may re-roll)."""
        return [f"thema:{puz['theme']}:{len(puz['items'])}", f"bonus:{puz['bonus']}"]

    def instruction(self, puz, part=0):
        return (f"Thema: {puz['theme']}. Ontwar de woorden; de gele vakjes "
                "vormen het bonuswoord.")

    # -- drawing ----------------------------------------------------------------
    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        items = puz["items"]
        n = len(items)
        maxlen = max(len(it[1]) for it in items)
        num_w = 26.0
        pitch = min(22.0, 176.0 / maxlen)            # scrambled tiles
        tile = pitch - 2.0
        left_w = maxlen * pitch
        gap = 22.0
        bw = min(30.0, (w - num_w - left_w - gap) / maxlen)   # answer boxes
        bonus_h = 58.0
        row_h = min(48.0, (h - bonus_h) / n)
        bh = min(bw, row_h - 9)
        top = y + h
        bx0 = x + num_w + left_w + gap
        for i, (scramble, answer, hi) in enumerate(items):
            cy = top - (i + 0.5) * row_h
            circle(c, x + 9, cy, 9, fill=INK, stroke=None)
            text_mid(c, x + 9, cy, i + 1, "SansB", 9.5, WHITE)
            for j, ch in enumerate(scramble):
                tx = x + num_w + j * pitch + pitch / 2
                rot = ((i * 37 + j * 23) % 7 - 3) * 3.0
                c.saveState()
                c.translate(tx, cy)
                c.rotate(rot)
                rrect(c, -tile / 2, -tile / 2, tile, tile, 3, stroke=INK, lw=0.9)
                text_mid(c, 0, 0, ch, "SansB", tile * 0.62, INK)
                c.restoreState()
            icon_chevron(c, bx0 - gap / 2, cy, 9, 1, GREY, 1.5)
            for j in range(len(answer)):
                bx = bx0 + j * bw
                c.saveState()
                c.setStrokeColor(INK)
                c.setLineWidth(1.0)
                if j == hi:
                    c.setFillColor(MUSTARD)
                c.rect(bx, cy - bh / 2, bw, bh, stroke=1, fill=1 if j == hi else 0)
                c.restoreState()
                if solved:
                    text_mid(c, bx + bw / 2, cy, answer[j], "Hand", bh * 0.86, PEN)
        # bonus word
        k = len(puz["bonus"])
        bb = 26.0
        total = k * bb
        by = y + 6
        bx = x + w - total
        text(c, bx - 12, by + bb / 2 - 4, "Bonuswoord", "SerifB", 13, INK, "r")
        for j, ch in enumerate(puz["bonus"]):
            c.saveState()
            c.setStrokeColor(INK)
            c.setLineWidth(1.3)
            c.setFillColor(MUSTARD)
            c.rect(bx + j * bb, by, bb, bb, stroke=1, fill=1)
            c.restoreState()
            if solved:
                text_mid(c, bx + j * bb + bb / 2, by + bb / 2, ch, "Hand", 22, PEN)

    def icon(self, c, cx, cy, s, color):
        t = s * 0.42
        for (dx, dy, rot, ch) in ((-0.28, 0.24, -14, "B"), (0.26, 0.2, 10, "A"),
                                  (-0.2, -0.26, 8, "C"), (0.28, -0.24, -9, "D")):
            c.saveState()
            c.translate(cx + dx * s, cy + dy * s)
            c.rotate(rot)
            rrect(c, -t / 2, -t / 2, t, t, 2, stroke=color, lw=1.4)
            text_mid(c, 0, 0, ch, "SansB", t * 0.62, color)
            c.restoreState()


GAME = Letterchaos()
