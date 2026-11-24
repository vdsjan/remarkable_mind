"""Tests for Lichtplan (Akari): valid, unique, deterministic, serialisable."""
import io
import json
import random

import pytest
from reportlab.pdfgen.canvas import Canvas

from mind import theme
from mind.games import lichtplan

GAME = lichtplan.GAME
OPEN, BLOCK = lichtplan.OPEN, lichtplan.BLOCK
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"lichtplan-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = make(level, seed)
    GAME.verify(puz)
    assert puz["n"] == lichtplan.SIZES[level]
    assert puz["lamps"], "a plan without lamps is no puzzle"


@pytest.mark.parametrize("level", (1, 2, 3))
def test_deterministic(level):
    assert make(level, 7) == make(level, 7)


@pytest.mark.parametrize("level", (1, 2, 3))
def test_json_roundtrip(level):
    puz = make(level, 5)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "lichtplan" and GAME.category == "logica"
    assert GAME.name and GAME.tagline and GAME.instruction({})
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25
    for s in [GAME.tagline, GAME.instruction({}), *GAME.rules, *GAME.tips]:
        assert not any(w in s.lower() for w in ("geel", "gele", "blauw", "rood", "rode"))


def test_solver_on_known_boards():
    # an empty 2 x 2 room: lamps on either diagonal
    sols, _ = lichtplan.solve(2, [OPEN] * 4, 5)
    assert sorted(sols) == [[0, 3], [1, 2]]
    # a 0 in a corner rules out one diagonal
    sols, branches = lichtplan.solve(3, [0, OPEN, OPEN,
                                         OPEN, BLOCK, OPEN,
                                         OPEN, OPEN, OPEN], 5)
    assert len(sols) == 1 and sols[0] == [2, 6] and branches == 0
    # a 4 without four free neighbours cannot be solved
    assert lichtplan.solve(2, [4, OPEN, OPEN, OPEN], 2)[0] == []


@pytest.mark.parametrize("level", (1, 2))
def test_easy_levels_need_no_guessing(level):
    for seed in (1, 2, 3):
        puz = make(level, seed)
        assert lichtplan.solve(puz["n"], puz["cells"], 2)[1] == 0


def test_levels_drop_numbers():
    def share(level):
        tot = num = 0
        for seed in range(6):
            blocks = [v for v in make(level, seed)["cells"] if v != OPEN]
            tot += len(blocks)
            num += sum(1 for v in blocks if v != BLOCK)
        return num / tot
    assert share(1) > share(3)


def test_verify_rejects_tampering():
    puz = make(2, 1)
    moved = dict(puz, lamps=puz["lamps"][1:])            # a room stays dark
    with pytest.raises(AssertionError):
        GAME.verify(moved)
    wrong = dict(puz, cells=list(puz["cells"]))
    i = next(i for i, v in enumerate(wrong["cells"]) if 0 <= v <= 4)
    wrong["cells"][i] = (wrong["cells"][i] + 1) % 5      # a number that lies
    with pytest.raises(AssertionError):
        GAME.verify(wrong)
    bare = dict(puz, cells=[v if v == OPEN else BLOCK for v in puz["cells"]])
    if len(lichtplan.solve(bare["n"], bare["cells"], 2)[0]) > 1:
        with pytest.raises(AssertionError):              # no longer unique
            GAME.verify(bare)


def _draw(puz, solved):
    c = Canvas(io.BytesIO(), pagesize=(theme.W, theme.H))
    sizes = []
    set_font = c.setFont
    c.setFont = lambda name, size, leading=None: (sizes.append(size),
                                                  set_font(name, size, leading))[1]
    GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
    on_page = list(sizes)                    # the icon is not part of the page
    GAME.icon(c, 30, 30, 26, theme.INK)
    c.showPage()
    c.save()
    return on_page


@pytest.mark.parametrize("device", ("paperpro", "rm2"))
def test_draws_on_wide_devices(device):
    theme.register_fonts()
    theme.set_device(device)
    try:
        puz = make(3, 2)
        for solved in (False, True):
            _draw(puz, solved)
    finally:
        theme.set_device("paperpro")


@pytest.mark.parametrize("level,seed", CASES)
def test_fits_the_move_page(level, seed):
    theme.register_fonts()
    theme.set_device("move")
    try:
        puz = make(level, seed)
        GAME.verify(puz)
        assert puz["n"] == lichtplan.SIZES_COMPACT[level]
        assert theme.PLAY_BOX[2] / puz["n"] >= 18, "cells too small to mark"
        for solved in (False, True):
            sizes = _draw(puz, solved)
            assert min(sizes) >= 7.5, "text too small for the 7.3-inch screen"
    finally:
        theme.set_device("paperpro")
