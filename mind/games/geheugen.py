"""Geheugentraining - study a page, turn it, answer from memory.

Part 0 is the study page, part 1 the question page. Three variants:
coloured shapes in a grid, a list (shopping, to-do, packing) and a short
scene full of names, times and numbers.
"""
from ..draw import Grid, circle, line, rrect, star, text, text_mid, wrap
from ..theme import GREEN, INK, MUSTARD, PEN, PURPLE, RED, WHITE
from ._woorden import DAGEN, LIJSTEN, NAMEN, STEDEN, STRATEN
from .base import Game

# name -> (with article, plural)
SHAPES = {
    "cirkel": ("de cirkel", "cirkels"),
    "vierkant": ("het vierkant", "vierkanten"),
    "driehoek": ("de driehoek", "driehoeken"),
    "ster": ("de ster", "sterren"),
    "hart": ("het hart", "harten"),
    "ruit": ("de ruit", "ruiten"),
    "kruis": ("het kruis", "kruisen"),
    "maan": ("de maan", "manen"),
}
# name -> (colour, inflected adjective)
COLORS = {
    "rood": (RED, "rode"),
    "geel": (MUSTARD, "gele"),
    "blauw": (PEN, "blauwe"),
    "groen": (GREEN, "groene"),
    "zwart": (INK, "zwarte"),
    "paars": (PURPLE, "paarse"),
}
SIZES = {1: (3, 4, 5, 5), 2: (4, 4, 6, 5), 3: (5, 4, 7, 6)}  # rows, cols, kinds, colours
LIST_LEN = {1: 8, 2: 10, 3: 12}
FACTS = {1: 4, 2: 5, 3: 6}
N_QUESTIONS = {1: 5, 2: 5, 3: 6}
DIRS = {"rechts van": (0, 1), "links van": (0, -1), "onder": (1, 0), "boven": (-1, 0)}
BASISKLEUREN = ["rood", "blauw", "groen", "geel", "zwart", "wit", "oranje"]


# --- question logic: text and answer are always derived from the study data ----
def ask_vormen(study, spec):
    R, C, cells = study["rows"], study["cols"], study["cells"]
    kind = spec[0]
    count_shape = lambda s: sum(1 for cell in cells if cell[0] == s)
    if kind == "hoek":
        pos = {"linksboven": 0, "rechtsboven": C - 1, "linksonder": (R - 1) * C,
               "rechtsonder": R * C - 1}[spec[1]]
        return (f"Welke vorm stond er {spec[1]}, en in welke kleur?",
                f"{cells[pos][0]}, {cells[pos][1]}")
    if kind == "telkleur":
        n = sum(1 for cell in cells if cell[1] == spec[1])
        return f"Hoeveel {COLORS[spec[1]][1]} vormen waren er?", str(n)
    if kind == "telvorm":
        return f"Hoeveel {SHAPES[spec[1]][1]} waren er?", str(count_shape(spec[1]))
    if kind == "kleurvan":
        assert count_shape(spec[1]) == 1
        colour = [cell[1] for cell in cells if cell[0] == spec[1]][0]
        return f"Welke kleur had {SHAPES[spec[1]][0]}?", colour
    if kind == "ontbreekt":
        a, b, d = spec[1]
        missing = [s for s in spec[1] if count_shape(s) == 0]
        assert len(missing) == 1
        return (f"Welke van deze vormen kwam niet voor: {a}, {b} of {d}?",
                missing[0])
    if kind == "naast":
        assert count_shape(spec[1]) == 1
        i = [k for k, cell in enumerate(cells) if cell[0] == spec[1]][0]
        dr, dc = DIRS[spec[2]]
        r, col = i // C + dr, i % C + dc
        assert 0 <= r < R and 0 <= col < C
        nb = cells[r * C + col]
        return (f"Welke vorm stond er {spec[2]} {SHAPES[spec[1]][0]}, en in welke kleur?",
                f"{nb[0]}, {nb[1]}")
    raise AssertionError(kind)


