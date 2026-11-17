"""Tests for the piramide game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import piramide

GAME = piramide.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"piramide-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    GAME.verify(make(level, seed))


@pytest.mark.parametrize("level", (1, 2, 3))
def test_deterministic(level):
    assert make(level, 7) == make(level, 7)


@pytest.mark.parametrize("level", (1, 2, 3))
def test_json_roundtrip(level):
    puz = make(level, 5)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "piramide"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_levels_shape():
    assert [len(make(lv, 1)["pyramids"]) for lv in (1, 2, 3)] == [2, 1, 1]
    assert [make(lv, 1)["pyramids"][0]["base"] for lv in (1, 2, 3)] == [4, 5, 6]


def test_rank_check_rejects_dependent_givens():
    # the two bottom bricks and the brick above them are linearly dependent
    assert piramide.solve_base(3, [[0, 0, 1], [0, 1, 2], [1, 0, 3]]) is None
    assert piramide.solve_base(3, [[0, 0, 1], [1, 1, 5], [2, 0, 8]]) == [1, 2, 3]


def test_verify_rejects_wrong_given():
    puz = make(2, 1)
    puz["pyramids"][0]["givens"][0][2] += 1
    with pytest.raises(AssertionError):
        GAME.verify(puz)
