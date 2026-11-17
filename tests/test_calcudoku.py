"""Tests for the calcudoku game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import calcudoku

GAME = calcudoku.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"calcudoku-{level}-{seed}"), level)


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
    assert GAME.key == "calcudoku"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_verify_rejects_wrong_solution():
    puz = make(1, 1)
    puz["solution"][0], puz["solution"][1] = puz["solution"][1], puz["solution"][0]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_solver_detects_ambiguity():
    # a 2x2 grid with two "+3" domino cages has two solutions
    cages = [{"cells": [0, 1], "op": "+", "target": 3},
             {"cells": [2, 3], "op": "+", "target": 3}]
    assert calcudoku.count_solutions(2, cages, 2) == 2
