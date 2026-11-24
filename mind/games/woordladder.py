"""Woordladder - change one letter per step; every rung is a Dutch word."""
from collections import deque

from .. import theme
from ..draw import circle, line, text_mid
from ..theme import INK, LIGHT, PEN, WHITE
from ._ladderwoorden import WORDS3, WORDS4
from .base import Game

# Words from the curated list that are left out after all: not ordinary
# standalone Dutch words (title, nationality in lower case, rare forms).
SKIP = {"don", "rus", "nes", "bet", "led", "tja", "vice", "wade"}

# Start and target words are everyday nouns and adjectives. Function words
# and verb forms may appear on the route, but never at either end.
END3 = set("""aap arm bad bak bal bed bel bes bok bol bom bos bot bus dag dak dal dam das eik elf fee gas
gat hak hal ham hek hof hok hut ijs jam jas juf kam kar kas kat kei kin kip koe kok kop kus lab lam lap
les lid lip lot man mat mes mol mop mos nek net oma oog oom oor opa pad pak pan pap pas pen pet pil pit
pop pot pup put rad ram rat rij rit rok rol rug sap sok som tak tas tin tip tol ton top tor uil uur vak
vat vel vis vos wal weg wei wet wol zak zee zin zon zoo zus dik dom dun fel fit gek nat oud ruw wit lui
los vol""".split())
NOT_END4 = set("""alle apen arme bent bied bijt bood boze brak daar deed denk deze dien doch dode doen doet
dook door dure durf eens eist elke enge enig even gaan gaat gauw gave geef geen gele ging gooi haal hang
hare hebt heen heet hele hete heus hier hing hoge hoor houd huil iets jouw kale keek kent kies kijk komt
koos kunt kwam laat lage late leef leek leen lees lege legt leve liep liet ligt luie lukt maak maar meen
meet meld mede mijn mits moet moge naar nare neem neen neer niet niks noch noem ogen onze ooit oren oude
ouwe over pakt past pure raak rare redt reed riep rijd rode ruwe soms stak telt toch toen trad trof trok
uren vaak valt veel vele viel vind voeg voel volg vond voor want ware wars wees weet welk werd wilt wint
wist woon word zakt zegt zich zien ziet zijn zoek zong zulk zult baat boel borg data info item mega mini
plus tips hype mate link scan""".split())
# Pairs that belong together make the nicest ladders; they are preferred
# whenever their distance happens to match the level.
RELATED = [p.split("-") for p in """kat-rat vis-zee kip-vos koe-wei mol-rat vos-uil kop-nek rug-nek lip-kin
jas-pet jas-rok oma-opa dak-hut mes-pan ijs-zon bos-wei oog-oor dag-uur zon-zee bal-pop pen-pak bed-kus
arm-rug kat-pot bus-weg kam-kop tak-bos zak-tas dik-dun nat-zee oud-opa wit-wol sok-jas kip-koe aap-uil
koud-warm hond-wolf boek-film wijn-bier hoed-jurk land-stad dorp-stad goud-geld hand-voet hoog-laag
kaas-melk wind-wolk vuur-rook zout-zoet zuur-zoet boom-blad boom-woud roos-geur berg-rots dood-graf
nood-hulp werk-rust maan-ster week-jaar muis-poes haan-eend wolf-haas soep-saus kerk-dorp park-tuin
trui-jurk oost-west kort-lang ziek-pijn vals-echt slim-knap boos-blij huis-tuin deur-raam mond-neus
tand-tong been-voet hals-keel buik-maag bank-geld boot-zeil zand-zout vlag-land ring-goud bier-glas
lamp-vuur kind-papa neef-zoon rijk-arts haas-hond wijn-glas brug-weer koel-warm rood-geel""".split()]

# level -> (letters, changes, ladders on a page)
LEVELS = {1: (3, (3,), 4), 2: (4, (4,), 3), 3: (4, (5, 6), 3)}
# The 7.3" Paper Pro Move: one long ladder less, so the boxes stay writable.
LEVELS_COMPACT = {1: (3, (3,), 4), 2: (4, (4,), 3), 3: (4, (5, 6), 2)}

_cache = {}


def words(n):
    return [w for w in (WORDS3 if n == 3 else WORDS4) if w not in SKIP]


