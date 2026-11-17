"""Logigram - an Einstein-style deduction puzzle with a cross-reference grid.

A handful of people each have exactly one item from every other category.
The clues pin down one single arrangement; a brute-force solver over all
arrangements guarantees that, and redundant clues are removed.
"""
from itertools import permutations, product

from reportlab.pdfbase.pdfmetrics import stringWidth

from ..draw import circle, fit_size, line, paragraph, rrect, text, text_mid, wrap
from ..theme import GREY, INK, LIGHT, PEN
from .base import Game


def _cat(label, verb, items, **extra):
    """items: (short label, object after the verb, full negative predicate,
    noun phrase for 'the one who has it')."""
    d = {"label": label, "verb": verb,
         "items": [dict(zip(("short", "obj", "neg", "who"), it)) for it in items]}
    d.update(extra)
    return d


def _ordinal_items(pattern_short, objs, neg_verb, who_fmt):
    return [(s, o, f"{neg_verb} {o}", who_fmt.format(o)) for s, o in
            zip(pattern_short, objs)]


THEMES = [
    {   # 1 ------------------------------------------------------------------
        "intro": "Deze buren wonen naast elkaar in de Kerkstraat.",
        "names": ["Emma", "Noor", "Lucas", "Finn", "Lotte", "Daan"],
        "ordered": _cat(
            "Huisnummer", "woont op",
            [(f"nr. {n}", f"nummer {n}", f"woont niet op nummer {n}",
              f"de bewoner van nummer {n}") for n in range(1, 6)],
            gt="woont op een hoger nummer dan", lt="woont op een lager nummer dan",
            adj="woont vlak naast"),
        "cats": [
            _cat("Huisdier", "heeft", [
                ("kat", "een kat", "heeft geen kat", "de eigenaar van de kat"),
                ("hond", "een hond", "heeft geen hond", "de eigenaar van de hond"),
                ("konijn", "een konijn", "heeft geen konijn", "de eigenaar van het konijn"),
                ("papegaai", "een papegaai", "heeft geen papegaai", "de eigenaar van de papegaai"),
                ("goudvis", "een goudvis", "heeft geen goudvis", "de eigenaar van de goudvis"),
            ]),
            _cat("Voordeur", "heeft", [
                ("rood", "een rode voordeur", "heeft geen rode voordeur", "de bewoner met de rode voordeur"),
                ("blauw", "een blauwe voordeur", "heeft geen blauwe voordeur", "de bewoner met de blauwe voordeur"),
                ("groen", "een groene voordeur", "heeft geen groene voordeur", "de bewoner met de groene voordeur"),
                ("geel", "een gele voordeur", "heeft geen gele voordeur", "de bewoner met de gele voordeur"),
                ("zwart", "een zwarte voordeur", "heeft geen zwarte voordeur", "de bewoner met de zwarte voordeur"),
            ]),
        ],
    },
    {   # 2 ------------------------------------------------------------------
        "intro": "Deze collega's werken in hetzelfde kantoorgebouw.",
        "names": ["Sara", "Tom", "Ines", "Bram", "Jana", "Wout"],
        "ordered": _cat(
            "Verdieping", "werkt op",
            [(f"{n}e", f"de {w} verdieping", f"werkt niet op de {w} verdieping",
              f"de collega van de {w} verdieping")
             for n, w in enumerate(["eerste", "tweede", "derde", "vierde", "vijfde"], 1)],
            gt="werkt hoger in het gebouw dan", lt="werkt lager in het gebouw dan",
            adj="werkt precies één verdieping boven of onder"),
        "cats": [
            _cat("Drankje", "drinkt", [
                ("koffie", "koffie", "drinkt geen koffie", "de koffiedrinker"),
                ("thee", "thee", "drinkt geen thee", "de theedrinker"),
                ("water", "water", "drinkt geen water", "de waterdrinker"),
                ("cola", "cola", "drinkt geen cola", "de coladrinker"),
                ("chocomelk", "chocomelk", "drinkt geen chocomelk", "de chocomelkdrinker"),
            ]),
            _cat("Vervoer", "komt met", [
                ("fiets", "de fiets", "komt niet met de fiets", "de fietser"),
                ("trein", "de trein", "komt niet met de trein", "de treinreiziger"),
                ("auto", "de auto", "komt niet met de auto", "de automobilist"),
                ("bus", "de bus", "komt niet met de bus", "de busreiziger"),
                ("step", "de step", "komt niet met de step", "de collega met de step"),
            ]),
        ],
    },
    {   # 3 ------------------------------------------------------------------
        "intro": "Deze leden van de sportclub doen elk een andere sport.",
        "names": ["Tom", "Sofie", "Bram", "Marie", "Pieter", "Lies"],
        "ordered": _cat(
            "Leeftijd", "is",
            [(f"{n} jaar", f"{n} jaar", f"is geen {n} jaar",
              f"het clublid van {n} jaar") for n in (19, 24, 31, 38, 45, 52)],
            gt="is ouder dan", lt="is jonger dan"),
        "cats": [
            _cat("Sport", "doet aan", [
                ("volleybal", "volleybal", "doet niet aan volleybal", "de volleyballer"),
                ("tennis", "tennis", "doet niet aan tennis", "de tennisser"),
                ("zwemmen", "zwemmen", "doet niet aan zwemmen", "de zwemmer"),
                ("hardlopen", "hardlopen", "doet niet aan hardlopen", "de hardloper"),
                ("padel", "padel", "doet niet aan padel", "de padelspeler"),
                ("wielrennen", "wielrennen", "doet niet aan wielrennen", "de wielrenner"),
            ]),
            _cat("Trainingsdag", "traint op", [
                (d, d, f"traint niet op {d}", f"het clublid dat op {d} traint")
                for d in ("maandag", "dinsdag", "woensdag", "donderdag", "zaterdag")
            ]),
        ],
    },
    {   # 4 ------------------------------------------------------------------
        "intro": "Deze vrienden vertrekken elk op een andere reis.",
        "names": ["Hanne", "Kobe", "Mila", "Arne", "Fien", "Jef"],
        "ordered": _cat(
            "Duur", "blijft",
            [(f"{n} dagen", f"{n} dagen weg", f"blijft geen {n} dagen weg",
              f"de reiziger die {n} dagen wegblijft") for n in (5, 7, 10, 14, 21)],
            gt="blijft langer weg dan", lt="blijft korter weg dan"),
        "cats": [
            _cat("Bestemming", "reist naar", [
                (n, n, f"reist niet naar {n}", f"de reiziger naar {n}")
                for n in ("Noorwegen", "Italië", "Tanzania", "Portugal", "Schotland")
            ]),
            _cat("Vervoer", "reist met", [
                ("camper", "de camper", "reist niet met de camper", "de reiziger met de camper"),
                ("vliegtuig", "het vliegtuig", "reist niet met het vliegtuig", "de reiziger met het vliegtuig"),
                ("trein", "de trein", "reist niet met de trein", "de reiziger met de trein"),
                ("auto", "de auto", "reist niet met de auto", "de reiziger met de auto"),
                ("fiets", "de fiets", "reist niet met de fiets", "de reiziger met de fiets"),
            ]),
        ],
    },
    {   # 5 ------------------------------------------------------------------
        "intro": "Deze bakkers deden mee aan de jaarlijkse bakwedstrijd.",
        "names": ["Marie", "Stijn", "Elke", "Koen", "Nina", "Ruben"],
        "ordered": _cat(
            "Plaats", "eindigde op",
            [(f"{n}e", f"de {w} plaats", f"eindigde niet op de {w} plaats",
              f"de bakker op de {w} plaats")
             for n, w in enumerate(["eerste", "tweede", "derde", "vierde", "vijfde"], 1)],
            gt="eindigde lager in de uitslag dan", lt="eindigde hoger in de uitslag dan",
            adj="eindigde net voor of net na"),
        "cats": [
            _cat("Gebak", "bakte", [
                ("appeltaart", "een appeltaart", "bakte geen appeltaart", "de bakker van de appeltaart"),
                ("wafels", "wafels", "bakte geen wafels", "de bakker van de wafels"),
                ("brownies", "brownies", "bakte geen brownies", "de bakker van de brownies"),
                ("cake", "een cake", "bakte geen cake", "de bakker van de cake"),
                ("vlaai", "een vlaai", "bakte geen vlaai", "de bakker van de vlaai"),
            ]),
            _cat("Schort", "droeg", [
                ("rood", "een rode schort", "droeg geen rode schort", "de bakker met de rode schort"),
                ("blauw", "een blauwe schort", "droeg geen blauwe schort", "de bakker met de blauwe schort"),
                ("geel", "een gele schort", "droeg geen gele schort", "de bakker met de gele schort"),
                ("groen", "een groene schort", "droeg geen groene schort", "de bakker met de groene schort"),
                ("wit", "een witte schort", "droeg geen witte schort", "de bakker met de witte schort"),
            ]),
        ],
    },
    {   # 6 ------------------------------------------------------------------
        "intro": "Deze leerlingen van de muziekschool hebben elk op een ander uur les.",
        "names": ["Lena", "Milan", "Olivia", "Jasper", "Zoë", "Thijs"],
        "ordered": _cat(
            "Lesuur", "heeft les om",
            [(f"{n} uur", f"{n} uur", f"heeft geen les om {n} uur",
              f"de leerling van {n} uur") for n in (14, 15, 16, 17, 18)],
            gt="heeft later les dan", lt="heeft vroeger les dan",
            adj="heeft les vlak voor of vlak na"),
        "cats": [
            _cat("Instrument", "speelt", [
                ("piano", "piano", "speelt geen piano", "de pianist"),
                ("gitaar", "gitaar", "speelt geen gitaar", "de gitarist"),
                ("viool", "viool", "speelt geen viool", "de violist"),
                ("drum", "drum", "speelt geen drum", "de drummer"),
                ("saxofoon", "saxofoon", "speelt geen saxofoon", "de saxofonist"),
            ]),
            _cat("Stijl", "houdt van", [
                ("jazz", "jazz", "houdt niet van jazz", "de jazzliefhebber"),
                ("klassiek", "klassieke muziek", "houdt niet van klassieke muziek", "de liefhebber van klassieke muziek"),
                ("rock", "rock", "houdt niet van rock", "de rockliefhebber"),
                ("pop", "pop", "houdt niet van pop", "de popliefhebber"),
                ("blues", "blues", "houdt niet van blues", "de bluesliefhebber"),
            ]),
        ],
    },
    {   # 7 ------------------------------------------------------------------
        "intro": "De leden van deze boekenclub lazen dit jaar elk een ander aantal boeken.",
        "names": ["Greet", "Luc", "Mieke", "Dirk", "Hilde", "Paul"],
        "ordered": _cat(
            "Aantal", "las",
            [(f"{n} boeken", f"{n} boeken", f"las geen {n} boeken",
              f"het lid dat {n} boeken las") for n in (4, 7, 9, 12, 15, 20)],
            gt="las meer boeken dan", lt="las minder boeken dan"),
        "cats": [
            _cat("Genre", "leest het liefst", [
                ("thrillers", "thrillers", "leest niet het liefst thrillers", "de thrillerfan"),
                ("romans", "romans", "leest niet het liefst romans", "de romanlezer"),
                ("strips", "strips", "leest niet het liefst strips", "de striplezer"),
                ("biografieën", "biografieën", "leest niet het liefst biografieën", "de lezer van biografieën"),
                ("fantasy", "fantasy", "leest niet het liefst fantasy", "de fantasyfan"),
            ]),
            _cat("Leesplek", "leest", [
                ("tuin", "in de tuin", "leest niet in de tuin", "het lid dat in de tuin leest"),
                ("trein", "in de trein", "leest niet in de trein", "het lid dat in de trein leest"),
                ("bed", "in bed", "leest niet in bed", "het lid dat in bed leest"),
                ("bad", "in bad", "leest niet in bad", "het lid dat in bad leest"),
                ("terras", "op het terras", "leest niet op het terras", "het lid dat op het terras leest"),
            ]),
        ],
    },
    {   # 8 ------------------------------------------------------------------
        "intro": "Deze kinderen bouwden elk een zandkasteel op het strand van Oostende.",
        "names": ["Lou", "Vic", "Ella", "Mats", "Juul", "Seppe"],
        "ordered": _cat(
            "Torens", "bouwde een kasteel met",
            [(f"{n} torens", f"{n} torens",
              f"bouwde geen kasteel met {n} torens",
              f"de bouwer van het kasteel met {n} torens") for n in (2, 3, 4, 5, 6)],
            gt="bouwde meer torens dan", lt="bouwde minder torens dan"),
        "cats": [
            _cat("Emmertje", "had", [
                ("rood", "een rood emmertje", "had geen rood emmertje", "het kind met het rode emmertje"),
                ("blauw", "een blauw emmertje", "had geen blauw emmertje", "het kind met het blauwe emmertje"),
                ("geel", "een geel emmertje", "had geen geel emmertje", "het kind met het gele emmertje"),
                ("groen", "een groen emmertje", "had geen groen emmertje", "het kind met het groene emmertje"),
                ("oranje", "een oranje emmertje", "had geen oranje emmertje", "het kind met het oranje emmertje"),
            ]),
            _cat("IJsje", "at", [
                ("vanille", "een vanille-ijsje", "at geen vanille-ijsje", "het kind met het vanille-ijsje"),
                ("chocolade", "een chocolade-ijsje", "at geen chocolade-ijsje", "het kind met het chocolade-ijsje"),
                ("aardbei", "een aardbeienijsje", "at geen aardbeienijsje", "het kind met het aardbeienijsje"),
                ("pistache", "een pistache-ijsje", "at geen pistache-ijsje", "het kind met het pistache-ijsje"),
                ("citroen", "een citroenijsje", "at geen citroenijsje", "het kind met het citroenijsje"),
            ]),
        ],
    },
]

