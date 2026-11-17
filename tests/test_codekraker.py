"""Tests for the codekraker game."""
import json
import random

import pytest

from mind.games.codekraker import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"codekraker-{level}-{seed}"), level)


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


def test_given_letters_per_level():
    for level, n in ((1, 5), (2, 3), (3, 1)):
        assert len(make(level, 4)["given"]) == n


def test_proverbs_are_clean():
    from mind.games._woorden import SPREEKWOORDEN
    from mind.games.codekraker import _by_level, _plain
    assert len(SPREEKWOORDEN) >= 45
    assert len({p for p, _ in SPREEKWOORDEN}) == len(SPREEKWOORDEN)
    for proverb, meaning in SPREEKWOORDEN:
        assert 24 <= len(_plain(proverb).replace(" ", "")) <= 60, proverb
        assert meaning.endswith(".")
    groups = _by_level()
    assert max(len(_plain(p)) for p, _ in groups[1]) <= min(len(_plain(p)) + 3 for p, _ in groups[3])


def test_verify_rejects_wrong_code():
    puz = make(2, 1)
    puz["code"][0], puz["code"][1] = puz["code"][1], puz["code"][0]
    if "A" in puz["text"] or "B" in puz["text"]:
        with pytest.raises(AssertionError):
            GAME.verify(puz)
