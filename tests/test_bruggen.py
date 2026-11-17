"""Tests for the bruggen game: validity, uniqueness, determinism, JSON-safety."""
import json
import random

import pytest

from mind.games.bruggen import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"bruggen-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a = GAME.generate(random.Random(f"bruggen-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"bruggen-{level}-{seed}"), level)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "bruggen"
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25


def test_verify_rejects_wrong_solution():
    puz = GAME.generate(random.Random("bruggen-reject"), 1)
    bad = json.loads(json.dumps(puz))
    bad["bridges"][0][2] = 3 - bad["bridges"][0][2]      # 1 <-> 2
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_solver_detects_ambiguous_puzzle():
    from mind.games.bruggen import solve
    # four islands on a square, all 2: ring of singles, or two double pairs (x2)
    islands = [[0, 0, 2], [0, 2, 2], [2, 0, 2], [2, 2, 2]]
    assert len(solve(islands, 5)[0]) == 1          # only the ring is connected
    islands = [[0, 0, 3], [0, 2, 3], [2, 0, 3], [2, 2, 3]]
    assert len(solve(islands, 5)[0]) == 2          # doubles top/bottom or left/right


def test_level_sizes():
    for level, (n, lo, hi) in {1: (7, 8, 10), 2: (9, 12, 16), 3: (11, 18, 24)}.items():
        puz = GAME.generate(random.Random(f"size-{level}"), level)
        assert puz["size"] == n and lo <= len(puz["islands"]) <= hi
