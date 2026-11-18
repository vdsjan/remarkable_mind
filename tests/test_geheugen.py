"""Tests for the geheugen game."""
import json
import random

import pytest

from mind.games.geheugen import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"geheugen-{level}-{seed}"), level)


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


def test_two_parts_and_all_variants():
    assert GAME.parts == 2 and GAME.example is False
    seen = set()
    for seed in range(40):
        puz = make(1 + seed % 3, 100 + seed)
        GAME.verify(puz)
        seen.add(puz["variant"])
    assert seen == {"vormen", "lijst", "verhaal"}


def test_verify_rejects_wrong_answer():
    puz = make(2, 1)
    puz["questions"][0][1] = puz["questions"][0][1] + "x"
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_layout_on_paper_pro_move():
    """Generate, verify and draw every part on the 9:16 Move page."""
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme as _theme
    from mind.games import get as _get

    game = _get("geheugen")
    _theme.register_fonts()
    try:
        _theme.set_device("move")
        assert _theme.COMPACT
        import io
        c = _canvas.Canvas(io.BytesIO(), pagesize=(_theme.W, _theme.H))
        for seed in range(3):
            for level in (1, 2, 3):
                puz = game.generate(_random.Random(f"move-{seed}"), level)
                game.verify(puz)
                for part in range(game.parts):
                    for solved in (False, True):
                        game.draw(c, _theme.PLAY_BOX, puz, solved=solved, part=part)
                        c.showPage()
    finally:
        _theme.set_device("paperpro")
