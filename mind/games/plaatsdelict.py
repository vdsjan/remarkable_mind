"""Plaats delict - put every suspect on the floor plan, then name the thief.

Inspired by Murdoku: exactly one suspect per row and per column, and a list
of statements about where they stood. Each puzzle has one placement that
fits every statement; the thief is the only suspect who stood in the room
the loot was taken from.
"""
from .. import theme
from ..draw import (circle, fit_size, line, paragraph, polyline, rrect, star,
                    text, text_mid, wrap)
from ..theme import GREY, INK, PEN, RED, WHITE
from .base import Game

# --- material ------------------------------------------------------------------
# object key -> (name with article, short name for the legend)
OBJECTS = {
    "trap": ("de trap", "trap"), "piano": ("de piano", "piano"),
    "klok": ("de klok", "klok"), "plant": ("de plant", "plant"),
    "vitrine": ("de vitrine", "vitrine"), "kluis": ("de kluis", "kluis"),
    "kist": ("de kist", "kist"), "beeld": ("het beeld", "beeld"),
    "vat": ("het vat", "vat"), "anker": ("het anker", "anker"),
    "kast": ("de kast", "kast"), "spiegel": ("de spiegel", "spiegel"),
    "lamp": ("de lamp", "lamp"), "bank": ("de bank", "bank"),
    "kar": ("de kar", "kar"), "put": ("de put", "put"),
}


def _room(label, phrase=None):
    """(label on the plan, 'in de keuken')."""
    het = {"depot", "atelier", "kantoor", "archief", "café", "clubhuis", "loket"}
    return [label, phrase or f"in {'het' if label in het else 'de'} {label}"]


# title, rooms, plain objects, loot options (object key, what was stolen), suspects
SCENARIOS = [
    ("Landhuis Ravenstein",
     [_room("keuken"), _room("salon"), _room("hal"), _room("serre"),
      _room("eetkamer"), _room("kelder")],
     ["trap", "piano", "klok", "plant", "spiegel", "lamp"],
     [("vitrine", "het zilveren bestek"), ("kluis", "de familiejuwelen"),
      ("kast", "een kostbaar horloge")],
     ["de tuinman", "de butler", "de kokkin", "de gravin", "de chauffeur", "de notaris"]),
    ("Museum De Oude Waag",
     [_room("hal"), _room("depot"), _room("atelier"), _room("winkel"),
      _room("kelder"), _room("galerij")],
     ["beeld", "trap", "bank", "plant", "lamp", "klok"],
     [("vitrine", "een gouden munt"), ("kluis", "de schets van een oude meester"),
      ("kist", "een antieke vaas")],
     ["de suppoost", "de directeur", "de restaurator", "de gids", "de bewaker",
      "de conservator"]),
    ("Hotel Bellevue",
     [_room("lobby"), _room("bar"), _room("keuken"), _room("kantoor"),
      _room("suite"), _room("terras", "op het terras")],
     ["trap", "piano", "plant", "lamp", "spiegel", "bank"],
     [("kluis", "de dagopbrengst"), ("kast", "een parelketting"),
      ("vitrine", "een fles zeldzame cognac")],
     ["de portier", "de barman", "de kok", "de gast", "de receptionist", "de directrice"]),
    ("Kasteel Hoogveld",
     [_room("toren"), _room("kapel"), _room("zaal"), _room("kelder"),
      _room("keuken"), _room("stal")],
     ["trap", "beeld", "vat", "put", "lamp", "bank"],
     [("kist", "de kroon van de graaf"), ("kast", "een zilveren beker"),
      ("vitrine", "het oude zegel")],
     ["de kasteelheer", "de gids", "de tuinier", "de smid", "de archivaris", "de barones"]),
    ("Jachthaven Zuiderdiep",
     [_room("steiger", "op de steiger"), _room("clubhuis"), _room("loods"),
      _room("werf", "op de werf"), _room("kantoor"), _room("terras", "op het terras")],
     ["anker", "vat", "bank", "kar", "lamp", "plant"],
     [("kluis", "de clubkas"), ("kist", "een antiek kompas"),
      ("kast", "de wisselbeker")],
     ["de havenmeester", "de schipper", "de zeilmaker", "de monteur", "de voorzitter",
      "de kapitein"]),
    ("Stadsbibliotheek",
     [_room("leeszaal"), _room("archief"), _room("hal"), _room("depot"),
      _room("café"), _room("kelder")],
     ["kast", "trap", "klok", "plant", "bank", "lamp"],
     [("vitrine", "een middeleeuws handschrift"), ("kluis", "een eerste druk"),
      ("kist", "een verzameling oude kaarten")],
     ["de bibliothecaris", "de student", "de conciërge", "de professor", "de archivaris",
      "de dichteres"]),
    ("Theater De Schouwburg",
     [_room("foyer"), _room("zaal"), _room("podium", "op het podium"), _room("loge"),
      _room("bar"), _room("kassa", "bij de kassa")],
     ["piano", "spiegel", "trap", "lamp", "bank", "plant"],
     [("kluis", "de recette"), ("kast", "de hoofdprijs van het gala"),
      ("kist", "een kostbaar kostuum")],
     ["de regisseur", "de souffleur", "de actrice", "de decorbouwer", "de pianist",
      "de technicus"]),
    ("Wijngoed De Zonneberg",
     [_room("kelder"), _room("schuur"), _room("winkel"), _room("kantoor"),
      _room("keuken"), _room("terras", "op het terras")],
     ["vat", "kar", "trap", "plant", "bank", "put"],
     [("kist", "een topfles uit 1961"), ("kluis", "het geheime recept"),
      ("kast", "de gouden medaille")],
     ["de wijnboer", "de keldermeester", "de plukster",
      "de sommelier", "de boekhouder", "de leverancier"]),
    ("Station Noord",
     [_room("hal"), _room("perron", "op het perron"), _room("kiosk", "bij de kiosk"),
      _room("café"), _room("kantoor"), _room("depot")],
     ["klok", "bank", "kar", "trap", "plant", "lamp"],
     [("kluis", "de dagkas"), ("kast", "een koffer vol documenten"),
      ("kist", "een zending postzegels")],
     ["de conducteur", "de machinist", "de reiziger", "de stationschef", "de kruier",
      "de bloemist"]),
    ("Hoeve De Linde",
     [_room("stal"), _room("schuur"), _room("keuken"), _room("kelder"),
      _room("zolder", "op de zolder"), _room("tuin")],
     ["put", "kar", "vat", "trap", "bank", "plant"],
     [("kist", "het spaargeld"), ("kast", "het familiezilver"),
      ("kluis", "de eigendomsakte")],
     ["de boer", "de knecht", "de veearts", "de postbode", "de melkboer", "de smid"]),
    ("Antiekbeurs Het Pakhuis",
     [_room("hal"), _room("loods"), _room("kantoor"), _room("depot"),
      _room("bar"), _room("zolder", "op de zolder")],
     ["klok", "spiegel", "beeld", "lamp", "kar", "piano"],
     [("vitrine", "een ring met een robijn"), ("kist", "een stel oude munten"),
      ("kluis", "het geld van de veiling")],
     ["de veilingmeester", "de handelaar", "de taxateur", "de sjouwer", "de bezoekster",
      "de juwelier"]),
    ("Sterrenwacht De Uitkijk",
     [_room("koepel", "in de koepel"), _room("hal"), _room("archief"), _room("kantoor"),
      _room("kelder"), _room("winkel")],
     ["trap", "klok", "kast", "lamp", "plant", "bank"],
     [("vitrine", "een stuk meteoriet"), ("kluis", "het logboek van de ontdekking"),
      ("kist", "een antieke telescooplens")],
     ["de astronoom", "de student", "de gids", "de opticien", "de fotograaf",
      "de nachtwaker"]),
]

