"""Tests for the doolhof game: validity, uniqueness, determinism, JSON-safety."""
import json
import random

import pytest

from mind.games.doolhof import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"doolhof-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a = GAME.generate(random.Random(f"doolhof-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"doolhof-{level}-{seed}"), level)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "doolhof"
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25


def test_shapes_per_level():
    assert GAME.generate(random.Random("a"), 1)["type"] == "rect"
    assert GAME.generate(random.Random("a"), 2)["type"] == "rect"
    puz = GAME.generate(random.Random("a"), 3)
    assert puz["type"] == "circle" and puz["end"] == 0 and len(puz["counts"]) == 9


def test_verify_rejects_loop_and_wall_crossing():
    puz = GAME.generate(random.Random("doolhof-reject"), 1)
    bad = json.loads(json.dumps(puz))
    bad["open"][0] = bad["open"][1]                 # duplicate passage, one cell cut off
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    bad["path"] = [bad["path"][0], bad["path"][-1]]  # jumps straight to the goal
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_routes_are_long_enough_to_be_fun():
    for level, minimum in ((1, 20), (2, 40), (3, 12)):
        puz = GAME.generate(random.Random(f"len-{level}"), level)
        assert len(puz["path"]) >= minimum


def test_fits_the_move_page(tmp_path):
    """Paper Pro Move: 9:16 page; generate, verify and draw without error."""
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme as _theme
    from mind.games import get as _get

    game = _get("doolhof")
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