def ask_lijst(study, spec):
    items = study["items"]
    kind = spec[0]
    if kind == "plaats":
        return f"Wat stond er op plaats {spec[1]}?", items[spec[1] - 1]
    if kind == "niet":
        missing = [o for o in spec[1] if o not in items]
        assert len(missing) == 2 and len(spec[1]) == 6
        return ("Welke twee van deze zes stonden NIET op de lijst: "
                + ", ".join(spec[1][:5]) + " of " + spec[1][5] + "?",
                " en ".join(missing))
    if kind == "aantal":
        return "Hoeveel dingen stonden er op de lijst?", str(len(items))
    if kind == "onderaan":
        return "Wat stond er helemaal onderaan de lijst?", items[-1]
    if kind == "bovenaan":
        return "Wat stond er helemaal bovenaan de lijst?", items[0]
    if kind == "onder":
        return f"Wat stond er net onder “{spec[1]}”?", items[items.index(spec[1]) + 1]
    if kind == "boven":
        return f"Wat stond er net boven “{spec[1]}”?", items[items.index(spec[1]) - 1]
    raise AssertionError(kind)


def ask_verhaal(study, spec):
    _, key, question = spec
    value = study["data"][key]
    assert value in " ".join(study["facts"])
    return question, value


ASK = {"vormen": ask_vormen, "lijst": ask_lijst, "verhaal": ask_verhaal}


# --- scenes ------------------------------------------------------------------
def _tijd(rng, lo=7, hi=20):
    return f"{rng.randint(lo, hi):02d}:{rng.randrange(60):02d}"


def _trein(rng):
    naam, stad = rng.choice(NAMEN), rng.choice(STEDEN)
    nr, tijd, spoor = rng.randint(1200, 9800), _tijd(rng, 6, 21), rng.randint(1, 14)
    rij, plaats = rng.randint(1, 8), rng.randint(21, 98)
    mins, prijs = rng.randint(18, 95), rng.randint(6, 28)
    boek = rng.choice(["vulkanen", "bijen", "sterren", "schaken", "zeilen",
                       "Noorwegen", "fotografie", "bruggen"])
    kleur, v = rng.choice(BASISKLEUREN), rng.randint(4, 25)
    reden = rng.choice(["mist", "een defect sein", "werken aan het spoor",
                        "een storing aan een overweg"])
    return "Onderweg met de trein", [
        (f"Trein {nr} naar {stad} vertrekt om {tijd} van spoor {spoor}.",
         [("nr", "Welk nummer had de trein?", str(nr)),
          ("stad", "Naar welke stad reed de trein?", stad),
          ("tijd", "Hoe laat vertrok de trein?", tijd),
          ("spoor", "Van welk spoor vertrok de trein?", str(spoor))]),
        (f"{naam} zit in rijtuig {rij}, op plaats {plaats}.",
         [("naam", "Hoe heette de reiziger?", naam),
          ("rij", "In welk rijtuig zat de reiziger?", str(rij)),
          ("plaats", "Op welke plaats zat de reiziger?", str(plaats))]),
        (f"De rit duurt {mins} minuten en kost {prijs} euro.",
         [("mins", "Hoeveel minuten duurde de rit?", str(mins)),
          ("prijs", "Hoeveel euro kostte de rit?", str(prijs))]),
        (f"Onderweg leest {naam} een boek over {boek}.",
         [("boek", "Waarover ging het boek?", boek)]),
        (f"De vouwfiets naast de deur is {kleur}.",
         [("kleur", "Welke kleur had de vouwfiets?", kleur)]),
        (f"Door {reden} heeft de trein {v} minuten vertraging.",
         [("reden", "Wat was de oorzaak van de vertraging?", reden),
          ("vertraging", "Hoeveel minuten vertraging had de trein?", str(v))]),
    ]


