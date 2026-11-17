import json
import random

import pytest

from mind.games.nonogram import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"nonogram-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic(level, seed):
    a = GAME.generate(random.Random(f"nonogram-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"nonogram-{level}-{seed}"), level)
    assert a == b


@pytest.mark.parametrize("level,seed", CASES)
def test_json_roundtrip(level, seed):
    puz = GAME.generate(random.Random(f"nonogram-{level}-{seed}"), level)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "nonogram"
    assert GAME.name and GAME.tagline and len(GAME.rules) >= 2 and GAME.tips
    assert sum(GAME.counts) == 25


def test_every_library_icon_is_unique():
    from mind.games import nonogram as n
    assert len(n.ICONS_10) >= 12 and len(n.ICONS_15) >= 8
    for size, lib in ((10, n.ICONS_10), (15, n.ICONS_15)):
        for name, (title, art) in lib.items():
            grid = n._parse(art)
            assert len(grid) == size and len(grid[0]) == size, name
            assert title
            assert n.is_unique(grid), f"{name} is not uniquely solvable"


def test_solver_spots_ambiguity():
    from mind.games import nonogram as n
    # a 2x2 checkerboard has two solutions
    assert n.count_solutions([[1], [1]], [[1], [1]], 2) == 2
    puz = GAME.generate(random.Random("amb"), 1)
    bad = dict(puz, rows=[[1]] * puz["size"], cols=[[1]] * puz["size"])
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_avoid_skips_used_pictures():
    from mind.games import nonogram as n
    used = set(n.ICONS_10)
    puz = GAME.generate(random.Random("avoid"), 1, avoid=used)
    assert puz["pic"] == ""
