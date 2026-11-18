"""Tests for the piramide game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import piramide

GAME = piramide.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"piramide-{level}-{seed}"), level)


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
    assert GAME.key == "piramide"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_levels_shape():
    assert [len(make(lv, 1)["pyramids"]) for lv in (1, 2, 3)] == [2, 1, 1]
    assert [make(lv, 1)["pyramids"][0]["base"] for lv in (1, 2, 3)] == [4, 5, 6]


def test_rank_check_rejects_dependent_givens():
    # the two bottom bricks and the brick above them are linearly dependent
    assert piramide.solve_base(3, [[0, 0, 1], [0, 1, 2], [1, 0, 3]]) is None
    assert piramide.solve_base(3, [[0, 0, 1], [1, 1, 5], [2, 0, 8]]) == [1, 2, 3]


def test_verify_rejects_wrong_given():
    puz = make(2, 1)
    puz["pyramids"][0]["givens"][0][2] += 1
    with pytest.raises(AssertionError):
        GAME.verify(puz)


# --- reMarkable Paper Pro Move (9:16, compact page) ---------------------------
class _RecordingCanvas:
    """Canvas that records font sizes and the extent of every drawn string."""

    def __new__(cls, size):
        import io
        from reportlab.pdfgen.canvas import Canvas

        class Rec(Canvas):
            def __init__(self):
                super().__init__(io.BytesIO(), pagesize=size)
                self.sizes, self.spans = [], []

            def setFont(self, name, sz, leading=None):
                self.sizes.append(sz)
                super().setFont(name, sz, leading)

            def _span(self, x0, t, y):
                w = self.stringWidth(t, self._fontname, self._fontsize)
                self.spans.append((x0(w), x0(w) + w, y))

            def drawString(self, x, y, t, *a, **k):
                self._span(lambda w: x, t, y)
                super().drawString(x, y, t, *a, **k)

            def drawCentredString(self, x, y, t, *a, **k):
                self._span(lambda w: x - w / 2, t, y)
                super().drawCentredString(x, y, t, *a, **k)

            def drawRightString(self, x, y, t, *a, **k):
                self._span(lambda w: x - w, t, y)
                super().drawRightString(x, y, t, *a, **k)

        return Rec()


@pytest.fixture
def move_device():
    from mind import theme
    theme.register_fonts()
    theme.set_device("move")
    try:
        yield theme
    finally:
        theme.set_device("paperpro")


@pytest.mark.parametrize("level,seed", CASES)
def test_fits_paper_pro_move(move_device, level, seed):
    theme = move_device
    puz = make(level, seed)
    GAME.verify(puz)
    x, y, w, h = theme.PLAY_BOX
    for solved in (False, True):
        c = _RecordingCanvas((theme.W, theme.H))
        GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
        c.showPage()
        c.save()
        assert min(c.sizes) >= 7.5, "text too small for the 7.3-inch screen"
        for x0, x1, yy in c.spans:
            assert x - 0.5 <= x0 and x1 <= x + w + 0.5, "text outside the box"
            assert y - 0.5 <= yy <= y + h + 0.5, "text outside the box"
