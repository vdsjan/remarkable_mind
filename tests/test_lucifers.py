import json
import random

import pytest

from mind.games.lucifers import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"lucifers-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic(level, seed):
    a = GAME.generate(random.Random(f"lucifers-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"lucifers-{level}-{seed}"), level)
    assert a == b


@pytest.mark.parametrize("level,seed", CASES)
def test_json_roundtrip(level, seed):
    puz = GAME.generate(random.Random(f"lucifers-{level}-{seed}"), level)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "lucifers"
    assert GAME.name and GAME.tagline and len(GAME.rules) >= 2 and GAME.tips
    assert sum(GAME.counts) == 25


def test_known_moves():
    from mind.games import lucifers as lu
    assert lu.is_true("6+4=10") and not lu.is_true("6+4=4")
    assert "8-3=5" in lu.neighbours("8-2=5", 1)      # 2 -> 3 inside one digit
    assert "9-4=5" in lu.neighbours("6-4=5", 1)      # 6 -> 9
    assert lu.solutions("6-4=5", 1) == ["9-4=5"]
    assert not lu.well_formed("07+1=8")


def test_levels_use_the_right_number_of_moves():
    for level, moves in ((1, 1), (2, 1), (3, 2)):
        puz = GAME.generate(random.Random(f"moves-{level}"), level)
        assert puz["moves"] == moves
    two_digit = GAME.generate(random.Random("l2"), 2)["shown"]
    left = two_digit.split("=")[0]
    assert any(len(n) == 2 for n in left.replace("-", "+").split("+"))


def test_verify_rejects_ambiguous_puzzle():
    from mind.games import lucifers as lu
    # 3+3=5 has two one-move fixes: 2+3=5 and 3+2=5
    assert sorted(lu.solutions("3+3=5", 1)) == ["2+3=5", "3+2=5"]
    with pytest.raises(AssertionError, match="unique"):
        GAME.verify({"shown": "3+3=5", "answer": "2+3=5", "moves": 1})
    GAME.verify({"shown": "6+3=3", "answer": "0+3=3", "moves": 1})


def test_fits_the_move_page(tmp_path):
    """Paper Pro Move: 9:16 page; generate, verify and draw without error."""
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme as _theme
    from mind.games import get as _get

    game = _get("lucifers")
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
