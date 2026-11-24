"""Tests for Eilandenrijk (Nurikabe): valid, unique, deterministic."""
import io
import json
import random

import pytest
from reportlab.pdfgen.canvas import Canvas

from mind import theme
from mind.games import eilandenrijk

GAME = eilandenrijk.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"eilandenrijk-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = make(level, seed)
    GAME.verify(puz)
    n = puz["n"]
    assert n == eilandenrijk.SIZES[level]
    sizes = [k for _, _, k in puz["clues"]]
    assert max(sizes) <= eilandenrijk.MAX_ISLAND[level]
    assert sum(sizes) + sum(puz["sea"]) == n * n


@pytest.mark.parametrize("level", (1, 2, 3))
def test_deterministic(level):
    assert make(level, 7) == make(level, 7)


@pytest.mark.parametrize("level", (1, 2, 3))
def test_json_roundtrip(level):
    puz = make(level, 5)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "eilandenrijk" and GAME.category == "logica"
    assert GAME.name and GAME.tagline and GAME.instruction({})
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_solver_on_known_boards():
    solve = eilandenrijk.solve
    # 2 x 2 with one island of 1: the three other cells are sea
    assert solve(2, [[0, 0, 1]], 5)[0] == [[0, 1, 1, 1]]
    # 3 x 3 with a lone 1 would need a 2 x 2 block of sea
    assert solve(3, [[0, 0, 1]], 5)[0] == []
    # a 2 in the corner of a 2 x 2 board can grow right or down
    assert len(solve(2, [[0, 0, 2]], 5)[0]) == 2
    # two numbers that would share an island leave no solution
    assert solve(1, [[0, 0, 1]], 5)[0] == [[0]]
    assert solve(2, [[0, 0, 2], [0, 1, 2]], 5)[0] == []


def test_first_level_needs_no_guessing():
    for seed in (1, 2, 3, 4):
        puz = make(1, seed)
        assert eilandenrijk.solve(puz["n"], puz["clues"], 2)[1] == 0


def test_verify_rejects_tampering():
    puz = make(2, 1)
    n = puz["n"]
    flooded = dict(puz, sea=[1] * (n * n))               # islands drowned
    with pytest.raises(AssertionError):
        GAME.verify(flooded)
    grown = dict(puz, clues=[list(c) for c in puz["clues"]])
    grown["clues"][0][2] += 1                            # a number that lies
    with pytest.raises(AssertionError):
        GAME.verify(grown)
    fewer = dict(puz, clues=puz["clues"][1:])            # an island without number
    with pytest.raises(AssertionError):
        GAME.verify(fewer)


def test_verify_rejects_a_second_solution():
    # a 2 in a corner fits two ways: the stored answer is valid but not unique
    puz = {"n": 2, "clues": [[0, 0, 2]], "sea": [0, 0, 1, 1]}
    with pytest.raises(AssertionError, match="unique"):
        GAME.verify(puz)


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
        assert theme.PLAY_BOX[2] / puz["n"] >= 18, "cells too small to shade"
        for solved in (False, True):
            sizes = _draw(puz, solved)
            assert min(sizes) >= 7.5, "text too small for the 7.3-inch screen"
    finally:
        theme.set_device("paperpro")
