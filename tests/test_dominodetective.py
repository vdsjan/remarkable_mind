"""Tests for Dominodetective: validity, uniqueness, determinism, JSON-safety."""
import json
import random

import pytest

from mind import theme
from mind.games.dominodetective import GAME, all_pairs, count_solutions

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"dominodetective-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    GAME.verify(make(level, seed))


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a, b = make(level, seed), make(level, seed)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "dominodetective" and GAME.category == "getallen"
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25
    assert GAME.instruction(make(1, 1))


def test_level_sets():
    for level, n in {1: 3, 2: 4, 3: 6}.items():
        puz = make(level, 7)
        assert puz["n"] == n
        assert len(puz["grid"]) == n + 1 and len(puz["grid"][0]) == n + 2
        assert len(puz["dominoes"]) == len(all_pairs(n)) == (n + 1) * (n + 2) // 2


def test_solver_counts_known_cases():
    # double-1 set (0-0, 0-1, 1-1) on a 2 x 3 grid
    assert count_solutions([[0, 0, 1], [0, 1, 1]], 1, 5) == 3   # all three tilings work
    # the 0-1 pair would be needed twice, 0-0 never: no solution
    assert count_solutions([[0, 1, 0], [1, 0, 1]], 1, 5) == 0
    # wrong shape for the set
    assert count_solutions([[0, 0], [1, 1]], 1, 5) == 0
    found = []
    puz = make(2, 3)
    assert count_solutions(puz["grid"], puz["n"], 2, found) == 1
    assert sorted(found) == puz["dominoes"]


def test_verify_rejects_tampering():
    puz = make(1, 5)
    bad = json.loads(json.dumps(puz))
    bad["dominoes"] = bad["dominoes"][:-1]
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    r1, c1, r2, c2 = bad["dominoes"][0]
    bad["grid"][r1][c1], bad["grid"][r2][c2] = 0, 0
    r1, c1, r2, c2 = bad["dominoes"][1]
    bad["grid"][r1][c1], bad["grid"][r2][c2] = 0, 0      # 0-0 now occurs twice
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_fits_the_move_page(tmp_path):
    """Paper Pro Move: smaller set on level 3; generate, verify and draw."""
    from reportlab.pdfgen import canvas
    try:
        theme.set_device("move")
        theme.register_fonts()
        assert theme.COMPACT
        c = canvas.Canvas(str(tmp_path / "move.pdf"), pagesize=(theme.W, theme.H))
        for level in (1, 2, 3):
            for seed in range(3):
                puz = GAME.generate(random.Random(f"move-{seed}"), level)
                GAME.verify(puz)
                assert puz["n"] <= 5
                for solved in (False, True):
                    GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
        GAME.icon(c, 30, 30, 26, theme.INK)
        c.save()
    finally:
        theme.set_device("paperpro")
