"""Lucifers - matchstick equations in seven-segment digits.

A wrong sum is laid out in matches. Move exactly one (or, on the hardest
level, exactly two) matches so the sum becomes true. A brute-force search
over every possible move guarantees exactly one way to do it.
"""
import math

from ..draw import line, text, text_mid
from ..theme import GREY, INK, MID, MUSTARD, PEN, RED, WHITE
from .base import Game

# segment bits: a top, b top-right, c bottom-right, d bottom, e bottom-left,
# f top-left, g middle
SEG = "abcdefg"
_DIGIT_SEGS = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
               5: "afgcd", 6: "afgecd", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
DIGIT = {d: sum(1 << SEG.index(s) for s in segs) for d, segs in _DIGIT_SEGS.items()}
MASK2DIGIT = {m: d for d, m in DIGIT.items()}
OP = {"+": 0b11, "-": 0b01}           # bit 0 = horizontal, bit 1 = vertical
MASK2OP = {m: o for o, m in OP.items()}


def _pop(x):
    return bin(x).count("1")


def _options(masks):
    """For every valid mask: the valid masks reachable, with (removed, added)."""
    return {m: [(m2, _pop(m & ~m2), _pop(m2 & ~m)) for m2 in masks] for m in masks}


OPT_DIGIT = _options(list(DIGIT.values()))
OPT_OP = _options(list(OP.values()))


def parse(eq):
    """'12+3=15' -> (shape, slots) with slots = [('d', mask) | ('o', mask)]."""
    left, c = eq.split("=")
    for op in "+-":
        k = left.find(op, 1)
        if k > 0:
            a, b = left[:k], left[k + 1:]
            break
    else:
        raise ValueError(eq)
    slots = [("d", DIGIT[int(ch)]) for ch in a] + [("o", OP[op])]
    slots += [("d", DIGIT[int(ch)]) for ch in b]
    slots += [("d", DIGIT[int(ch)]) for ch in c]
    return (len(a), len(b), len(c)), slots


def unparse(shape, masks):
    la, lb, lc = shape
    it = iter(masks)
    a = "".join(str(MASK2DIGIT[next(it)]) for _ in range(la))
    op = MASK2OP[next(it)]
    b = "".join(str(MASK2DIGIT[next(it)]) for _ in range(lb))
    c = "".join(str(MASK2DIGIT[next(it)]) for _ in range(lc))
    return f"{a}{op}{b}={c}"


def well_formed(eq):
    left, c = eq.split("=")
    op = "+" if "+" in left else "-"
    a, b = left.split(op)
    return all(len(n) == 1 or n[0] != "0" for n in (a, b, c))


def is_true(eq):
    left, c = eq.split("=")
    op = "+" if "+" in left else "-"
    a, b = left.split(op)
    return (int(a) + int(b) if op == "+" else int(a) - int(b)) == int(c)


def neighbours(eq, k):
    """All well-formed equations obtained by moving exactly k matches."""
    shape, slots = parse(eq)
    out = []

    def rec(i, rem, add, acc):
        if i == len(slots):
            if rem == k and add == k:
                out.append(unparse(shape, acc))
            return
        kind, m = slots[i]
        for m2, r, a in (OPT_DIGIT if kind == "d" else OPT_OP)[m]:
            if rem + r <= k and add + a <= k:
                rec(i + 1, rem + r, add + a, acc + [m2])

    rec(0, 0, 0, [])
    return [e for e in out if well_formed(e)]


_TRUE_CACHE = {}


def true_equations(shape):
    """Every true, well-formed equation with the given digit counts."""
    if shape in _TRUE_CACHE:
        return _TRUE_CACHE[shape]
    la, lb, lc = shape

    def rng_(n):
        return range(0 if n == 1 else 10 ** (n - 1), 10 ** n)

    out = []
    for a in rng_(la):
        for b in rng_(lb):
            for op, c in (("+", a + b), ("-", a - b)):
                if c >= 0 and len(str(c)) == lc:
                    out.append(f"{a}{op}{b}={c}")
    _TRUE_CACHE[shape] = out
    return out


def _bits(eq):
    """Whole equation as one integer bit mask (7 bits per slot)."""
    _, slots = parse(eq)
    v = 0
    for _, m in slots:
        v = (v << 7) | m
    return v


def solutions(eq, k):
    """True equations reachable from eq by moving exactly k matches
    (independent of ``neighbours``: compares against every true equation)."""
    shape, _ = parse(eq)
    s = _bits(eq)
    res = []
    for t in true_equations(shape):
        tb = _bits(t)
        if _pop(s & ~tb) == k and _pop(tb & ~s) == k:
            res.append(t)
    return res


