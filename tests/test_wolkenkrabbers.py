"""Tests for the wolkenkrabbers game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import wolkenkrabbers

GAME = wolkenkrabbers.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"wolkenkrabbers-{level}-{seed}"), level)


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
    assert GAME.key == "wolkenkrabbers"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_visible():
    assert wolkenkrabbers.visible([1, 2, 3, 4]) == 4
    assert wolkenkrabbers.visible([4, 1, 2, 3]) == 1
    assert wolkenkrabbers.visible([2, 1, 4, 3]) == 2


def test_solver_detects_ambiguity():
    n = 4
    none = [0] * n
    assert wolkenkrabbers.count_solutions(n, none, none, none, none,
                                          [0] * 16, 2) == 2


def test_verify_rejects_tampered_clue():
    puz = make(1, 1)
    side = next(s for s in ("top", "bottom", "left", "right") if any(puz[s]))
    k = next(i for i, v in enumerate(puz[side]) if v)
    puz[side][k] = puz[side][k] % 4 + 1
    with pytest.raises(AssertionError):
        GAME.verify(puz)
