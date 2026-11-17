"""Tests for the binairo game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import binairo

GAME = binairo.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"binairo-{level}-{seed}"), level)


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
    assert GAME.key == "binairo"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_solver_detects_ambiguity():
    assert binairo.count_solutions(6, [-1] * 36, 2) == 2


def test_verify_rejects_three_in_a_row():
    puz = make(1, 1)
    puz["solution"][0:3] = [1, 1, 1]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_clue_share(level, seed):
    puz = make(level, seed)
    filled = sum(1 for v in puz["grid"] if v >= 0)
    assert filled < len(puz["grid"]) * 0.6
