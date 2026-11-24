"""Tests for the woordladder game."""
import io
import json
import random

import pytest

from mind.games import woordladder
from mind.games.woordladder import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"woordladder-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    GAME.verify(make(level, seed))


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic(level, seed):
    assert make(level, seed) == make(level, seed)


@pytest.mark.parametrize("level,seed", CASES)
def test_json_roundtrip(level, seed):
    puz = make(level, seed)
    assert json.loads(json.dumps(puz)) == puz
    GAME.verify(json.loads(json.dumps(puz)))


@pytest.mark.parametrize("level,seed", CASES)
def test_routes_are_shortest_and_step_one_letter(level, seed):
    puz = make(level, seed)
    n, changes, count = woordladder.LEVELS[level]
    assert puz["letters"] == n and len(puz["ladders"]) == count
    g, _ends = woordladder.graph(n)
    for ladder in puz["ladders"]:
        route = ladder["route"]
        assert len(route) - 1 in changes
        assert woordladder.distances(g, route[0])[route[-1]] == len(route) - 1
        for a, b in zip(route, route[1:]):
            assert sum(x != y for x, y in zip(a, b)) == 1
        assert ladder["fixed"][0] == 0 and ladder["fixed"][-1] == len(route) - 1
        assert len(ladder["fixed"]) == (3 if level == 3 else 2)


def test_word_list_is_clean():
    for n in (3, 4):
        ws = woordladder.words(n)
        assert all(len(w) == n and w.isalpha() and w.islower() for w in ws)
        assert not set(ws) & woordladder.SKIP
        g, ends = woordladder.graph(n)
        assert set(ends) <= set(g)


def test_fingerprints_name_every_ladder():
    puz = make(2, 1)
    keys = GAME.fingerprints(puz)
    assert len(keys) == len(set(keys)) == len(puz["ladders"])


def test_verify_rejects_tampered_route():
    puz = make(2, 1)
    route = puz["ladders"][0]["route"]
    route[1] = route[0][::-1] if route[0][::-1] != route[0] else "zzzz"
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_verify_rejects_detour():
    puz = make(1, 2)
    route = puz["ladders"][0]["route"]
    route.insert(1, route[0])
    puz["ladders"][0]["fixed"][-1] = len(route) - 1
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_layout_on_paper_pro_move():
    """Generate, verify and draw every part on the 9:16 Move page."""
    from reportlab.pdfgen import canvas

    from mind import theme

    theme.register_fonts()
    try:
        theme.set_device("move")
        assert theme.COMPACT
        c = canvas.Canvas(io.BytesIO(), pagesize=(theme.W, theme.H))
        for seed in range(3):
            for level in (1, 2, 3):
                puz = GAME.generate(random.Random(f"move-{seed}"), level)
                GAME.verify(puz)
                assert len(puz["ladders"]) == woordladder.LEVELS_COMPACT[level][2]
                for solved in (False, True):
                    GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
    finally:
        theme.set_device("paperpro")