# level -> (grid size, rooms, plain objects, most clues, most direct room clues)
LEVELS = {1: (4, 4, 2, 5, 9), 2: (5, 5, 3, 7, 2), 3: (6, 6, 4, 9, 1)}
# The 7.3" Paper Pro Move keeps the plan at 5 x 5; level 3 then has no
# statement that names a suspect's room.
LEVELS_COMPACT = {1: (4, 4, 2, 5, 9), 2: (5, 5, 3, 7, 2), 3: (5, 5, 3, 8, 0)}
WEIGHTS = {
    1: {"room": 5, "next": 4, "see": 2, "notroom": 1, "corner": 2, "north": 1, "west": 1,
        "same": 1, "alone": 1, "nextp": 1, "notsee": 0.5},
    2: {"room": 2, "next": 3, "see": 3, "notroom": 1.5, "corner": 2, "north": 2, "west": 2,
        "same": 2, "alone": 2, "nextp": 2, "notsee": 1},
    3: {"room": 0.4, "next": 2, "see": 3, "notroom": 2, "corner": 1.5, "north": 3, "west": 3,
        "same": 3, "alone": 3, "nextp": 2, "notsee": 2},
}
DIRECT = ("room",)


# --- the logic of the statements ---------------------------------------------------
def sees(objects, cell, k):
    """True if cell is in the row or column of object k with no other object
    between them."""
    r, c = cell
    orow, ocol = objects[k][0], objects[k][1]
    if (r, c) == (orow, ocol) or (r != orow and c != ocol):
        return False
    for j, (r2, c2, _) in enumerate(objects):
        if j == k:
            continue
        if r == orow == r2 and min(c, ocol) < c2 < max(c, ocol):
            return False
        if c == ocol == c2 and min(r, orow) < r2 < max(r, orow):
            return False
    return True


