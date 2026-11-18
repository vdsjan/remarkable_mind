"""Tests for the kleurlink game: validity, uniqueness, determinism, JSON-safety."""
import json
import random

import pytest

from mind.games.kleurlink import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"kleurlink-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a = GAME.generate(random.Random(f"kleurlink-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"kleurlink-{level}-{seed}"), level)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "kleurlink"
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25


def test_solver_counts_known_cases():
    from mind.games.kleurlink import count_solutions
    # 2x2 with one pair in adjacent corners: the only cover is the U-shape
    assert count_solutions(2, [[0, 0, 1, 0]], 5) == 1
    # 3x3, pair in opposite corners: the two S-shaped snakes
    assert count_solutions(3, [[0, 0, 2, 2]], 5) == 2
    # dots of two colours that cannot both be joined
    assert count_solutions(2, [[0, 0, 1, 1], [0, 1, 1, 0]], 5) == 0


def test_verify_rejects_uncovered_grid():
    puz = GAME.generate(random.Random("kleurlink-reject"), 1)
    bad = json.loads(json.dumps(puz))
    bad["paths"][0] = bad["paths"][0][:1] + bad["paths"][0][-1:]
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_level_sizes():
    for level, (n, lo, hi) in {1: (5, 4, 5), 2: (6, 5, 6), 3: (7, 6, 7)}.items():
        puz = GAME.generate(random.Random(f"size-{level}"), level)
        assert puz["n"] == n and lo <= len(puz["dots"]) <= hi
        assert all(len(p) >= 3 for p in puz["paths"])


def test_fits_the_move_page(tmp_path):
    """Paper Pro Move: 9:16 page; generate, verify and draw without error."""
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme as _theme
    from mind.games import get as _get

    game = _get("kleurlink")
    try:
        _theme.set_device("move")
        _theme.register_fonts()
        assert _theme.COMPACT
        c = _canvas.Canvas(str(tmp_path / "move.pdf"), pagesize=(_theme.W, _theme.H))
        for level in (1, 2, 3):
            for seed in range(3):
                puz = game.generate(_random.Random(f"move-{seed}"), level)
                game.verify(puz)
                for solved in (False, True):
                    game.draw(c, _theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
        c.save()
    finally:
        _theme.set_device("paperpro")