SHAPE = {1: (3, 3), 2: (3, 4), 3: (4, 4)}          # level -> (categories, items)
CLUE_RANGE = {1: (3, 6), 2: (5, 8), 3: (7, 11)}
MAX_POS = {1: 1, 2: 2, 3: 3}


# --- logic ----------------------------------------------------------------------
def _states(k, n, ordered):
    """All arrangements as flat tuples.

    v[c*n + item] = person holding that item of category c (category 0 is the
    people themselves); if there is an ordered category, the tail
    v[k*n + person] is that person's rank in it."""
    perms = list(permutations(range(n)))
    ident = tuple(range(n))
    out = []
    for combo in product(perms, repeat=k - 1):
        v = list(ident)
        for fwd in combo:                 # fwd[person] = item
            inv = [0] * n
            for p, it in enumerate(fwd):
                inv[it] = p
            v.extend(inv)
        if ordered >= 0:
            v.extend(combo[ordered - 1])
        out.append(tuple(v))
    return out


def _holds(clue, n, k):
    """Compile a clue dict into a predicate over a state tuple."""
    t = clue["t"]
    i = clue["a"][0] * n + clue["a"][1]
    j = clue["b"][0] * n + clue["b"][1]
    o = k * n
    if t == "pos":
        return lambda v: v[i] == v[j]
    if t == "neg":
        return lambda v: v[i] != v[j]
    if t == "gt":
        return lambda v: v[o + v[i]] > v[o + v[j]]
    if t == "lt":
        return lambda v: v[o + v[i]] < v[o + v[j]]
    if t == "adj":
        return lambda v: abs(v[o + v[i]] - v[o + v[j]]) == 1
    if t == "or":
        j2 = clue["b2"][0] * n + clue["b2"][1]
        return lambda v: v[i] == v[j] or v[i] == v[j2]
    raise ValueError(t)


