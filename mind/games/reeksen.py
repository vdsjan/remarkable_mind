"""Getallenreeksen - find the rule, write the missing number."""
from ..draw import circle, fit_size, line, rrect, text, text_mid
from ..theme import INK, MID, PEN
from .base import Game

PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
          67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
LIMIT = {1: 600, 2: 3000, 3: 9999}
OPS = {"+": "+", "-": "−", "*": "×"}


# --- rules: machine readable, so answers can be recomputed ------------------
def expand(rule, n):
    """First n terms of the sequence described by rule."""
    t = rule["type"]
    if t == "cycle":            # apply ops in turn: [["+", 3], ["*", 2]]
        out = [rule["start"]]
        ops = rule["ops"]
        while len(out) < n:
            op, k = ops[(len(out) - 1) % len(ops)]
            v = out[-1]
            out.append(v + k if op == "+" else v - k if op == "-" else v * k)
        return out
    if t == "affine":           # next = previous * k + c
        out = [rule["start"]]
        while len(out) < n:
            out.append(out[-1] * rule["k"] + rule["c"])
        return out
    if t == "growdiff":         # differences d, d+e, d+2e, ...
        out, d = [rule["start"]], rule["d"]
        while len(out) < n:
            out.append(out[-1] + d)
            d += rule["e"]
        return out
    if t == "diffgeom":         # differences d, d*r, d*r*r, ...
        out, d = [rule["start"]], rule["d"]
        while len(out) < n:
            out.append(out[-1] + d)
            d *= rule["r"]
        return out
    if t == "power":            # (n0 + i) ** p + c
        return [(rule["n0"] + i) ** rule["p"] + rule["c"] for i in range(n)]
    if t == "fib":              # sum of the previous len(start) terms
        out = list(rule["start"])
        k = len(out)
        while len(out) < n:
            out.append(sum(out[-k:]))
        return out[:n]
    if t == "mulgrow":          # factors f, f+1, f+2, ...
        out, f = [rule["start"]], rule["f"]
        while len(out) < n:
            out.append(out[-1] * f)
            f += 1
        return out
    if t == "primes":
        return PRIMES[rule["i0"]:rule["i0"] + n]
    if t == "interleave":
        a = expand(rule["a"], (n + 1) // 2)
        b = expand(rule["b"], n // 2)
        out = []
        for i in range(n):
            out.append(a[i // 2] if i % 2 == 0 else b[i // 2])
        return out
    raise ValueError(t)


def _op(op, k):
    return f"{OPS[op]}{k}"


def explain(rule):
    """Short Dutch description of the rule."""
    t = rule["type"]
    if t == "cycle":
        ops = rule["ops"]
        if len(ops) == 1:
            return f"telkens {_op(*ops[0])}"
        if len(ops) == 2:
            return f"om de beurt {_op(*ops[0])} en {_op(*ops[1])}"
        return "steeds opnieuw " + ", ".join(_op(*o) for o in ops)
    if t == "affine":
        c = rule["c"]
        return f"telkens ×{rule['k']} en dan {'+' if c > 0 else '−'}{abs(c)}"
    if t == "growdiff":
        d, e = rule["d"], rule["e"]
        return f"het verschil groeit: +{d}, +{d + e}, +{d + 2 * e} …"
    if t == "diffgeom":
        d, r = rule["d"], rule["r"]
        return f"het verschil wordt telkens ×{r}: +{d}, +{d * r}, +{d * r * r} …"
    if t == "power":
        n0, c = rule["n0"], rule["c"]
        word, sup = ("kwadraten", "²") if rule["p"] == 2 else ("derdemachten", "³")
        tail = "" if c == 0 else f", telkens {'+' if c > 0 else '−'}{abs(c)}"
        return f"{word}: {n0}{sup}, {n0 + 1}{sup}, {n0 + 2}{sup} …{tail}"
    if t == "fib":
        if len(rule["start"]) == 2:
            return "elk getal is de som van de twee vorige"
        return "elk getal is de som van de drie vorige"
    if t == "mulgrow":
        f = rule["f"]
        return f"de factor groeit: ×{f}, ×{f + 1}, ×{f + 2} …"
    if t == "primes":
        return "opeenvolgende priemgetallen"
    if t == "interleave":
        return ("twee reeksen door elkaar: " + _short(rule["a"]) + " en "
                + _short(rule["b"]))
    raise ValueError(t)


def _short(rule):
    return explain(rule).replace("telkens ", "")


# --- makers: each returns (rule, number of terms) ----------------------------
def m_arith_up(rng):
    return {"type": "cycle", "start": rng.randint(1, 20),
            "ops": [["+", rng.randint(2, 9)]]}, 7


def m_arith_down(rng):
    d = rng.randint(2, 8)
    return {"type": "cycle", "start": d * 6 + rng.randint(1, 15),
            "ops": [["-", d]]}, 7


def m_geom(rng):
    if rng.random() < 0.6:
        return {"type": "cycle", "start": rng.randint(1, 5),
                "ops": [["*", 2]]}, 7
    return {"type": "cycle", "start": rng.randint(1, 2), "ops": [["*", 3]]}, 6


def m_alt_add(rng):
    a, b = rng.sample(range(1, 8), 2)
    if rng.random() < 0.5:
        return {"type": "cycle", "start": rng.randint(1, 12),
                "ops": [["+", a], ["+", b]]}, 7
    a, b = max(a, b) + 1, min(a, b)
    return {"type": "cycle", "start": rng.randint(2, 12),
            "ops": [["+", a], ["-", b]]}, 7


def m_squares(rng):
    return {"type": "power", "n0": rng.randint(1, 4), "p": 2, "c": 0}, 7


def m_grow_easy(rng):
    return {"type": "growdiff", "start": rng.randint(1, 6),
            "d": rng.randint(1, 2), "e": 1}, 7


def m_grow(rng):
    return {"type": "growdiff", "start": rng.randint(1, 12),
            "d": rng.randint(2, 5), "e": rng.randint(2, 3)}, 7


def m_fib(rng):
    a = rng.randint(1, 5)
    return {"type": "fib", "start": [a, rng.randint(a, a + 4)]}, 7


def m_affine(rng):
    k = rng.choice([2, 2, 3])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    return {"type": "affine", "start": rng.randint(2, 5), "k": k, "c": c}, 6


def m_mul_sub(rng):
    ops = rng.choice([[["*", 2], ["-", 1]], [["*", 2], ["-", 3]],
                      [["*", 3], ["-", 2]], [["+", 3], ["*", 2]],
                      [["*", 2], ["+", 1]], [["+", 2], ["*", 2]]])
    return {"type": "cycle", "start": rng.randint(2, 4), "ops": ops}, 7


def m_inter_arith(rng):
    d1, d2 = rng.sample(range(2, 8), 2)
    a = {"type": "cycle", "start": rng.randint(1, 10), "ops": [["+", d1]]}
    if rng.random() < 0.5:
        b = {"type": "cycle", "start": rng.randint(20, 40), "ops": [["+", d2]]}
    else:
        b = {"type": "cycle", "start": d2 * 4 + rng.randint(15, 30),
             "ops": [["-", d2]]}
    return {"type": "interleave", "a": a, "b": b}, 8


def m_power_offset(rng):
    if rng.random() < 0.6:
        return {"type": "power", "n0": rng.randint(1, 5), "p": 2,
                "c": rng.choice([-2, -1, 1, 2, 3])}, 7
    return {"type": "power", "n0": 1, "p": 3, "c": 0}, 6


def m_primes(rng):
    return {"type": "primes", "i0": rng.randint(0, 5)}, 7


def m_alt_big(rng):
    b = rng.randint(3, 9)
    a = b + rng.randint(2, 9)
    return {"type": "cycle", "start": rng.randint(5, 30),
            "ops": [["+", a], ["-", b]]}, 7


def m_inter_mixed(rng):
    a = {"type": "cycle", "start": rng.randint(1, 4), "ops": [["*", 2]]}
    d = rng.randint(3, 9)
    if rng.random() < 0.5:
        b = {"type": "cycle", "start": rng.randint(5, 30), "ops": [["+", d]]}
    else:
        b = {"type": "cycle", "start": d * 4 + rng.randint(20, 40),
             "ops": [["-", d]]}
    if rng.random() < 0.5:
        a, b = b, a
    return {"type": "interleave", "a": a, "b": b}, 8


def m_trib(rng):
    if rng.random() < 0.5:
        a = rng.randint(1, 3)
        return {"type": "fib", "start": [a, a + rng.randint(0, 2),
                                         a + rng.randint(1, 4)]}, 7
    a = rng.randint(3, 9)
    return {"type": "fib", "start": [a, rng.randint(a + 2, a + 9)]}, 7


def m_affine_hard(rng):
    k = rng.choice([2, 3, 3])
    c = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    return {"type": "affine", "start": rng.randint(3, 7), "k": k, "c": c}, 6


def m_diffgeom(rng):
    return {"type": "diffgeom", "start": rng.randint(1, 15),
            "d": rng.randint(1, 3), "r": rng.choice([2, 2, 3])}, 7


def m_grow_hard(rng):
    return {"type": "growdiff", "start": rng.randint(2, 20),
            "d": rng.randint(3, 9), "e": rng.randint(3, 6)}, 7


def m_cubes(rng):
    if rng.random() < 0.5:
        return {"type": "power", "n0": rng.randint(1, 3), "p": 3,
                "c": rng.choice([-2, -1, 1, 2])}, 6
    return {"type": "power", "n0": rng.randint(4, 9), "p": 2,
            "c": rng.choice([-5, -3, 4, 6])}, 7


def m_mulgrow(rng):
    return {"type": "mulgrow", "start": rng.randint(1, 3),
            "f": rng.randint(1, 2)}, 6


def m_cycle3(rng):
    a, b = rng.randint(2, 6), rng.randint(1, 4)
    ops = rng.choice([[["+", a], ["*", 2], ["-", b]],
                      [["*", 2], ["+", a], ["-", b]],
                      [["+", a], ["+", a + b], ["-", b]]])
    return {"type": "cycle", "start": rng.randint(1, 5), "ops": ops}, 7


POOLS = {
    1: [m_arith_up, m_arith_down, m_geom, m_alt_add, m_squares, m_grow_easy],
    2: [m_grow, m_fib, m_affine, m_mul_sub, m_inter_arith, m_power_offset,
        m_primes, m_alt_big],
    3: [m_inter_mixed, m_trib, m_affine_hard, m_diffgeom, m_grow_hard,
        m_cubes, m_mulgrow, m_cycle3],
}
ROWS = 6


class Reeksen(Game):
    key = "reeksen"
    name = "Getallenreeksen"
    category = "getallen"
    tagline = "Ontdek de regel, vind het ontbrekende getal."
    rules = [
        "Elke rij getallen volgt een vaste regel.",
        "Zoek de regel en schrijf het getal op dat op de plaats van het "
        "vraagteken hoort.",
        "De regel kan optellen, aftrekken, vermenigvuldigen of een mix "
        "daarvan zijn.",
    ]
    tips = [
        "Schrijf de verschillen tussen buren onder de rij: vaak zit de "
        "regel daarin.",
        "Zie je geen patroon? Bekijk dan om en om de getallen: misschien "
        "zijn het twee reeksen door elkaar.",
    ]
    example = False

    def generate(self, rng, level):
        makers = rng.sample(POOLS[level], ROWS)
        rows = []
        for make in makers:
            while True:
                rule, n = make(rng)
                terms = expand(rule, n)
                if (all(0 <= v <= LIMIT[level] for v in terms)
                        and len(set(terms)) >= n - 1):
                    break
            blank = n - 1
            if level == 3 and rng.random() < 0.5:
                blank = rng.randint(2, n - 3)
            rows.append({"terms": terms, "blank": blank, "rule": rule})
        return {"rows": rows}

    def verify(self, puz):
        rows = puz["rows"]
        assert len(rows) == ROWS
        for row in rows:
            terms, blank = row["terms"], row["blank"]
            assert 6 <= len(terms) <= 8
            assert 0 <= blank < len(terms)
            assert expand(row["rule"], len(terms)) == terms, \
                "terms must follow the stored rule"
            assert all(isinstance(v, int) and 0 <= v <= 9999 for v in terms)
            assert explain(row["rule"])
            shown = [v for i, v in enumerate(terms) if i != blank]
            assert len(shown) >= 5, "enough terms to find the rule"

    def instruction(self, puz, part=0):
        return ("Welk getal hoort op de plaats van het vraagteken? Zoek voor "
                "elke rij de regel.")

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        rows = puz["rows"]
        rh = h / len(rows)
        k = min(1.0, rh / 76.0)
        lab = 34 * k
        gap = 5 * k
        for idx, row in enumerate(rows):
            top = y + h - idx * rh
            terms, blank = row["terms"], row["blank"]
            n = len(terms)
            bw = min(56 * k, (w - lab - gap * (n - 1)) / n)
            bh = 40 * k
            by = top - 6 * k - bh
            circle(c, x + 12 * k, by + bh / 2, 11 * k, stroke=INK, lw=1.2)
            text_mid(c, x + 12 * k, by + bh / 2, "ABCDEF"[idx], "SansB",
                     11 * k, INK)
            for i, v in enumerate(terms):
                bx = x + lab + i * (bw + gap)
                if i == blank:
                    rrect(c, bx, by, bw, bh, 5 * k, stroke=INK, lw=2.2)
                    if solved:
                        s = str(v)
                        size = fit_size(s, "Hand", bw - 6, 27 * k)
                        text_mid(c, bx + bw / 2, by + bh / 2, s, "Hand",
                                 size, PEN)
                    else:
                        text_mid(c, bx + bw / 2, by + bh / 2, "?", "SansB",
                                 18 * k, MID)
                else:
                    rrect(c, bx, by, bw, bh, 5 * k, stroke=INK, lw=0.8)
                    s = str(v)
                    size = fit_size(s, "SansS", bw - 8, 17 * k)
                    text_mid(c, bx + bw / 2, by + bh / 2, s, "SansS", size,
                             INK)
            if solved:
                s = explain(row["rule"])
                size = fit_size(s, "Hand", w - lab, 17 * k)
                text(c, x + lab, by - 19 * k, s, "Hand", size, PEN)
            if idx < len(rows) - 1:
                line(c, x, top - rh, x + w, top - rh, 0.5, MID, dash=(1, 3))

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        w = s / 4
        for k, height in enumerate((0.25, 0.5, 0.75)):
            bx = cx - h + k * w
            rrect(c, bx + 1, cy - h, w - 2, s * height, 1, stroke=color,
                  lw=1.5)
        text_mid(c, cx + h - w / 2, cy + s * 0.02, "?", "SansX", s * 0.5,
                 color)


GAME = Reeksen()
