import json
import random

import pytest

from mind.games.logigram import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = GAME.generate(random.Random(f"logigram-{level}-{seed}"), level)
    GAME.verify(puz)


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic(level, seed):
    a = GAME.generate(random.Random(f"logigram-{level}-{seed}"), level)
    b = GAME.generate(random.Random(f"logigram-{level}-{seed}"), level)
    assert a == b


@pytest.mark.parametrize("level,seed", CASES)
def test_json_roundtrip(level, seed):
    puz = GAME.generate(random.Random(f"logigram-{level}-{seed}"), level)
    assert json.loads(json.dumps(puz)) == puz


def test_metadata():
    assert GAME.key == "logigram"
    assert GAME.name and GAME.tagline and len(GAME.rules) >= 2 and GAME.tips
    assert sum(GAME.counts) == 25


def test_dropping_a_clue_breaks_uniqueness():
    from mind.games.logigram import solve
    puz = GAME.generate(random.Random("drop"), 2)
    for i in range(len(puz["clues"])):
        fewer = dict(puz, clues=puz["clues"][:i] + puz["clues"][i + 1:])
        assert len(solve(fewer, 2)) == 2, "every clue must be needed"
    with pytest.raises(AssertionError):
        GAME.verify(dict(puz, clues=puz["clues"][1:]))


def test_clue_counts_and_shapes():
    from mind.games.logigram import CLUE_RANGE, SHAPE
    for level in (1, 2, 3):
        puz = GAME.generate(random.Random(f"shape-{level}"), level)
        k, n = SHAPE[level]
        assert len(puz["cats"]) == k and len(puz["cats"][0]["items"]) == n
        lo, hi = CLUE_RANGE[level]
        assert lo <= len(puz["clues"]) <= hi
        assert all(c["text"][0].isupper() for c in puz["clues"])


# --- reMarkable Paper Pro Move (9:16, compact) ---------------------------------
def test_move_device_generates_and_renders():
    import io
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme
    from mind.games.logigram import GAME as _GAME
    from mind.theme import register_fonts

    register_fonts()
    theme.set_device("move")
    try:
        assert theme.COMPACT
        for level in (1, 2, 3):
            for seed in range(3):
                puz = _GAME.generate(_random.Random(f"move-{seed}"), level)
                _GAME.verify(puz)
                c = _canvas.Canvas(io.BytesIO(), pagesize=(theme.W, theme.H))
                for solved in (False, True):
                    _GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
                c.save()
    finally:
        theme.set_device("paperpro")


def test_move_level3_fits_three_by_four_and_paper_pro_stays_four_by_four():
    import random as _random

    from mind import theme
    from mind.games.logigram import GAME as _GAME

    assert len(_GAME.generate(_random.Random("l"), 3)["cats"]) == 4
    theme.set_device("move")
    try:
        for seed in range(5):
            puz = _GAME.generate(_random.Random(f"l{seed}"), 3)
            assert len(puz["cats"]) == 3 and len(puz["cats"][0]["items"]) == 4
            assert 6 <= len(puz["clues"]) <= 8
            assert sum(c["t"] == "pos" for c in puz["clues"]) <= 1
    finally:
        theme.set_device("paperpro")