def _afspraak(rng):
    naam, dag, tijd = rng.choice(NAMEN), rng.choice(DAGEN), _tijd(rng, 8, 18)
    wie = rng.choice(["tandarts", "kapper", "oogarts", "kinesist", "notaris",
                      "dierenarts"])
    straat, nr, stad = rng.choice(STRATEN), rng.randint(3, 148), rng.choice(STEDEN)
    mins, prijs = rng.randrange(15, 65, 5), rng.randint(24, 95)
    mee = rng.choice(["een pasfoto", "de verzekeringspapieren", "het vorige verslag",
                      "een handdoek", "de identiteitskaart"])
    verdieping, deur = rng.randint(1, 6), rng.choice("ABCDEF")
    dossier = rng.randint(1000, 9999)
    return "Een afspraak", [
        (f"{naam} heeft op {dag} om {tijd} een afspraak bij de {wie}.",
         [("naam", "Wie had de afspraak?", naam),
          ("dag", "Op welke dag was de afspraak?", dag),
          ("tijd", "Hoe laat was de afspraak?", tijd),
          ("wie", "Bij wie was de afspraak?", wie)]),
        (f"Het adres is {straat} {nr} in {stad}.",
         [("straat", "In welke straat was de afspraak?", straat),
          ("nr", "Wat was het huisnummer?", str(nr)),
          ("stad", "In welke stad was de afspraak?", stad)]),
        (f"De afspraak duurt {mins} minuten en kost {prijs} euro.",
         [("mins", "Hoeveel minuten duurde de afspraak?", str(mins)),
          ("prijs", "Hoeveel euro kostte de afspraak?", str(prijs))]),
        (f"{naam} moet {mee} meebrengen.",
         [("mee", "Wat moest er meegebracht worden?", mee)]),
        (f"De wachtzaal is op verdieping {verdieping}, achter deur {deur}.",
         [("verdieping", "Op welke verdieping was de wachtzaal?", str(verdieping)),
          ("deur", "Welke letter stond er op de deur van de wachtzaal?", deur)]),
        (f"Het dossiernummer is {dossier}.",
         [("dossier", "Wat was het dossiernummer?", str(dossier))]),
    ]


def _pakje(rng):
    code = f"{rng.choice('BKLMRT')}{rng.randint(100, 999)}"
    kg, stad, naam = rng.randint(2, 18), rng.choice(STEDEN), rng.choice(NAMEN)
    kleur, dag = rng.choice(BASISKLEUREN), rng.choice(DAGEN)
    u1 = rng.randint(8, 17)
    buren, aantal = rng.randint(2, 96), rng.randint(2, 9)
    dingen = rng.choice(["boeken", "puzzels", "fietslampen", "koffiekopjes",
                         "fotokaders", "volleyballen", "notitieboekjes"])
    kosten = rng.randint(4, 19)
    return "Een pakje onderweg", [
        (f"Pakje {code} weegt {kg} kilogram en moet naar {stad}.",
         [("code", "Wat was de code van het pakje?", code),
          ("kg", "Hoeveel kilogram woog het pakje?", str(kg)),
          ("stad", "Naar welke stad moest het pakje?", stad)]),
        (f"De koerier heet {naam}; de bestelwagen is {kleur}.",
         [("naam", "Hoe heette de koerier?", naam),
          ("kleur", "Welke kleur had de bestelwagen?", kleur)]),
        (f"De levering is op {dag}, tussen {u1} en {u1 + 2} uur.",
         [("dag", "Op welke dag werd het pakje geleverd?", dag),
          ("uren", "Tussen welke uren werd het pakje geleverd?", f"{u1} en {u1 + 2}")]),
        (f"Is er niemand thuis, dan gaat het pakje naar de buren op nummer {buren}.",
         [("buren", "Op welk huisnummer wonen de buren?", str(buren))]),
        (f"In het pakje zitten {aantal} {dingen}.",
         [("inhoud", "Wat zat er in het pakje, en hoeveel?", f"{aantal} {dingen}")]),
        (f"De verzendkosten bedragen {kosten} euro.",
         [("kosten", "Hoeveel euro bedroegen de verzendkosten?", str(kosten))]),
    ]


def _restaurant(rng):
    tafel, tijd, k = rng.randint(2, 24), _tijd(rng, 17, 21), rng.randint(2, 8)
    naam = rng.choice(NAMEN)
    voor = rng.choice(["tomatensoep", "garnaalkroketten", "kaaskroketten",
                       "carpaccio", "witloofsalade"])
    hoofd = rng.choice(["stoofvlees", "zalm", "mosselen", "steak", "kip"])
    bij = rng.choice(["frieten", "puree", "kroketten", "rijst", "salade"])
    dessert = rng.choice(["chocolademousse", "rijstpap", "appeltaart",
                          "tiramisu", "vanille-ijs"])
    bedrag = rng.randint(48, 320)
    plek = rng.choice(["bij het raam", "op het terras", "naast de open haard",
                       "in de serre", "vlak bij de keuken"])
    return "Uit eten", [
        (f"Tafel {tafel} is om {tijd} gereserveerd voor {k} personen, op naam van {naam}.",
         [("tafel", "Welk nummer had de tafel?", str(tafel)),
          ("tijd", "Hoe laat was de tafel gereserveerd?", tijd),
          ("personen", "Voor hoeveel personen was er gereserveerd?", str(k)),
          ("naam", "Op welke naam stond de reservatie?", naam)]),
        (f"Het gezelschap zit {plek}.",
         [("plek", "Waar zat het gezelschap?", plek)]),
        (f"Als voorgerecht kiezen ze {voor}.",
         [("voor", "Wat was het voorgerecht?", voor)]),
        (f"Het hoofdgerecht is {hoofd} met {bij}.",
         [("hoofd", "Wat was het hoofdgerecht?", hoofd),
          ("bij", "Wat werd er bij het hoofdgerecht geserveerd?", bij)]),
        (f"Als dessert volgt er {dessert}.",
         [("dessert", "Wat was het dessert?", dessert)]),
        (f"De rekening bedraagt {bedrag} euro.",
         [("bedrag", "Hoeveel euro bedroeg de rekening?", str(bedrag))]),
    ]


