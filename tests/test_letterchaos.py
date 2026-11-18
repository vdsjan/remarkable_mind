"""Tests for the letterchaos game."""
import json
import random

import pytest

from mind.games.letterchaos import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"letterchaos-{level}-{seed}"), level)


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


def test_word_counts_and_lengths():
    for level, (n, lo, hi) in ((1, (8, 4, 6)), (2, (9, 6, 8)), (3, (10, 8, 12))):
        puz = make(level, 5)
        assert len(puz["items"]) == n == len(puz["bonus"])
        assert all(lo <= len(answer) <= hi for _, answer, _ in puz["items"])


def test_no_anagram_twins_in_any_theme():
    from mind.games._woorden import BONUS, THEMES
    for title, words, _ in THEMES:
        keys = ["".join(sorted(w)) for w in words]
        assert len(set(keys)) == len(keys), title
    for n, words in BONUS.items():
        assert len(words) >= 20 and all(len(w) == n and w.isalpha() for w in words)


def test_verify_rejects_wrong_bonus():
    puz = make(1, 1)
    puz["bonus"] = puz["bonus"][::-1]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_layout_on_paper_pro_move():
    """Generate, verify and draw every part on the 9:16 Move page."""
    import random as _random

    from reportlab.pdfgen import canvas as _canvas

    from mind import theme as _theme
    from mind.games import get as _get

    game = _get("letterchaos")
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
