"""Tests for the woordzoeker game."""
import json
import random

import pytest

from mind.games.woordzoeker import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"woordzoeker-{level}-{seed}"), level)


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


def test_level_shapes():
    from mind.games.woordzoeker import E, S, SE, LEVELS
    for level, size in ((1, 11), (2, 13), (3, 15)):
        puz = make(level, 7)
        assert puz["size"] == size
        assert all((dr, dc) in LEVELS[level][1] for _, _, _, dr, dc in puz["words"])
    assert LEVELS[1][1] == (E, S, SE)


def test_verify_rejects_broken_grid():
    puz = make(1, 1)
    word, r, c, dr, dc = puz["words"][0]
    rows = [list(row) for row in puz["grid"]]
    rows[r][c] = "Q" if rows[r][c] != "Q" else "X"
    puz["grid"] = ["".join(row) for row in rows]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_themes_are_clean():
    from mind.games._woorden import GENERIC_SOLUTIONS, THEMES
    assert len(THEMES) >= 14
    for title, words, phrases in THEMES:
        assert len(words) >= 16 and len(set(words)) == len(words)
        assert all(w.isalpha() and w.isupper() and w.isascii() and 4 <= len(w) <= 12
                   for w in words), title
        assert all(p.replace(" ", "").isalpha() and p.isupper() and p.isascii()
                   for p in phrases + GENERIC_SOLUTIONS), title
