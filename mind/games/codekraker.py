"""Codekraker - a Dutch proverb hidden behind a number-for-letter cipher."""
from .. import theme
from ..draw import line, paragraph, rrect, text, text_mid, wrap
from ..theme import GREY, INK, LIGHT, PEN
from ._woorden import SPREEKWOORDEN
from .base import Game

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GIVEN = {1: 5, 2: 3, 3: 1}


def _plain(proverb):
    return "".join(ch for ch in proverb.upper() if ch in ALPHABET or ch == " ")


def _by_level():
    """Split the proverbs in three groups by length; level 3 gets the longest."""
    items = sorted(SPREEKWOORDEN, key=lambda p: (len(_plain(p[0]).replace(" ", "")), p[0]))
    third = len(items) // 3
    return {1: items[:third], 2: items[third:2 * third], 3: items[2 * third:]}


class Codekraker(Game):
    key = "codekraker"
    name = "Codekraker"
    category = "taal"
    tagline = "Elk cijfer is een letter. Kraak de code en lees het spreekwoord."
    rules = [
        "Elk getal staat voor één vaste letter; dezelfde letter heeft overal "
        "hetzelfde getal.",
        "Enkele letters zijn al ingevuld. Vul de rest in tot er een bekend "
        "Nederlands spreekwoord staat.",
        "Hou in de sleutel onderaan bij welk getal bij welke letter hoort.",
    ]
    tips = [
        "De E en de N komen in het Nederlands het vaakst voor.",
        "Korte woorden zoals DE, HET, EEN, IS en IN verraden veel.",
    ]
    counts = (9, 8, 8)
    example = False

    def generate(self, rng, level):
        proverb, meaning = rng.choice(_by_level()[level])
        text_ = _plain(proverb)
        numbers = list(range(1, 27))
        rng.shuffle(numbers)                       # numbers[i] codes ALPHABET[i]
        present = sorted(set(text_.replace(" ", "")))
        freq = sorted(present, key=lambda ch: (-text_.count(ch), ch))
        k = GIVEN[level]
        if level == 1:                             # the two commonest + 3 others
            given = freq[:2] + rng.sample(freq[2:], k - 2)
        elif level == 2:                           # one common + 2 others
            given = freq[:1] + rng.sample(freq[1:], k - 1)
        else:                                      # one of the commoner letters
            given = [rng.choice(freq[1:5])]
        cipher = [[numbers[ALPHABET.index(ch)] for ch in word]
                  for word in text_.split()]
        return {"text": text_, "code": numbers, "cipher": cipher,
                "given": sorted(given), "meaning": meaning}

    def verify(self, puz):
        code = puz["code"]
        assert sorted(code) == list(range(1, 27))
        decode = {n: ALPHABET[i] for i, n in enumerate(code)}
        plain = " ".join("".join(decode[n] for n in word) for word in puz["cipher"])
        assert plain == puz["text"]
        assert all(ch in ALPHABET or ch == " " for ch in plain)
        assert 24 <= len(plain.replace(" ", "")) <= 60
        assert puz["given"] and all(g in plain for g in puz["given"])
        assert len(set(puz["given"])) == len(puz["given"])
        assert len(set(plain.replace(" ", ""))) >= len(puz["given"]) + 3
        assert any(_plain(p) == plain and m == puz["meaning"]
                   for p, m in SPREEKWOORDEN)

    def fingerprints(self, puz):
        """Keys that should not repeat within one book (builder may re-roll)."""
        return [f"spreekwoord:{puz['text']}"]

    def instruction(self, puz, part=0):
        return "Elk getal is een letter. Kraak de code en lees het spreekwoord."

    # -- drawing ----------------------------------------------------------------
    def _layout(self, words, width, bw):
        """Wrap words into lines of at most `width`; returns list of lines."""
        space = bw * 0.7
        lines, cur, cur_w = [], [], 0.0
        for word in words:
            ww = len(word) * bw
            if cur and cur_w + space + ww > width:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur_w += (space if cur else 0) + ww
            cur.append(word)
        lines.append(cur)
        return lines

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        code = puz["code"]
        decode = {n: ALPHABET[i] for i, n in enumerate(code)}
        given = set(puz["given"])
        used = set(puz["text"].replace(" ", ""))

        # --- key strip: A-Z with a box for the number --------------------------
        compact = theme.COMPACT
        per_row = 9 if compact else 13            # narrow page: three rows
        nrows = -(-26 // per_row)
        kw = w / per_row
        kh = 22.0
        strip_h = nrows * (kh + 15) + 16
        text(c, x, y + strip_h - 9, "SLEUTEL", "SansB", 8, INK)
        line(c, x + 44, y + strip_h - 6, x + w, y + strip_h - 6, 0.8, INK)
        for i, ch in enumerate(ALPHABET):
            row, col = divmod(i, per_row)
            kx = x + col * kw
            ky = y + (nrows - 1 - row) * (kh + 15)
            text_mid(c, kx + kw / 2, ky + kh + 7, ch, "SansB", 10.5, INK)
            rrect(c, kx + 3, ky, kw - 6, kh, 3,
                  fill=LIGHT if ch in given else None, stroke=INK, lw=0.9)
            if ch in given:
                text_mid(c, kx + kw / 2, ky + kh / 2, code[i], "SansS", 11, INK)
            elif solved and ch in used:
                text_mid(c, kx + kw / 2, ky + kh / 2, code[i], "Hand", 16, PEN)
            elif solved:
                line(c, kx + kw / 2 - 4, ky + kh / 2, kx + kw / 2 + 4, ky + kh / 2,
                     0.9, GREY)

        # --- the coded sentence ------------------------------------------------
        area_y = y + strip_h + 14
        if compact:
            mean_lines = wrap("Betekenis: " + puz["meaning"], "HandM", 14, w - 20)
            reserve = len(mean_lines) * 15 + 10
        else:
            reserve = 46
        area_h = h - strip_h - 14 - (reserve if solved else 0)
        bw = 30.0
        while True:
            lines = self._layout(puz["cipher"], w, bw)
            row_h = bw + 15 + bw * 0.45
            if len(lines) * row_h <= area_h or bw <= 16:
                break
            bw -= 1.0
        block_h = len(lines) * row_h - bw * 0.45
        top = area_y + area_h - max(0.0, (area_h - block_h) * 0.35)
        space = bw * 0.7
        yy = top - bw
        for ln in lines:
            lw_ = sum(len(wd) * bw for wd in ln) + space * (len(ln) - 1)
            xx = x + (w - lw_) / 2
            for word in ln:
                for n in word:
                    ch = decode[n]
                    c.saveState()
                    c.setStrokeColor(INK)
                    c.setLineWidth(1.0)
                    if ch in given:
                        c.setFillColor(LIGHT)
                        c.rect(xx, yy, bw, bw, stroke=1, fill=1)
                    else:
                        c.rect(xx, yy, bw, bw, stroke=1, fill=0)
                    c.restoreState()
                    if ch in given:
                        text_mid(c, xx + bw / 2, yy + bw / 2, ch, "SansB", bw * 0.56, INK)
                    elif solved:
                        text_mid(c, xx + bw / 2, yy + bw / 2, ch, "Hand", bw * 0.82, PEN)
                    text_mid(c, xx + bw / 2, yy - 7.5, n, "SansM", min(8.5, bw * 0.36), INK)
                    xx += bw
                xx += space
            yy -= row_h
        if solved and compact:
            paragraph(c, x + 10, yy + row_h - bw * 0.2 - 12, w - 20,
                      "Betekenis: " + puz["meaning"], "HandM", 14, 15, PEN, "c")
        elif solved:
            paragraph(c, x + 10, yy + row_h - bw * 0.2 - 18, w - 20,
                      "Betekenis: " + puz["meaning"], "HandM", 16, 18, PEN, "c")

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        rrect(c, cx - h * 0.8, cy - h, s * 0.8, s * 0.58, 3, stroke=color, lw=1.6)
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(1.6)
        c.arc(cx - h * 0.45, cy - h * 0.25, cx + h * 0.45, cy + h, 0, 180)
        c.restoreState()
        line(c, cx - h * 0.45, cy + h * 0.16, cx - h * 0.45, cy + h * 0.4, 1.6, color)
        line(c, cx + h * 0.45, cy + h * 0.16, cx + h * 0.45, cy + h * 0.4, 1.6, color)
        text_mid(c, cx, cy - h * 0.42, "7", "SansB", s * 0.3, color)


GAME = Codekraker()
