import json
import random

import pytest

from mind.games.sudoku import GAME


@pytest.mark.parametrize("level", [1, 2, 3])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_generate_verify(level, seed):
    puz = GAME.generate(random.Random(f"s{seed}"), level)
    GAME.verify(puz)
    assert json.loads(json.dumps(puz)) == puz
    assert puz == GAME.generate(random.Random(f"s{seed}"), level)


def test_levels_get_harder():
    clues = [sum(1 for v in GAME.generate(random.Random("x"), lvl)["grid"] if v)
             for lvl in (1, 2, 3)]
    assert clues[0] > clues[1] > clues[2]
    assert clues[2] <= 28


def test_verify_rejects_tampering():
    puz = GAME.generate(random.Random("t"), 1)
    i = next(i for i, v in enumerate(puz["grid"]) if v)
    puz["grid"][i] = 0
    j = next(k for k, v in enumerate(puz["grid"]) if v and k != i)
    puz["grid"][j] = 0
    bad = dict(puz, solution=[(v % 9) + 1 for v in puz["solution"]])
    with pytest.raises(AssertionError):
        GAME.verify(bad)