SCENES = [_trein, _afspraak, _pakje, _restaurant]


# --- shape drawing -------------------------------------------------------------
def draw_shape(c, name, cx, cy, r, color):
    c.saveState()
    c.setFillColor(color)
    if name == "cirkel":
        c.circle(cx, cy, r, stroke=0, fill=1)
    elif name == "vierkant":
        s = r * 1.7
        c.rect(cx - s / 2, cy - s / 2, s, s, stroke=0, fill=1)
    elif name == "driehoek":
        p = c.beginPath()
        p.moveTo(cx, cy + r)
        p.lineTo(cx + r * 1.05, cy - r * 0.8)
        p.lineTo(cx - r * 1.05, cy - r * 0.8)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    elif name == "ster":
        star(c, cx, cy - r * 0.05, r * 1.12, fill=color)
    elif name == "hart":
        p = c.beginPath()
        p.moveTo(cx, cy - r * 0.9)
        p.curveTo(cx - r * 1.7, cy + r * 0.1, cx - r * 0.95, cy + r * 1.3, cx, cy + r * 0.45)
        p.curveTo(cx + r * 0.95, cy + r * 1.3, cx + r * 1.7, cy + r * 0.1, cx, cy - r * 0.9)
        c.drawPath(p, stroke=0, fill=1)
    elif name == "ruit":
        p = c.beginPath()
        p.moveTo(cx, cy + r * 1.1)
        p.lineTo(cx + r * 0.78, cy)
        p.lineTo(cx, cy - r * 1.1)
        p.lineTo(cx - r * 0.78, cy)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    elif name == "kruis":
        a = r * 0.36
        c.rect(cx - a, cy - r, 2 * a, 2 * r, stroke=0, fill=1)
        c.rect(cx - r, cy - a, 2 * r, 2 * a, stroke=0, fill=1)
    elif name == "maan":
        c.circle(cx - r * 0.1, cy, r, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.circle(cx + r * 0.38, cy + r * 0.12, r * 0.84, stroke=0, fill=1)
    c.restoreState()


class Geheugen(Game):
    key = "geheugen"
    name = "Geheugentraining"
    category = "taal"
    tagline = "Kijk, onthoud, blader om en test wat je nog weet."
    rules = [
        "Bekijk de eerste pagina een minuut lang heel aandachtig.",
        "Tik op Verder en beantwoord de vragen uit je hoofd, zonder terug te bladeren.",
        "Controleer daarna je antwoorden op de oplossingspagina.",
    ]
    tips = [
        "Maak er een verhaaltje of een beeld van: dat onthoudt beter dan losse feiten.",
        "Benoem wat je ziet: wie het verwoordt, onthoudt het beter.",
    ]
    counts = (9, 8, 8)
    parts = 2
    example = False

    # -- generation -------------------------------------------------------------
    def _vormen(self, rng, level):
        R, C, kinds, ncol = SIZES[level]
        n = R * C
        names = rng.sample(sorted(SHAPES), kinds)
        colours = rng.sample(sorted(COLORS), ncol)
        uniq, rest = names[:2], names[2:]
        while True:
            fill = [rng.choice(rest) for _ in range(n - 2)]
            if all(fill.count(s) >= 2 for s in rest):
                break
        shapes = uniq + fill
        rng.shuffle(shapes)
        palette = [colours[i % ncol] for i in range(n)]     # evenly spread
        rng.shuffle(palette)
        cells = [[s, k] for s, k in zip(shapes, palette)]
        study = {"rows": R, "cols": C, "cells": cells}
        absent = [s for s in sorted(SHAPES) if s not in names]
        options = rng.sample(rest, 2) + [rng.choice(absent)]
        rng.shuffle(options)
        i = shapes.index(uniq[1])
        dirs = [d for d, (dr, dc) in DIRS.items()
                if 0 <= i // C + dr < R and 0 <= i % C + dc < C]
        specs = [
            ["hoek", rng.choice(["linksboven", "rechtsboven", "linksonder", "rechtsonder"])],
            ["telkleur", rng.choice(sorted({cell[1] for cell in cells}))],
            ["telvorm", rng.choice(rest)],
            ["kleurvan", uniq[0]],
            ["ontbreekt", options],
            ["naast", uniq[1], rng.choice(dirs)],
        ]
        return study, specs

    def _lijst(self, rng, level):
        title, pool = rng.choice(LIJSTEN)
        items = rng.sample(pool, LIST_LEN[level])
        study = {"title": title, "items": items}
        others = [p for p in pool if p not in items]
        options = rng.sample(items, 4) + rng.sample(others, 2)
        rng.shuffle(options)
        k = rng.randint(2, len(items) - 1)
        mid = rng.sample(items[1:-1], 2)
        specs = [
            ["niet", options],
            ["plaats", k],
            ["onder", mid[0]],
            ["boven", mid[1]],
            rng.choice([["onderaan"], ["bovenaan"]]),
            ["aantal"],
        ]
        return study, specs

    def _verhaal(self, rng, level):
        title, facts = rng.choice(SCENES)(rng)
        keep = [0] + sorted(rng.sample(range(1, len(facts)), FACTS[level] - 1))
        facts = [facts[i] for i in keep]
        data, specs, spare = {}, [], []
        for sentence, slots in facts:
            slots = list(slots)
            rng.shuffle(slots)
            for j, (key, question, value) in enumerate(slots):
                data[key] = value
                (specs if j == 0 else spare).append(["slot", key, question])
        rng.shuffle(spare)
        specs += spare
        study = {"title": title, "facts": [f[0] for f in facts], "data": data}
        return study, specs

    def generate(self, rng, level):
        variant = rng.choice(["vormen", "lijst", "verhaal"])
        study, specs = getattr(self, "_" + variant)(rng, level)
        nq = N_QUESTIONS[level]
        if variant != "verhaal":
            first, rest = specs[:1], specs[1:]
            rng.shuffle(rest)
            specs = first + rest
        specs = specs[:nq]
        rng.shuffle(specs)
        questions = [list(ASK[variant](study, s)) for s in specs]
        return {"variant": variant, "study": study, "specs": specs,
                "questions": questions}

    def verify(self, puz):
        variant, study = puz["variant"], puz["study"]
        assert variant in ASK
        assert 5 <= len(puz["questions"]) == len(puz["specs"]) <= 6
        for spec, (question, answer) in zip(puz["specs"], puz["questions"]):
            q, a = ASK[variant](study, spec)       # recomputed from the study data
            assert (q, a) == (question, answer), (q, a, question, answer)
            assert answer != ""
        assert len({q for q, _ in puz["questions"]}) == len(puz["questions"])
        if variant == "vormen":
            assert len(study["cells"]) == study["rows"] * study["cols"]
            assert all(s in SHAPES and k in COLORS for s, k in study["cells"])
        elif variant == "lijst":
            assert len(set(study["items"])) == len(study["items"]) >= 8
        else:
            text_ = " ".join(study["facts"])
            for key, value in study["data"].items():
                assert text_.count(value) >= 1

    def fingerprints(self, puz):
        """Keys that should not repeat within one book (builder may re-roll)."""
        study = puz["study"]
        if puz["variant"] == "verhaal":
            return [f"verhaal:{study['title']}:{len(study['facts'])}"]
        return []

    def instruction(self, puz, part=0):
        if part == 0:
            return "Bekijk dit 60 seconden aandachtig en tik dan op Verder."
        return "Beantwoord de vragen uit je hoofd. Niet terugbladeren!"

    # -- drawing ----------------------------------------------------------------
    def _draw_study(self, c, box, puz):
        x, y, w, h = box
        study, variant = puz["study"], puz["variant"]
        if variant == "vormen":
            R, C = study["rows"], study["cols"]
            g = Grid((x, y + 6, w, h - 12), C, R, max_cell=108)
            for i, (shape, colour) in enumerate(study["cells"]):
                r, col = divmod(i, C)
                rx, ry, s, _ = g.rect(r, col)
                rrect(c, rx + 4, ry + 4, s - 8, s - 8, 10, stroke=INK, lw=1.1)
                draw_shape(c, shape, g.cx(col), g.cy(r), s * 0.27, COLORS[colour][0])
            return
        pad = 22
        rrect(c, x + 8, y + 8, w - 16, h - 16, 14, stroke=INK, lw=1.6)
        top = y + h - 8 - pad
        text(c, x + 8 + pad, top - 20, study["title"], "SerifB", 22, INK)
        line(c, x + 8 + pad, top - 32, x + w - 8 - pad, top - 32, 1.2, INK)
        inner_w = w - 16 - 2 * pad
        if variant == "lijst":
            items = study["items"]
            lead = min(31.0, (h - 16 - 2 * pad - 50) / len(items))
            yy = top - 50 - lead * 0.5
            for i, item in enumerate(items):
                circle(c, x + 8 + pad + 10, yy + 5, 10, stroke=INK, lw=1.0)
                text_mid(c, x + 8 + pad + 10, yy + 5, i + 1, "SansS", 10, INK)
                text(c, x + 8 + pad + 32, yy, item, "SansM", 15.5, INK)
                yy -= lead
        else:
            facts = study["facts"]
            size = 17.5 if len(facts) <= 4 else 15.5
            lead = size * 1.5
            blocks = [wrap(f, "Serif", size, inner_w - 28) for f in facts]
            total = sum(len(b) * lead for b in blocks)
            gap = min(34.0, (h - 16 - 2 * pad - 50 - total) / max(1, len(facts)))
            yy = top - 50
            for i, lines_ in enumerate(blocks):
                circle(c, x + 8 + pad + 8, yy - size * 0.65 + 6, 4, fill=RED, stroke=None)
                for ln in lines_:
                    yy -= lead
                    text(c, x + 8 + pad + 28, yy + lead - size, ln, "Serif", size, INK)
                yy -= gap

    def _draw_questions(self, c, box, puz, solved):
        x, y, w, h = box
        qs = puz["questions"]
        size, lead = 12.0, 16.0
        tw = w - 34
        blocks = [wrap(q, "SansM", size, tw) for q, _ in qs]
        fixed = sum(len(b) * lead for b in blocks)
        answer_h = min(46.0, (h - fixed) / len(qs) - 8)
        gap = (h - fixed - answer_h * len(qs)) / len(qs)
        gap = min(gap, 26.0)
        yy = y + h
        for i, lines_ in enumerate(blocks):
            circle(c, x + 10, yy - 7.5, 10, fill=INK, stroke=None)
            text_mid(c, x + 10, yy - 7.5, i + 1, "SansB", 10, WHITE)
            for ln in lines_:
                text(c, x + 34, yy - size, ln, "SansM", size, INK)
                yy -= lead
            base = yy - answer_h + 10
            line(c, x + 34, base, x + w, base, 0.9, INK)
            if solved:
                text(c, x + 40, base + 5, qs[i][1], "Hand", 23, PEN)
            yy -= answer_h + gap

    def draw(self, c, box, puz, solved=False, part=0):
        if part == 0:
            self._draw_study(c, box, puz)
        else:
            self._draw_questions(c, box, puz, solved)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        g = s * 0.1
        q = (s - g) / 2
        rrect(c, cx - h, cy + g / 2, q, q, 2.5, stroke=color, lw=1.5)
        rrect(c, cx + g / 2, cy + g / 2, q, q, 2.5, fill=color, stroke=color, lw=1.5)
        rrect(c, cx - h, cy - h, q, q, 2.5, fill=color, stroke=color, lw=1.5)
        rrect(c, cx + g / 2, cy - h, q, q, 2.5, stroke=color, lw=1.5)
        star(c, cx - h + q / 2, cy + g / 2 + q / 2, q * 0.3, fill=color)
        text_mid(c, cx + g / 2 + q / 2, cy - h + q / 2, "?", "SansB", q * 0.62, color)


GAME = Geheugen()