SHAPES = {
    1: [(1, 1, 1), (1, 1, 1), (1, 1, 2)],
    2: [(2, 1, 1), (2, 1, 2), (1, 2, 2), (2, 2, 2), (2, 2, 1)],
    3: [(1, 1, 1), (1, 1, 2), (2, 1, 2), (2, 1, 1)],
}


class Lucifers(Game):
    key = "lucifers"
    name = "Lucifers"
    category = "ruimte"
    tagline = "De som klopt niet. Eén lucifer verleggen en ze klopt wel."
    rules = [
        "De som in lucifers is fout. Verplaats precies het gevraagde aantal "
        "lucifers zodat ze klopt.",
        "Je mag geen lucifers wegnemen of bijleggen, en het =-teken blijft staan.",
        "Elk cijfer blijft een geldig cijfer; van een + mag je een − maken en omgekeerd.",
    ]
    tips = [
        "Met één lucifer verandert een 6 in een 9 of een 0, een 3 in een 2 of een 5.",
        "Tel de lucifers: een 8 heeft er zeven, een 1 maar twee. Wie geeft af, wie krijgt bij?",
    ]
    counts = (9, 8, 8)

    def generate(self, rng, level):
        k = 2 if level == 3 else 1
        for _ in range(500):
            shape = rng.choice(SHAPES[level])
            pool = [e for e in true_equations(shape)
                    if not e.startswith("0") and "+0" not in e and "-0" not in e]
            target = rng.choice(pool)
            cands = [e for e in neighbours(target, k) if not is_true(e)]
            rng.shuffle(cands)
            for shown in cands[:12]:
                sols = solutions(shown, k)
                if len(sols) != 1:
                    continue
                if k == 2 and solutions(shown, 1):
                    continue
                return {"shown": shown, "answer": sols[0], "moves": k}
        raise RuntimeError("lucifers: no puzzle found")

    def verify(self, puz):
        shown, answer, k = puz["shown"], puz["answer"], puz["moves"]
        assert k in (1, 2)
        assert well_formed(shown) and well_formed(answer)
        assert not is_true(shown), "the shown equation must be wrong"
        assert is_true(answer), "the answer must be a true equation"
        s, a = _bits(shown), _bits(answer)
        assert _pop(s & ~a) == k and _pop(a & ~s) == k, "exactly k matches move"
        assert solutions(shown, k) == [answer], "solution must be unique"
        assert sorted(e for e in neighbours(shown, k) if is_true(e)) == [answer]
        if k == 2:
            assert not solutions(shown, 1), "must really need two moves"

    def instruction(self, puz, part=0):
        n = "één lucifer" if puz["moves"] == 1 else "twee lucifers"
        return f"Verplaats precies {n} zodat de som klopt."

    # -- drawing -----------------------------------------------------------------
    @staticmethod
    def _match(c, x1, y1, x2, y2, L, style="wood"):
        """One match from (x1, y1) to (x2, y2); the head sits at the second end."""
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        length = math.hypot(x2 - x1, y2 - y1)
        t = L * 0.115
        gap = L * 0.075
        c.saveState()
        c.translate(x1, y1)
        c.rotate(ang)
        if style == "ghost":
            c.setStrokeColor(MID)
            c.setLineWidth(0.8)
            c.setDash(2.2, 2.2)
            c.roundRect(gap, -t / 2, length - 2 * gap, t, t / 2, stroke=1, fill=0)
        else:
            body = PEN if style == "pen" else MUSTARD
            c.setStrokeColor(PEN if style == "pen" else INK)
            c.setLineWidth(0.9)
            c.setFillColor(body)
            c.roundRect(gap, -t / 2, length - 2 * gap, t, t / 2, stroke=1, fill=1)
            c.setFillColor(WHITE if style == "pen" else RED)
            hl, ht = L * 0.2, t * 1.75
            c.ellipse(length - gap - hl, -ht / 2, length - gap + L * 0.02, ht / 2,
                      stroke=1, fill=1)
        c.restoreState()

    @staticmethod
    def _segments(kind, x, y, L):
        """bit index -> (x1, y1, x2, y2) for a slot whose bottom-left is (x, y)."""
        if kind == "d":
            return {
                0: (x, y + 2 * L, x + L, y + 2 * L),
                1: (x + L, y + L, x + L, y + 2 * L),
                2: (x + L, y, x + L, y + L),
                3: (x, y, x + L, y),
                4: (x, y, x, y + L),
                5: (x, y + L, x, y + 2 * L),
                6: (x, y + L, x + L, y + L),
            }
        w = 0.8 * L
        if kind == "o":
            return {0: (x, y + L, x + w, y + L),
                    1: (x + w / 2, y + L - w / 2, x + w / 2, y + L + w / 2)}
        return {0: (x, y + L + 0.2 * L, x + w, y + L + 0.2 * L),      # '='
                1: (x, y + L - 0.2 * L, x + w, y + L - 0.2 * L)}

    def _row(self, c, x, y, w, max_l, shown, compare=None, ghost=False):
        """Draw an equation centred in width w with its baseline at y.

        compare: the original equation; matches that differ are highlighted.
        ghost: draw an empty template (all segments dotted) to write on."""
        shape, slots = parse(shown)
        base = parse(compare)[1] if compare else slots
        la, lb, _ = shape
        seq = []                                  # (kind, mask, base mask)
        for i, (kind, m) in enumerate(slots):
            if i == la + 1 + lb:
                seq.append(("e", 0b11, 0b11))
            seq.append((kind, m, base[i][1]))
        adv = {"d": 1.5, "o": 1.42, "e": 1.42}
        wid = {"d": 1.0, "o": 0.8, "e": 0.8}
        units = 0.0
        for i, (kind, _, _) in enumerate(seq):
            # operators get a little air on both sides
            units += adv[kind] if i < len(seq) - 1 else wid[kind]
            if kind in "oe":
                units += 0.2
        L = min(max_l, (w - 10) / units)          # keep match heads inside the box
        cx = x + (w - units * L) / 2
        for kind, m, bm in seq:
            if kind in "oe":
                cx += 0.2 * L
            segs = self._segments(kind, cx, y, L)
            for bit, (x1, y1, x2, y2) in segs.items():
                on, was = m >> bit & 1, bm >> bit & 1
                if ghost:
                    self._match(c, x1, y1, x2, y2, L,
                                "wood" if kind == "e" else "ghost")
                elif on:
                    self._match(c, x1, y1, x2, y2, L, "wood" if was else "pen")
                elif was:
                    self._match(c, x1, y1, x2, y2, L, "ghost")
            cx += adv[kind] * L
        return L

    @staticmethod
    def _pretty(eq):
        out = eq.replace("+", " + ").replace("-", " − ").replace("=", " = ")
        return out

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        shape, _ = parse(puz["shown"])
        max_l = 54 if sum(shape) <= 4 else 46
        if not solved:
            L = self._row(c, x, y + h * 0.60, w, max_l, puz["shown"])
            line(c, x, y + h * 0.50, x + w, y + h * 0.50, 0.6, MID, dash=(1, 3))
            text(c, x, y + h * 0.50 - 16, "Teken hier jouw oplossing:", "SansM",
                 9, GREY)
            self._row(c, x, y + h * 0.50 - 34 - 2 * L, w, max_l, puz["shown"],
                      ghost=True)
        else:
            text(c, x, y + h - 12, "Opgave", "SansM", 9, GREY)
            self._row(c, x, y + h - 22 - 2 * 30, w, 30, puz["shown"])
            line(c, x, y + h - 100, x + w, y + h - 100, 0.6, MID, dash=(1, 3))
            n = puz["moves"]
            label = ("Oplossing: de blauwe lucifer is verlegd" if n == 1 else
                     "Oplossing: de twee blauwe lucifers zijn verlegd")
            text(c, x, y + h - 118, label, "SansM", 9, GREY)
            self._row(c, x, y + h - 140 - 2 * max_l, w, max_l, puz["answer"],
                      compare=puz["shown"])
            text(c, x + w / 2, y + h - 140 - 2 * max_l - 70,
                 self._pretty(puz["answer"]), "Hand", 46, PEN, "c")

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        for dx, tilt in ((-0.28, -0.12), (0.05, 0.1), (0.36, -0.05)):
            x1, y1 = cx + dx * s - tilt * s, cy - h
            x2, y2 = cx + dx * s + tilt * s, cy + h * 0.7
            line(c, x1, y1, x2, y2, 1.6, color)
            c.saveState()
            c.setFillColor(color)
            c.circle(x2, y2 + s * 0.06, s * 0.1, stroke=0, fill=1)
            c.restoreState()


GAME = Lucifers()
