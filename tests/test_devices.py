"""Device profiles: Paper Pro (colour) and reMarkable 2 (greyscale)."""
import json
import random

import pymupdf
import pytest

from mind import book, games, theme
from mind.games import geheugen


@pytest.fixture(autouse=True)
def back_to_colour():
    yield
    theme.set_device("paperpro")


def is_grey(colour):
    r, g, b = colour.rgb()
    return abs(r - g) < 1e-6 and abs(g - b) < 1e-6


def test_both_screens_are_three_by_four():
    for dev in theme.DEVICES.values():
        w, h = dev["px"]
        assert w / h == pytest.approx(theme.W / theme.H)


def test_rm2_turns_every_spot_colour_grey_and_back():
    spots = [theme.RED, theme.TEAL, theme.MUSTARD, theme.PEN, *theme.PALETTE]
    before = [c.rgb() for c in spots]
    assert not is_grey(theme.RED)
    theme.set_device("rm2")
    assert theme.MONO and all(is_grey(c) for c in spots)
    # the four categories stay distinguishable on a 16-level panel
    levels = sorted(round(theme.CATEGORIES[k]["color"].rgb()[0] * 15)
                    for k in theme.CATEGORY_ORDER)
    assert all(b - a >= 2 for a, b in zip(levels, levels[1:]))
    theme.set_device("paperpro")
    assert not theme.MONO and [c.rgb() for c in spots] == before


def test_texts_do_not_mention_colour_on_rm2():
    red = "Teken de weg van de rode pijl bovenaan naar de ster onderaan."
    assert theme.localize(red) == red
    theme.set_device("rm2")
    assert "rode" not in theme.localize(red)
    link = games.get("kleurlink")
    for s in [link.tagline, link.instruction({}), *link.rules]:
        s = theme.localize(s)
        assert "kleur" not in s.lower() and "Paper Pro" not in s


@pytest.mark.parametrize("level", [1, 2, 3])
def test_memory_shapes_use_tones_instead_of_colours(level):
    game = games.get("geheugen")
    theme.set_device("rm2")
    seen = 0
    for seed in range(40):
        puz = game.generate(random.Random(f"m{seed}"), level)
        game.verify(puz)
        if puz["variant"] != "vormen":
            continue
        seen += 1
        tones = {cell[1] for cell in puz["study"]["cells"]}
        assert tones <= set(geheugen.MONO_COLORS)
        assert ["maan", "wit"] not in puz["study"]["cells"]
    assert seen >= 3


def test_logic_puzzles_are_identical_on_both_devices():
    for key in ("sudoku", "bruggen", "kleurlink", "doolhof"):
        game = games.get(key)
        a = game.generate(random.Random("same"), 2)
        theme.set_device("rm2")
        b = game.generate(random.Random("same"), 2)
        theme.set_device("paperpro")
        assert a == b


@pytest.fixture(scope="module")
def rm2_book(tmp_path_factory):
    out = tmp_path_factory.mktemp("rm2") / "mini-rm2.pdf"
    stats = book.build(seed=7, out=out, jobs=1, cache=out.parent / "cache",
                       log=lambda *a: None, only={"kleurlink", "geheugen"},
                       device="rm2")
    theme.set_device("paperpro")
    return stats, pymupdf.open(str(out)), json.loads(out.with_suffix(".json").read_text())


def test_rm2_book_has_the_same_structure(rm2_book):
    stats, doc, manifest = rm2_book
    assert manifest["device"] == "rm2"
    # 8 fixed pages + kleurlink (1 + 25 + 25) + geheugen (1 + 2 * 25 + 25)
    assert doc.page_count == 8 + 51 + 76
    for page in doc:
        for l in page.get_links():
            assert l["kind"] == pymupdf.LINK_GOTO and 0 <= l["page"] < doc.page_count


def test_rm2_book_contains_no_colour(rm2_book):
    _, doc, manifest = rm2_book
    index = manifest["pages"]
    keys = ["cover", "home", "training1", "score", "hub:kleurlink", "s:kleurlink:20",
            "hub:geheugen", "colophon"]
    keys += [k for k in index if k.startswith(("p:geheugen", "s:geheugen"))][::7]
    for key in keys:
        pix = doc[index[key]].get_pixmap(matrix=pymupdf.Matrix(0.6, 0.6))
        data = pix.samples
        spread = max(max(data[i:i + 3]) - min(data[i:i + 3])
                     for i in range(0, len(data), 3 * 7))
        assert spread <= 6, f"{key} still contains colour"


def test_default_output_names():
    assert book.default_out("paperpro").name == "RemarkableMind.pdf"
    assert book.default_out("rm2").name == "RemarkableMind-rM2.pdf"