def solve(puz, limit=2):
    """Return up to ``limit`` solutions (in the puz['solution'] format)."""
    k, n = len(puz["cats"]), len(puz["cats"][0]["items"])
    states = _states(k, n, puz["ordered"])
    for clue in puz["clues"]:
        f = _holds(clue, n, k)
        states = [v for v in states if f(v)]
    out = []
    for v in states[:limit]:
        sol = []
        for c in range(k):
            inv = v[c * n:(c + 1) * n]
            fwd = [0] * n
            for it, p in enumerate(inv):
                fwd[p] = it
            sol.append(fwd)
        out.append(sol)
    return out


def _cap(s):
    return s[:1].upper() + s[1:]


class Logigram(Game):
    key = "logigram"
    name = "Logigram"
    category = "logica"
    tagline = "Wie hoort bij wat? Speel detective met een handvol aanwijzingen."
    rules = [
        "Elke persoon hoort bij precies één item uit elke andere categorie, "
        "en elk item hoort bij precies één persoon.",
        "Lees de aanwijzingen en noteer in het rooster wat zeker niet kan "
        "(kruisje) en wat zeker wel klopt (bolletje).",
        "Alle aanwijzingen samen laten precies één oplossing over.",
    ]
    tips = [
        "Een bolletje in een blok betekent kruisjes in de rest van die rij en kolom.",
        "Combineer aanwijzingen: als Emma de kat heeft en de kat niet bij "
        "nummer 2 woont, dan woont Emma daar ook niet.",
    ]
    counts = (9, 8, 8)

    # -- generation ------------------------------------------------------------
    def _text(self, clue, cats, raw):
        def ref(e):
            c, i = e
            return cats[c]["items"][i] if c == 0 else raw[c]["items"][i]["who"]

        def subj(e):
            # a relative clause ("het lid dat in bed leest") needs a comma
            # before the main verb
            s = ref(e)
            return s + "," if (" dat " in s or " die " in s) else s

        a, b = clue["a"], clue["b"]
        t = clue["t"]
        if t == "pos":
            s = f"{subj(a)} {raw[b[0]]['verb']} {raw[b[0]]['items'][b[1]]['obj']}"
        elif t == "neg":
            s = f"{subj(a)} {raw[b[0]]['items'][b[1]]['neg']}"
        elif t in ("gt", "lt", "adj"):
            s = f"{subj(a)} {raw[clue['o']][t]} {ref(b)}"
        else:
            b2 = clue["b2"]
            s = (f"{subj(a)} {raw[b[0]]['verb']} {raw[b[0]]['items'][b[1]]['obj']}"
                 f" of {raw[b2[0]]['items'][b2[1]]['obj']}")
        return _cap(s) + "."

    def generate(self, rng, level):
        k, n = SHAPE[level]
        lo, hi = CLUE_RANGE[level]
        theme_idx = rng.randrange(len(THEMES))
        theme = THEMES[theme_idx]
        for _ in range(300):
            puz = self._attempt(rng, theme, theme_idx, k, n, level)
            if puz and lo <= len(puz["clues"]) <= hi:
                return puz
        raise RuntimeError("logigram: no puzzle within the clue range")

    def _attempt(self, rng, theme, theme_idx, k, n, level):
        # choose categories: raw[c] is the theme data of category c (c >= 1)
        nominal = list(theme["cats"])
        rng.shuffle(nominal)
        use_ordered = k == 4 or rng.random() < 0.75
        chosen = ([theme["ordered"]] if use_ordered else []) + nominal
        chosen = chosen[:k - 1]
        rng.shuffle(chosen)
        ordered = chosen.index(theme["ordered"]) + 1 if use_ordered else -1
        raw = [None]
        cats = [{"label": "Naam", "items": rng.sample(theme["names"], n)}]
        for cat in chosen:
            m = len(cat["items"])
            if cat is theme["ordered"]:
                if "adj" in cat:                   # neighbours need a contiguous run
                    s = rng.randrange(m - n + 1)
                    idx = list(range(s, s + n))
                else:
                    idx = sorted(rng.sample(range(m), n))
            else:
                idx = rng.sample(range(m), n)
            sub = dict(cat)
            sub["items"] = [cat["items"][i] for i in idx]
            raw.append(sub)
            cats.append({"label": cat["label"],
                         "items": [it["short"] for it in sub["items"]]})
        solution = [list(range(n))] + [rng.sample(range(n), n) for _ in range(k - 1)]
        if len({tuple(x) for x in solution}) < k:
            return None          # a diagonal or repeated block looks odd in the grid
        owner = [[0] * n for _ in range(k)]         # owner[c][item] = person
        for c in range(k):
            for p, it in enumerate(solution[c]):
                owner[c][it] = p
        rank = solution[ordered] if ordered >= 0 else None

        ents = [(c, i) for c in range(k) for i in range(n)]
        pos, neg, cmp_, either = [], [], [], []
        for a in ents:
            for b in ents:
                if a[0] == b[0] or b[0] == 0:
                    continue
                same = owner[a[0]][a[1]] == owner[b[0]][b[1]]
                if a[0] != 0 and a[0] > b[0] and rng.random() < 0.5:
                    continue                        # avoid mirrored duplicates
                if same:
                    pos.append({"t": "pos", "a": list(a), "b": list(b)})
                    for i2 in range(n):
                        if i2 != b[1]:
                            pair = [list(b), [b[0], i2]]
                            rng.shuffle(pair)
                            either.append({"t": "or", "a": list(a),
                                           "b": pair[0], "b2": pair[1]})
                else:
                    neg.append({"t": "neg", "a": list(a), "b": list(b)})
        if ordered >= 0:
            others = [e for e in ents if e[0] != ordered]
            for a in others:
                for b in others:
                    pa, pb = owner[a[0]][a[1]], owner[b[0]][b[1]]
                    if pa == pb:
                        continue
                    t = "gt" if rank[pa] > rank[pb] else "lt"
                    cmp_.append({"t": t, "a": list(a), "b": list(b), "o": ordered})
                    if "adj" in raw[ordered] and abs(rank[pa] - rank[pb]) == 1 and a < b:
                        cmp_.append({"t": "adj", "a": list(a), "b": list(b),
                                     "o": ordered})
        rng.shuffle(pos)
        pool = pos[:MAX_POS[level]]
        rng.shuffle(neg)
        rng.shuffle(cmp_)
        rng.shuffle(either)
        pool += neg[:3 * n] + cmp_[:3 * n] + either[:2 * n]
        rng.shuffle(pool)

        states = _states(k, n, ordered)
        picked = []
        for clue in pool:
            f = _holds(clue, n, k)
            left = [v for v in states if f(v)]
            if len(left) < len(states):
                picked.append(clue)
                states = left
                if len(states) == 1:
                    break
        if len(states) != 1:
            return None
        # drop clues that the others already imply
        allstates = _states(k, n, ordered)
        fs = {id(c): _holds(c, n, k) for c in picked}
        for clue in list(picked):
            rest = [c for c in picked if c is not clue]
            left = allstates
            for c in rest:
                f = fs[id(c)]
                left = [v for v in left if f(v)]
                if len(left) <= 1:
                    break
            if len(left) == 1:
                picked = rest
        if ordered >= 0 and not any(c["t"] in ("gt", "lt", "adj") for c in picked):
            return None
        rng.shuffle(picked)
        for clue in picked:
            clue["text"] = self._text(clue, cats, raw)
        return {"theme": theme_idx, "intro": theme["intro"], "cats": cats,
                "ordered": ordered, "clues": picked, "solution": solution}

    # -- checking ----------------------------------------------------------------
    def verify(self, puz):
        k, n = len(puz["cats"]), len(puz["cats"][0]["items"])
        sol = puz["solution"]
        assert len(sol) == k and sol[0] == list(range(n))
        for c in range(k):
            assert len(puz["cats"][c]["items"]) == n
            assert sorted(sol[c]) == list(range(n)), "each item used once"
        for clue in puz["clues"]:
            assert clue["text"].endswith(".") and len(clue["text"]) > 8
        found = solve(puz, 2)
        assert len(found) == 1, f"logigram must be unique, found {len(found)}"
        assert found[0] == sol

    # -- drawing -----------------------------------------------------------------
    def instruction(self, puz, part=0):
        return ("Wie hoort bij wat? Zet in het rooster een kruisje voor ‘nee’ "
                "en een bolletje voor ‘ja’.")

    def _grid(self, c, box, puz, solved):
        """The triangular cross-reference grid, centred in box."""
        x, y, w, h = box
        cats = puz["cats"]
        k, n = len(cats), len(cats[0]["items"])
        g = k - 1
        col_groups = list(range(1, k))
        row_groups = [0] + list(range(k - 1, 1, -1))
        fs = 8.6
        strip = 13.0                                   # category name strip
        lab_w = max(stringWidth(it, "SansM", fs)
                    for cg in row_groups for it in cats[cg]["items"]) + 10
        lab_h = max(stringWidth(it, "SansM", fs)
                    for cg in col_groups for it in cats[cg]["items"]) + 10
        cell = min(36.0, (w - lab_w - strip) / (g * n), (h - lab_h - strip) / (g * n))
        tw = lab_w + strip + g * n * cell
        th = lab_h + strip + g * n * cell
        gx = x + (w - tw) / 2 + lab_w + strip          # left edge of the cells
        gy = y + h - (h - th) / 2 - lab_h - strip      # top edge of the cells
        owner = [[0] * n for _ in range(k)]
        for cc in range(k):
            for p, it in enumerate(puz["solution"][cc]):
                owner[cc][it] = p
        for gi, rc in enumerate(row_groups):
            by = gy - gi * n * cell
            # row labels + rotated category strip
            c.saveState()
            c.translate(gx - lab_w - strip + 9.5, by - n * cell / 2)
            c.rotate(90)
            text(c, 0, 0, cats[rc]["label"].upper(), "SansB", 6.8, GREY, "c")
            c.restoreState()
            for r in range(n):
                text(c, gx - 5, by - (r + 0.5) * cell - fs * 0.35,
                     cats[rc]["items"][r], "SansM", fs, INK, "r")
            for gj, cc in enumerate(col_groups[:g - gi]):
                bx = gx + gj * n * cell
                if gi == 0:
                    text(c, bx + n * cell / 2, gy + lab_h + 3.5,
                         cats[cc]["label"].upper(), "SansB", 6.8, GREY, "c")
                    for q in range(n):
                        c.saveState()
                        c.translate(bx + (q + 0.5) * cell + fs * 0.35, gy + 5)
                        c.rotate(90)
                        text(c, 0, 0, cats[cc]["items"][q], "SansM", fs, INK)
                        c.restoreState()
                for i in range(1, n):
                    line(c, bx + i * cell, by, bx + i * cell, by - n * cell, 0.5, INK, cap=2)
                    line(c, bx, by - i * cell, bx + n * cell, by - i * cell, 0.5, INK, cap=2)
                c.saveState()
                c.setLineWidth(1.8)
                c.setStrokeColor(INK)
                c.rect(bx, by - n * cell, n * cell, n * cell, stroke=1, fill=0)
                c.restoreState()
                if solved:
                    for r in range(n):
                        for q in range(n):
                            mx, my = bx + (q + 0.5) * cell, by - (r + 0.5) * cell
                            if owner[rc][r] == owner[cc][q]:
                                circle(c, mx, my, cell * 0.24, fill=PEN, stroke=None)
                            else:
                                d = cell * 0.13
                                line(c, mx - d, my - d, mx + d, my + d, 0.9, PEN)
                                line(c, mx - d, my + d, mx + d, my - d, 0.9, PEN)

    def _table(self, c, x, y_top, w, puz):
        """Answer table in pen; returns the y below it."""
        cats = puz["cats"]
        k, n = len(cats), len(cats[0]["items"])
        rh = 25.0
        cw = w / k
        for cc in range(k):
            text(c, x + cc * cw + 8, y_top - 13, cats[cc]["label"].upper(),
                 "SansB", 7.5, GREY)
        line(c, x, y_top - 19, x + w, y_top - 19, 1.4, INK)
        for p in range(n):
            yy = y_top - 19 - (p + 1) * rh
            text(c, x + 8, yy + 8, cats[0]["items"][p], "SansS", 11, INK)
            for cc in range(1, k):
                label = cats[cc]["items"][puz["solution"][cc][p]]
                text(c, x + cc * cw + 8, yy + 7, label, "Hand", 17, PEN)
            line(c, x, yy, x + w, yy, 0.5, GREY)
        return y_top - 19 - n * rh

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        top = y + h
        yy = paragraph(c, x, top, w, puz["intro"], "SansS", 10, color=INK) - 9
        if solved:
            yy = self._table(c, x, yy + 2, w, puz) - 16
        else:
            fs, lead = 9.8, 13.4
            for i, clue in enumerate(puz["clues"], 1):
                lines = wrap(clue["text"], "Sans", fs, w - 22)
                circle(c, x + 7, yy - fs * 0.62, 6.6, fill=None, stroke=INK, lw=0.9)
                text_mid(c, x + 7, yy - fs * 0.62, i, "SansB", 7.2, INK)
                for ln in lines:
                    text(c, x + 20, yy - fs, ln, "Sans", fs, INK)
                    yy -= lead
                yy -= 2.2
            yy -= 6
        self._grid(c, (x, y, w, yy - y), puz, solved)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        q = s / 3
        for i in range(4):
            lw = 1.6 if i in (0, 3) else 0.9
            line(c, cx - h + i * q, cy - h, cx - h + i * q, cy + h, lw, color, cap=2)
            line(c, cx - h, cy - h + i * q, cx + h, cy - h + i * q, lw, color, cap=2)
        circle(c, cx, cy, q * 0.28, fill=color, stroke=None)
        for (dx, dy) in ((-1, 1), (1, -1), (-1, 0)):
            mx, my, d = cx + dx * q, cy + dy * q, q * 0.22
            line(c, mx - d, my - d, mx + d, my + d, 1.1, color)
            line(c, mx - d, my + d, mx + d, my - d, 1.1, color)


GAME = Logigram()
