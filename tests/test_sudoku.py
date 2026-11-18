import json
import random

import pytest

from mind.games.sudoku import GAME


@pytest.mark.parametrize("level", [1, 2, 3])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_generate_verify(level, seed):
    puz = GAME.generate(random.Random(f"s{seed}"), level)
    GAME.verify(puz)
    assert json.loads(json.dumps(puz)) == puz
    assert puz == GAME.generate(random.Random(f"s{seed}"), level)


def test_levels_get_harder():
    clues = [sum(1 for v in GAME.generate(random.Random("x"), lvl)["grid"] if v)
             for lvl in (1, 2, 3)]
    assert clues[0] > clues[1] > clues[2]
    assert clues[2] <= 28


def test_verify_rejects_tampering():
    puz = GAME.generate(random.Random("t"), 1)
    i = next(i for i, v in enumerate(puz["grid"]) if v)
    puz["grid"][i] = 0
    j = next(k for k, v in enumerate(puz["grid"]) if v and k != i)
    puz["grid"][j] = 0
    bad = dict(puz, solution=[(v % 9) + 1 for v in puz["solution"]])
    with pytest.raises(AssertionError):
        GAME.verify(bad)


CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"sudoku-{level}-{seed}"), level)


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