def touches(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def unary_ok(puz, clue, cell):
    """Statements about one suspect and the plan."""
    kind = clue[0]
    n, rooms, objects = puz["n"], puz["rooms"], puz["objects"]
    if kind == "room":
        return rooms[cell[0]][cell[1]] == clue[2]
    if kind == "notroom":
        return rooms[cell[0]][cell[1]] != clue[2]
    if kind == "next":
        return touches(cell, objects[clue[2]][:2])
    if kind == "see":
        return sees(objects, cell, clue[2])
    if kind == "notsee":
        return not sees(objects, cell, clue[2])
    if kind == "corner":
        return cell[0] in (0, n - 1) and cell[1] in (0, n - 1)
    raise AssertionError(kind)


def binary_ok(puz, clue, a, b):
    """Statements about two suspects standing on cells a and b."""
    kind = clue[0]
    rooms = puz["rooms"]
    if kind == "same":
        return rooms[a[0]][a[1]] == rooms[b[0]][b[1]]
    if kind == "north":
        return a[0] < b[0]
    if kind == "west":
        return a[1] < b[1]
    if kind == "nextp":
        return touches(a, b)
    raise AssertionError(kind)


UNARY = ("room", "notroom", "next", "see", "notsee", "corner")
BINARY = ("same", "north", "west", "nextp")


def holds(puz, clue, placement):
    """Is the statement true for this complete placement?"""
    if clue[0] in UNARY:
        return unary_ok(puz, clue, tuple(placement[clue[1]]))
    if clue[0] in BINARY:
        return binary_ok(puz, clue, tuple(placement[clue[1]]), tuple(placement[clue[2]]))
    assert clue[0] == "alone"
    rooms = puz["rooms"]
    me = rooms[placement[clue[1]][0]][placement[clue[1]][1]]
    return sum(rooms[r][c] == me for r, c in placement) == 1


def solve(puz, clues=None, limit=2):
    """All placements (up to limit) with one suspect per row and column that
    fit every statement. A placement is a list of [row, col] per suspect."""
    clues = puz["clues"] if clues is None else clues
    n = puz["n"]
    rooms = puz["rooms"]
    k = len(puz["suspects"])
    taken = {(o[0], o[1]) for o in puz["objects"]}
    domains = []
    for p in range(k):
        mine = [cl for cl in clues if cl[0] in UNARY and cl[1] == p]
        domains.append([(r, c) for r in range(n) for c in range(n)
                        if (r, c) not in taken
                        and all(unary_ok(puz, cl, (r, c)) for cl in mine)])
    pairs = [cl for cl in clues if cl[0] in BINARY]
    alone = [cl[1] for cl in clues if cl[0] == "alone"]
    order = sorted(range(k), key=lambda p: len(domains[p]))
    place = [None] * k
    rows, cols = set(), set()
    found = []

    def fits(p, cell):
        for cl in pairs:
            if cl[1] == p and place[cl[2]] is not None:
                if not binary_ok(puz, cl, cell, place[cl[2]]):
                    return False
            elif cl[2] == p and place[cl[1]] is not None:
                if not binary_ok(puz, cl, place[cl[1]], cell):
                    return False
        room = rooms[cell[0]][cell[1]]
        for q in range(k):
            other = place[q]
            if other is None or rooms[other[0]][other[1]] != room:
                continue
            if p in alone or q in alone:
                return False
        return True

    def rec(i):
        if len(found) >= limit:
            return
        if i == k:
            found.append([list(cell) for cell in place])
            return
        p = order[i]
        for cell in domains[p]:
            if cell[0] in rows or cell[1] in cols or not fits(p, cell):
                continue
            place[p] = cell
            rows.add(cell[0])
            cols.add(cell[1])
            rec(i + 1)
            place[p] = None
            rows.discard(cell[0])
            cols.discard(cell[1])

    rec(0)
    return found


def thief_of(puz, placement):
    """The only suspect in the room the loot was taken from, or None."""
    lr, lc = puz["objects"][puz["loot"]][:2]
    room = puz["rooms"][lr][lc]
    inside = [p for p, (r, c) in enumerate(placement) if puz["rooms"][r][c] == room]
    return inside[0] if len(inside) == 1 else None


def clue_text(puz, clue):
    kind = clue[0]
    who = puz["suspects"][clue[1]][1]
    start = who[0].upper() + who[1:]
    if kind == "room":
        return f"{start} stond {puz['room_names'][clue[2]][1]}."
    if kind == "notroom":
        return f"{start} stond niet {puz['room_names'][clue[2]][1]}."
    if kind in ("next", "see", "notsee"):
        obj = OBJECTS[puz["objects"][clue[2]][2]][0]
        return {"next": f"{start} stond naast {obj}.",
                "see": f"{start} kon {obj} zien.",
                "notsee": f"{start} kon {obj} niet zien."}[kind]
    if kind == "corner":
        return f"{start} stond in een hoek van de plattegrond."
    if kind == "alone":
        return f"{start} stond alleen in een ruimte."
    other = puz["suspects"][clue[2]][1]
    return {"same": f"{start} en {other} stonden in dezelfde ruimte.",
            "north": f"{start} stond noordelijker dan {other}.",
            "west": f"{start} stond westelijker dan {other}.",
            "nextp": f"{start} stond naast {other}."}[kind]


# --- generation helpers -----------------------------------------------------------
def _rooms(rng, n, k):
    """Split the n x n grid into k connected rooms of at least two cells."""
    for _ in range(200):
        cells = [(r, c) for r in range(n) for c in range(n)]
        seeds = rng.sample(cells, k)
        owner = {cell: i for i, cell in enumerate(seeds)}
        sizes = [1] * k
        cap = max(3, round(n * n / k * 1.7))
        while len(owner) < n * n:
            border = []
            for (r, c), i in owner.items():
                if sizes[i] >= cap:
                    continue
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (r + dr, c + dc)
                    if 0 <= nb[0] < n and 0 <= nb[1] < n and nb not in owner:
                        border.append((nb, i))
            if not border:
                break
            # small rooms grow first, so the sizes stay balanced
            low = min(sizes[i] for _, i in border)
            nb, i = rng.choice([b for b in border if sizes[b[1]] <= low + 1])
            owner[nb] = i
            sizes[i] += 1
        if len(owner) == n * n and min(sizes) >= 2:
            return [[owner[(r, c)] for c in range(n)] for r in range(n)]
    raise RuntimeError("no floor plan")


def _label_runs(rooms, taken):
    """For each room the widest free horizontal run in its top-most rows:
    {room: (row, col, length)} - that is where the room's name goes."""
    n = len(rooms)
    best = {}
    for r in range(n):
        c = 0
        while c < n:
            room = rooms[r][c]
            e = c
            while e + 1 < n and rooms[r][e + 1] == room:
                e += 1
            # prefer a start cell without an object, so name and picture do not collide
            length = e - c + 1
            penalty = 1 if (r, c) in taken else 0
            score = (length - penalty, -r)
            if room not in best or score > best[room][0]:
                best[room] = (score, (r, c, length))
            c = e + 1
    return {room: v[1] for room, v in best.items()}


def _pool(puz, sol, thief):
    """Every true statement that may be used as a clue."""
    n, rooms, objects = puz["n"], puz["rooms"], puz["objects"]
    k = len(sol)
    lr, lc = objects[puz["loot"]][:2]
    loot_room = rooms[lr][lc]
    room_of = [rooms[r][c] for r, c in sol]
    out = []
    for p, cell in enumerate(sol):
        cell = tuple(cell)
        if room_of[p] != loot_room:
            out.append(["room", p, room_of[p]])
        for room in sorted({x for row in rooms for x in row}):
            if room != room_of[p] and room != loot_room:
                out.append(["notroom", p, room])
        for j in range(len(objects)):
            if touches(cell, objects[j][:2]):
                if not (p == thief and j == puz["loot"]):
                    out.append(["next", p, j])
            out.append(["see" if sees(objects, cell, j) else "notsee", p, j])
        if cell[0] in (0, n - 1) and cell[1] in (0, n - 1):
            out.append(["corner", p])
        if room_of.count(room_of[p]) == 1 and p != thief:
            out.append(["alone", p])
        for q in range(k):
            if q == p:
                continue
            other = tuple(sol[q])
            if p < q and room_of[p] == room_of[q]:
                out.append(["same", p, q])
            if cell[0] < other[0]:
                out.append(["north", p, q])
            if cell[1] < other[1]:
                out.append(["west", p, q])
            if p < q and touches(cell, other):
                out.append(["nextp", p, q])
    return out


class PlaatsDelict(Game):
    key = "plaatsdelict"
    name = "Plaats delict"
    category = "taal"
    tagline = "Zet de verdachten op de plattegrond en ontmasker de dief."
    rules = [
        "Zet elke verdachte in een leeg vakje. In elke rij en in elke kolom staat precies "
        "één verdachte; op een voorwerp kan niemand staan.",
        "Alle uitspraken kloppen. Naast betekent: de vakjes raken elkaar met een zijde. "
        "Iemand ziet een voorwerp als die in dezelfde rij of kolom staat, zonder ander "
        "voorwerp ertussen. Noord is boven, west is links.",
        "De dief is de enige verdachte in de ruimte van het voorwerp met de ster.",
    ]
    tips = [
        "Begin met de uitspraak die het minste vakjes overlaat en streep meteen die rij "
        "en kolom af voor de anderen.",
        "Wie alleen in een ruimte stond, sluit die hele ruimte uit voor alle anderen.",
    ]
    counts = (9, 8, 8)
    example = False

    # -- generation ---------------------------------------------------------------
    def generate(self, rng, level):
        n, k_rooms, n_plain, max_clues, max_direct = \
            (LEVELS_COMPACT if theme.COMPACT else LEVELS)[level]
        weights = WEIGHTS[level]
        for _ in range(600):
            title, room_defs, plain, loots, people = rng.choice(SCENARIOS)
            rooms = _rooms(rng, n, k_rooms)
            cells = [(r, c) for r in range(n) for c in range(n)]
            loot_key, loot_item = rng.choice(loots)
            keys = [loot_key] + rng.sample(plain, n_plain)
            spots = rng.sample(cells, len(keys))
            objects = [[r, c, key] for (r, c), key in zip(spots, keys)]
            taken = set(spots)
            # every row and column must keep a free cell
            if any(all((r, c) in taken for c in range(n)) for r in range(n)):
                continue
            # a random placement: one suspect per row and column, none on an object
            perm = list(range(n))
            for _try in range(40):
                rng.shuffle(perm)
                sol = [[r, perm[r]] for r in range(n)]
                if all((r, c) not in taken for r, c in sol):
                    break
            else:
                continue
            rng.shuffle(sol)
            # room names: the narrowest rooms get the shortest names
            runs = _label_runs(rooms, taken)
            chosen = rng.sample(room_defs, k_rooms)
            by_width = sorted(range(k_rooms), key=lambda i: (runs[i][2], rng.random()))
            by_len = sorted(chosen, key=lambda rd: len(rd[0]))
            room_names = [None] * k_rooms
            for room, rd in zip(by_width, by_len):
                room_names[room] = list(rd)
            roles = rng.sample(people, n)
            letters = [role.split(" ", 1)[1][0].upper() for role in roles]
            if len(set(letters)) < n:
                continue
            puz = {"level": level, "n": n, "title": title, "rooms": rooms,
                   "room_names": room_names, "objects": objects, "loot": 0,
                   "loot_item": loot_item,
                   "suspects": [[ch, role] for ch, role in zip(letters, roles)],
                   "clues": [], "solution": sol}
            thief = thief_of(puz, sol)
            if thief is None:
                continue
            pool = [cl for cl in _pool(puz, sol, thief) if weights.get(cl[0], 0) > 0]
            if max_direct == 0:
                pool = [cl for cl in pool if cl[0] not in DIRECT]
            # weighted random order; then keep adding a statement that rules out
            # a wrong placement the solver still finds, until only the truth is left
            pool.sort(key=lambda cl: -(rng.random() ** (1.0 / weights[cl[0]])))
            clues = pool[:2]
            target = [list(cell) for cell in sol]
            for _step in range(max_clues + 6):
                wrong = [f for f in solve(puz, clues) if f != target]
                if not wrong:
                    break
                cut = next((cl for cl in pool if cl not in clues
                            and not holds(puz, cl, wrong[0])), None)
                if cut is None:
                    break
                clues.append(cut)
            else:
                continue
            if wrong:
                continue
            # drop what is not needed; level 1 keeps its direct clues, level 3 loses them
            def keep_last(cl):
                direct = cl[0] in DIRECT or cl[0] == "next"
                return (direct if level == 1 else not direct, rng.random())
            for cl in sorted(clues, key=keep_last):
                rest = [x for x in clues if x is not cl]
                if len(solve(puz, rest)) == 1:
                    clues = rest
            if len(clues) > max_clues or len(clues) < 3:
                continue
            if sum(cl[0] in DIRECT for cl in clues) > max_direct:
                continue
            if level > 1 and len({cl[0] for cl in clues}) < 3:
                continue
            rng.shuffle(clues)
            puz["clues"] = clues
            puz["thief"] = thief
            return puz
        raise RuntimeError("could not build a crime scene")

    def verify(self, puz):
        n = puz["n"]
        rooms, objects, sol = puz["rooms"], puz["objects"], puz["solution"]
        k = len(puz["suspects"])
        assert k == n == len(sol) == len(rooms) and all(len(row) == n for row in rooms)
        ids = sorted({x for row in rooms for x in row})
        assert ids == list(range(len(puz["room_names"])))
        for room in ids:                              # every room is one connected area
            cells = {(r, c) for r in range(n) for c in range(n) if rooms[r][c] == room}
            assert len(cells) >= 2
            seen, stack = set(), [next(iter(cells))]
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                stack += [(cur[0] + dr, cur[1] + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                          if (cur[0] + dr, cur[1] + dc) in cells]
            assert seen == cells, "room is not connected"
        taken = {(o[0], o[1]) for o in objects}
        assert len(taken) == len(objects) and all(o[2] in OBJECTS for o in objects)
        assert len({s[0] for s in puz["suspects"]}) == k, "tokens must differ"
        assert sorted(r for r, _ in sol) == list(range(n))
        assert sorted(c for _, c in sol) == list(range(n))
        assert not {tuple(cell) for cell in sol} & taken
        for cl in puz["clues"]:                       # every statement is true
            assert holds(puz, cl, sol), cl
        found = solve(puz, limit=3)
        assert found == [[list(cell) for cell in sol]], "placement must be unique"
        assert thief_of(puz, sol) == puz["thief"] is not None
        lr, lc = objects[puz["loot"]][:2]
        assert not any(cl[0] == "room" and cl[2] == rooms[lr][lc] for cl in puz["clues"])

    def fingerprints(self, puz):
        return [f"plaats:{puz['title']}:{puz['level']}"]

    def instruction(self, puz, part=0):
        return ("Zet elke verdachte op de plattegrond: precies één per rij en per kolom. "
                "Wie stond alleen in de ruimte van de buit?")

    # -- drawing ------------------------------------------------------------------
    @staticmethod
    def _intro(puz):
        obj = OBJECTS[puz["objects"][puz["loot"]][2]][0]
        lr, lc = puz["objects"][puz["loot"]][:2]
        where = puz["room_names"][puz["rooms"][lr][lc]][1]
        return f"Uit {obj} {where} is {puz['loot_item']} gestolen."

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        compact = theme.COMPACT
        n = puz["n"]
        fs = 8.0 if compact else 9.6
        lead = fs * 1.34
        top = y + h
        # scenario
        text(c, x, top - fs - 1, puz["title"], "SansB", fs + 1.5, INK)
        ty = paragraph(c, x, top - fs - 5, w, self._intro(puz), "Sans", fs, leading=lead)
        ty -= 7
        # space needed under the plan
        clue_lines = [wrap(clue_text(puz, cl), "Sans", fs, w - 18) for cl in puz["clues"]]
        clues_h = sum(len(ls) for ls in clue_lines) * lead + 4
        key = ("Naast: de vakjes raken met een zijde. Zien: dezelfde rij of kolom, zonder "
               "voorwerp ertussen. Noord is boven.")
        ks = 7.5 if compact else 8.0
        key_h = len(wrap(key, "Sans", ks, w)) * ks * 1.3 + 4
        answer_h = 26 if compact else 30
        room_for_plan = ty - y - clues_h - key_h - answer_h - 14
        side = min(room_for_plan, w - (100 if compact else 160), n * (48 if compact else 64))
        cell = side / n
        self.last_cell = cell                  # for the layout tests
        gx, gtop = x, ty
        self._plan(c, puz, gx, gtop, cell, solved)
        self._legend(c, puz, gx + side + (10 if compact else 18), gtop,
                     x + w - (gx + side + (10 if compact else 18)), side, fs)
        # statements
        cy = gtop - side - 12
        for i, lines in enumerate(clue_lines):
            circle(c, x + 6, cy - fs * 0.36, 6, stroke=INK, lw=0.9)
            text_mid(c, x + 6, cy - fs * 0.36, i + 1, "SansB", 7.5 if compact else 8, INK)
            for ln in lines:
                text(c, x + 18, cy - fs * 0.72, ln, "Sans", fs, INK)
                cy -= lead
        cy -= 3
        for ln in wrap(key, "Sans", ks, w):
            text(c, x, cy - ks * 0.8, ln, "Sans", ks, GREY)
            cy -= ks * 1.3
        # answer
        ay = y + 4
        text(c, x, ay + 4, "De dief:", "SerifB", 12 if compact else 13.5, INK)
        lx = x + (54 if compact else 62)
        line(c, lx, ay + 2, lx + (150 if compact else 190), ay + 2, 0.9, INK)
        if solved:
            text(c, lx + 6, ay + 5, puz["suspects"][puz["thief"]][1], "Hand",
                 19 if compact else 22, PEN)

    def _plan(self, c, puz, gx, gtop, cell, solved):
        n = puz["n"]
        rooms = puz["rooms"]
        side = n * cell
        # thin cell lines, thick walls between rooms
        for i in range(n + 1):
            for j in range(n):
                # vertical segment at column border i, row j
                wall = i in (0, n) or rooms[j][i - 1] != rooms[j][i]
                line(c, gx + i * cell, gtop - j * cell, gx + i * cell, gtop - (j + 1) * cell,
                     2.6 if wall else 0.5, INK, cap=2)
                wall = i in (0, n) or rooms[i - 1][j] != rooms[i][j]
                line(c, gx + j * cell, gtop - i * cell, gx + (j + 1) * cell, gtop - i * cell,
                     2.6 if wall else 0.5, INK, cap=2)
        taken = {(o[0], o[1]) for o in puz["objects"]}
        base = 7.5 if theme.COMPACT else 8.0
        for room, (r, col, length) in _label_runs(rooms, taken).items():
            label = puz["room_names"][room][0]
            size = fit_size(label, "SansM", length * cell - 6, base, min_size=6.0)
            text(c, gx + col * cell + 3.5, gtop - r * cell - size - 2, label, "SansM", size, GREY)
        for k, (r, col, key) in enumerate(puz["objects"]):
            cx, cy = gx + (col + 0.5) * cell, gtop - (r + 0.5) * cell - cell * 0.07
            draw_object(c, key, cx, cy, cell * 0.5)
            if k == puz["loot"]:
                star(c, gx + (col + 1) * cell - cell * 0.17, gtop - (r + 1) * cell + cell * 0.17,
                     cell * 0.12, fill=RED)
        if solved:
            for (letter, _), (r, col) in zip(puz["suspects"], puz["solution"]):
                text_mid(c, gx + (col + 0.5) * cell, gtop - (r + 0.5) * cell - cell * 0.1,
                         letter, "Hand", cell * 0.58, PEN)

    def _legend(self, c, puz, lx, top, width, side, fs):
        compact = theme.COMPACT
        row = fs * 1.5
        hs = 7.5
        ty = top - hs
        text(c, lx, ty, "VERDACHTEN", "SansB", hs, GREY)
        ty -= row * 0.95
        r = fs * 0.72
        for letter, role in puz["suspects"]:
            circle(c, lx + r, ty + fs * 0.32, r, stroke=INK, lw=1.0)
            text_mid(c, lx + r, ty + fs * 0.32, letter, "SansB", fs * 0.92, INK)
            size = fit_size(role, "Sans", width - 2 * r - 6, fs, min_size=7.0)
            text(c, lx + 2 * r + 5, ty, role, "Sans", size, INK)
            ty -= row
        ty -= 2
        text(c, lx, ty, "VOORWERPEN", "SansB", hs, GREY)
        ty -= row * 0.95
        for k, (_, _, key) in enumerate(puz["objects"]):
            draw_object(c, key, lx + r, ty + fs * 0.32, fs * 1.35)
            name = OBJECTS[key][1]
            text(c, lx + 2 * r + 5, ty, name, "Sans", fs, INK)
            if k == puz["loot"]:
                sx = lx + 2 * r + 5 + c.stringWidth(name, "Sans", fs) + 7
                star(c, sx, ty + fs * 0.34, fs * 0.42, fill=RED)
                if not compact:
                    text(c, sx + 8, ty, "hier lag de buit", "Sans", fs - 1.4, GREY)
            ty -= row
        # compass under the legend: north is up
        ax = lx + r
        ay = min(ty - 4, top - side + 26) - 18
        ay = max(ay, top - side)
        polyline(c, [(ax - 4, ay + 12), (ax, ay + 20), (ax + 4, ay + 12)], 1.3, INK)
        line(c, ax, ay, ax, ay + 19, 1.3, INK)
        text(c, ax + 8, ay + 9, "N", "SansB", fs, INK)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        rrect(c, cx - h, cy - h, s * 0.72, s * 0.72 + s * 0.28, 1.5, stroke=color, lw=1.5)
        line(c, cx - h, cy + s * 0.08, cx - h + s * 0.4, cy + s * 0.08, 1.3, color)
        line(c, cx - h + s * 0.4, cy - h, cx - h + s * 0.4, cy - s * 0.12, 1.3, color)
        circle(c, cx + s * 0.2, cy - s * 0.08, s * 0.2, fill=None, stroke=color, lw=1.7)
        line(c, cx + s * 0.34, cy - s * 0.22, cx + h, cy - h + s * 0.04, 2.2, color)


# --- object pictograms ---------------------------------------------------------------
def draw_object(c, key, cx, cy, s, color=INK):
    """A small pictogram of about s x s points centred on (cx, cy)."""
    h = s / 2
    lw = max(0.9, s * 0.055)

    def ln(x1, y1, x2, y2, width=lw):
        line(c, cx + x1 * s, cy + y1 * s, cx + x2 * s, cy + y2 * s, width, color)

    def poly(pts, close=False, fill=None):
        polyline(c, [(cx + px * s, cy + py * s) for px, py in pts], lw, color,
                 close=close, fill=fill)

    def box(x1, y1, x2, y2, r=0.0, fill=None):
        rrect(c, cx + x1 * s, cy + y1 * s, (x2 - x1) * s, (y2 - y1) * s, r * s,
              fill=fill, stroke=color, lw=lw)

    def ring(px, py, r, fill=None):
        circle(c, cx + px * s, cy + py * s, r * s, fill=fill, stroke=color, lw=lw)

    if key == "trap":
        poly([(-0.5, -0.45), (-0.5, -0.2), (-0.25, -0.2), (-0.25, 0.05), (0.0, 0.05),
              (0.0, 0.3), (0.25, 0.3), (0.25, 0.5), (0.5, 0.5), (0.5, -0.45)], close=True)
    elif key == "piano":
        box(-0.5, -0.3, 0.5, 0.35, 0.04)
        ln(-0.5, 0.0, 0.5, 0.0)
        for k in range(1, 6):
            ln(-0.5 + k / 6, -0.3, -0.5 + k / 6, 0.0)
        for k in (1, 2, 4, 5):
            box(-0.5 + k / 6 - 0.045, -0.12, -0.5 + k / 6 + 0.045, 0.0, 0, fill=color)
    elif key == "klok":
        ring(0, 0, 0.46)
        ln(0, 0, 0, 0.3)
        ln(0, 0, 0.2, -0.1)
        for ax, ay in ((0, 0.4), (0.4, 0), (0, -0.4), (-0.4, 0)):
            ln(ax, ay, ax * 0.85, ay * 0.85)
    elif key == "plant":
        poly([(-0.26, -0.05), (0.26, -0.05), (0.18, -0.5), (-0.18, -0.5)], close=True)
        poly([(0, -0.05), (0, 0.5)])
        poly([(0, 0.1), (-0.32, 0.38), (-0.08, 0.2)])
        poly([(0, 0.2), (0.34, 0.46), (0.1, 0.26)])
        poly([(0, 0.02), (0.3, 0.12)])
    elif key == "vitrine":
        box(-0.42, -0.2, 0.42, 0.5, 0.03)
        ln(-0.32, -0.2, -0.32, -0.5)
        ln(0.32, -0.2, 0.32, -0.5)
        poly([(0, 0.34), (0.18, 0.15), (0, -0.06), (-0.18, 0.15)], close=True)
    elif key == "kluis":
        box(-0.46, -0.46, 0.46, 0.46, 0.08)
        ring(-0.05, 0, 0.2)
        ln(-0.05, 0.2, -0.05, 0.08)
        ln(-0.25, 0, -0.13, 0)
        ln(0.15, 0, 0.03, 0)
        ln(0.3, -0.18, 0.3, 0.18, lw * 1.5)
    elif key == "kist":
        box(-0.48, -0.4, 0.48, 0.05, 0.02)
        poly([(-0.48, 0.05), (-0.4, 0.38), (0.4, 0.38), (0.48, 0.05)])
        box(-0.08, -0.14, 0.08, 0.1, 0.02, fill=color)
    elif key == "beeld":
        box(-0.3, -0.5, 0.3, -0.3, 0.02)
        poly([(-0.26, -0.3), (-0.2, -0.02), (0.2, -0.02), (0.26, -0.3)])
        ring(0, 0.24, 0.2)
    elif key == "vat":
        poly([(-0.3, 0.48), (0.3, 0.48), (0.44, 0.12), (0.44, -0.12), (0.3, -0.48),
              (-0.3, -0.48), (-0.44, -0.12), (-0.44, 0.12)], close=True)
        ln(-0.42, 0.18, 0.42, 0.18)
        ln(-0.42, -0.18, 0.42, -0.18)
    elif key == "anker":
        ring(0, 0.38, 0.1)
        ln(0, 0.28, 0, -0.45)
        ln(-0.22, 0.12, 0.22, 0.12)
        poly([(-0.4, -0.12), (-0.3, -0.36), (0, -0.46), (0.3, -0.36), (0.4, -0.12)])
    elif key == "kast":
        box(-0.4, -0.5, 0.4, 0.5, 0.02)
        ln(-0.4, 0.17, 0.4, 0.17)
        ln(-0.4, -0.17, 0.4, -0.17)
        for px in (-0.25, -0.12, 0.02):
            ln(px, 0.2, px, 0.42)
        for px in (0.05, 0.18, 0.28):
            ln(px, -0.14, px, 0.08)
    elif key == "spiegel":
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        c.ellipse(cx - 0.3 * s, cy - 0.22 * s, cx + 0.3 * s, cy + 0.5 * s, stroke=1, fill=0)
        c.restoreState()
        ln(0, -0.22, 0, -0.42)
        ln(-0.24, -0.46, 0.24, -0.46)
        ln(-0.1, 0.3, 0.08, 0.12)
    elif key == "lamp":
        poly([(-0.36, 0.08), (-0.2, 0.5), (0.2, 0.5), (0.36, 0.08)], close=True)
        ln(0, 0.08, 0, -0.42)
        ln(-0.24, -0.46, 0.24, -0.46)
    elif key == "bank":
        box(-0.5, -0.12, 0.5, 0.04, 0.02)
        box(-0.5, 0.14, 0.5, 0.36, 0.02)
        ln(-0.38, -0.12, -0.38, -0.44)
        ln(0.38, -0.12, 0.38, -0.44)
        ln(-0.44, 0.04, -0.44, 0.14)
        ln(0.44, 0.04, 0.44, 0.14)
    elif key == "kar":
        box(-0.34, -0.12, 0.44, 0.34, 0.02)
        ring(0.05, -0.32, 0.16)
        poly([(-0.34, 0.3), (-0.5, 0.44)])
        ln(-0.34, -0.12, -0.34, -0.44)
    elif key == "put":
        box(-0.34, -0.5, 0.34, -0.08, 0.03)
        ln(-0.28, -0.08, -0.28, 0.26)
        ln(0.28, -0.08, 0.28, 0.26)
        poly([(-0.44, 0.24), (0, 0.5), (0.44, 0.24)], close=True)
        ln(0, 0.24, 0, 0.02)
    else:
        raise AssertionError(key)
    del h


GAME = PlaatsDelict()