def graph(n):
    """Word graph for n-letter words: {word: [neighbours]}, built once."""
    if n not in _cache:
        ws = words(n)
        buckets = {}
        for w in ws:
            for i in range(n):
                buckets.setdefault(w[:i] + "_" + w[i + 1:], []).append(w)
        g = {w: [] for w in ws}
        for group in buckets.values():
            for a in group:
                for b in group:
                    if a != b:
                        g[a].append(b)
        ends = (END3 if n == 3 else set(ws) - NOT_END4) & {w for w in ws if g[w]}
        _cache[n] = (g, sorted(ends))
    return _cache[n]


def distances(g, start):
    dist = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in g[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def _route(rng, g, dist, ends, target):
    """A random shortest route to target (dist measured from the start),
    preferring everyday nouns and adjectives on the way."""
    best = None
    for _ in range(6):
        path = [target]
        while dist[path[-1]]:
            prev = [v for v in g[path[-1]] if dist.get(v) == dist[path[-1]] - 1]
            path.append(rng.choice(prev))
        path.reverse()
        score = sum(w in ends for w in path[1:-1])
        if best is None or score > best[0]:
            best = (score, path)
    return best[1]


class Woordladder(Game):
    key = "woordladder"
    name = "Woordladder"
    category = "taal"
    tagline = "Van woord naar woord, één letter per sport."
    rules = [
        "Klim van het bovenste woord naar het onderste. Op elke sport verander je precies "
        "één letter, en elke sport is een bestaand Nederlands woord.",
        "De letters blijven op hun plaats: KAT wordt LAT, LAT wordt LOT, LOT wordt POT.",
        "Er zijn precies genoeg sporten voor de kortste weg. Staat er al een woord op een "
        "sport, dan moet je route daarlangs.",
        "Vaak kan het op meer manieren: elke route met echte woorden telt.",
    ]
    tips = [
        "Kijk welke letters verschillen en werk van boven én van onder naar het midden.",
        "Loopt het vast? Probeer eerst een klinker te wisselen.",
    ]
    counts = (9, 8, 8)
    example = False

    # -- generation ---------------------------------------------------------------
    def _ladder(self, rng, n, changes, obligatory, used):
        g, ends = graph(n)
        ends_set = set(ends)
        related = [p for p in RELATED if len(p[0]) == n and p[0] in g and p[1] in g]
        for attempt in range(400):
            if attempt < 12 and related and rng.random() < 0.6:
                start, target = rng.sample(rng.choice(related), 2)
                dist = distances(g, start)
                if dist.get(target) not in changes:
                    continue
            else:
                start = rng.choice(ends)
                dist = distances(g, start)
                goals = [w for w in ends if dist.get(w) in changes]
                if not goals:
                    continue
                target = rng.choice(goals)
            if start in used or target in used:
                continue
            # no trivial ladders: at least two letters differ between the ends
            if sum(a != b for a, b in zip(start, target)) < 2:
                continue
            route = _route(rng, g, dist, ends_set, target)
            if set(route[1:-1]) & used:
                continue
            fixed = [0, len(route) - 1]
            if obligatory:
                mid = [i for i in range(2, len(route) - 2)] or [len(route) // 2]
                nice = [i for i in mid if route[i] in ends_set] or mid
                fixed.insert(1, rng.choice(nice))
            return {"route": route, "fixed": fixed}
        raise RuntimeError("no word ladder found")

    def generate(self, rng, level):
        n, changes, count = (LEVELS_COMPACT if theme.COMPACT else LEVELS)[level]
        used, ladders = set(), []
        for _ in range(count):
            ladder = self._ladder(rng, n, changes, level == 3, used)
            used.update(ladder["route"])
            ladders.append(ladder)
        return {"level": level, "letters": n, "ladders": ladders}

    def verify(self, puz):
        n = puz["letters"]
        assert n in (3, 4) and 2 <= len(puz["ladders"]) <= 4
        ws = set(words(n))
        g, _ = graph(n)
        ends = set()
        for ladder in puz["ladders"]:
            route, fixed = ladder["route"], ladder["fixed"]
            start, target = route[0], route[-1]
            assert start != target and len(set(route)) == len(route)
            assert all(len(w) == n and w in ws for w in route), "unknown word"
            for a, b in zip(route, route[1:]):
                assert sum(x != y for x, y in zip(a, b)) == 1, "one letter per step"
            assert fixed[0] == 0 and fixed[-1] == len(route) - 1
            assert fixed == sorted(set(fixed)) and len(fixed) in (2, 3)
            dist = distances(g, start)
            if len(fixed) == 3:                 # shortest route through the given word
                mid = route[fixed[1]]
                assert dist[mid] == fixed[1], "obligatory word is on its row"
                assert distances(g, mid)[target] == len(route) - 1 - fixed[1]
            assert dist[target] == len(route) - 1, "as many rungs as the shortest route"
            assert not {start, target} & ends, "a word is used at two ladder ends"
            ends |= {start, target}

    def fingerprints(self, puz):
        return ["ladder:" + "-".join(sorted((ld["route"][0], ld["route"][-1])))
                for ld in puz["ladders"]]

    def instruction(self, puz, part=0):
        extra = " Het grijze woord onderweg is verplicht." if puz["level"] == 3 else ""
        return ("Verander op elke sport één letter, zodat er telkens een bestaand woord "
                "staat." + extra)

    # -- drawing ------------------------------------------------------------------
    @staticmethod
    def _layout(box, count, n, rows):
        """Arrange the ladders in a grid; returns (cols, box size, slot w, slot h)."""
        x, y, w, h = box
        cap = 34.0 if theme.COMPACT else 42.0
        best = None
        for cols in range(1, count + 1):
            lines = -(-count // cols)
            slot_w, slot_h = w / cols, h / lines
            b = min(cap, (slot_w - 22) / n, (slot_h - 30) / (rows * 1.16))
            if best is None or b > best[1] + 0.5:
                best = (cols, b, slot_w, slot_h)
        return best

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        ladders = puz["ladders"]
        n = puz["letters"]
        rows = max(len(ld["route"]) for ld in ladders)
        cols, b, slot_w, slot_h = self._layout(box, len(ladders), n, rows)
        gap = b * 0.16
        lines = -(-len(ladders) // cols)
        for k, ld in enumerate(ladders):
            line_no, col = divmod(k, cols)
            in_line = min(cols, len(ladders) - line_no * cols)
            # centre a shorter last line
            sx = x + (w - in_line * slot_w) / 2 + col * slot_w
            top = y + h - line_no * slot_h
            route, fixed = ld["route"], ld["fixed"]
            height = len(route) * b + (len(route) - 1) * gap
            lx = sx + (slot_w - n * b) / 2
            ly = top - 22 - (slot_h - 30 - height) / 2      # top edge of the first row
            circle(c, sx + slot_w / 2, ly + 11, 7.5, fill=INK, stroke=None)
            text_mid(c, sx + slot_w / 2, ly + 11, k + 1, "SansB", 8.5, WHITE)
            # the ladder's rails
            for rx in (lx - 5, lx + n * b + 5):
                line(c, rx, ly + 2, rx, ly - height - 2, 1.6, INK)
            for i, word in enumerate(route):
                ry = ly - i * (b + gap) - b            # bottom of this row
                given = i in fixed
                changed = None
                if i:
                    changed = [j for j in range(n) if word[j] != route[i - 1][j]][0]
                for j in range(n):
                    c.saveState()
                    c.setStrokeColor(INK)
                    c.setLineWidth(1.0)
                    if given:
                        c.setFillColor(LIGHT)
                    c.rect(lx + j * b, ry, b, b, stroke=1, fill=1 if given else 0)
                    c.restoreState()
                    if given:
                        text_mid(c, lx + (j + 0.5) * b, ry + b / 2, word[j].upper(),
                                 "SansB", b * 0.56, INK)
                    elif solved:
                        text_mid(c, lx + (j + 0.5) * b, ry + b / 2, word[j].upper(),
                                 "Hand", b * 0.8, PEN)
                if solved and changed is not None:     # the letter that changed
                    c.saveState()
                    c.setStrokeColor(PEN)
                    c.setLineWidth(2.4)
                    c.rect(lx + changed * b + 1.6, ry + 1.6, b - 3.2, b - 3.2, stroke=1, fill=0)
                    c.restoreState()
        del lines

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        for dx in (-0.3, 0.3):
            line(c, cx + dx * s, cy - h, cx + dx * s, cy + h, 1.8, color)
        for k in (-0.3, 0.0, 0.3):
            line(c, cx - 0.3 * s, cy + k * s, cx + 0.3 * s, cy + k * s, 1.5, color)
        text_mid(c, cx, cy + 0.15 * s, "A", "SansB", s * 0.24, color)
        text_mid(c, cx, cy - 0.15 * s, "B", "SansB", s * 0.24, color)


GAME = Woordladder()
