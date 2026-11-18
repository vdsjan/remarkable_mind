"""Tests for the reeksen game: valid, unique, deterministic, serialisable."""
import json
import random

import pytest

from mind.games import reeksen

GAME = reeksen.GAME
CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"reeksen-{level}-{seed}"), level)


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
    assert GAME.key == "reeksen"
    assert GAME.name and GAME.tagline
    assert GAME.category in ("getallen", "logica", "ruimte", "taal")
    assert 2 <= len(GAME.rules) <= 4 and 1 <= len(GAME.tips) <= 2
    assert sum(GAME.counts) == 25


def test_expand_rules():
    ex = reeksen.expand
    assert ex({"type": "cycle", "start": 3, "ops": [["+", 4]]}, 4) == [3, 7, 11, 15]
    assert ex({"type": "cycle", "start": 2, "ops": [["*", 2], ["-", 1]]}, 5) == [2, 4, 3, 6, 5]
    assert ex({"type": "affine", "start": 1, "k": 2, "c": 1}, 4) == [1, 3, 7, 15]
    assert ex({"type": "growdiff", "start": 1, "d": 1, "e": 1}, 5) == [1, 2, 4, 7, 11]
    assert ex({"type": "diffgeom", "start": 1, "d": 1, "r": 2}, 5) == [1, 2, 4, 8, 16]
    assert ex({"type": "power", "n0": 1, "p": 2, "c": 0}, 4) == [1, 4, 9, 16]
    assert ex({"type": "fib", "start": [1, 1]}, 6) == [1, 1, 2, 3, 5, 8]
    assert ex({"type": "mulgrow", "start": 1, "f": 1}, 5) == [1, 1, 2, 6, 24]
    assert ex({"type": "primes", "i0": 0}, 4) == [2, 3, 5, 7]
    inter = {"type": "interleave",
             "a": {"type": "cycle", "start": 1, "ops": [["+", 1]]},
             "b": {"type": "cycle", "start": 10, "ops": [["*", 2]]}}
    assert ex(inter, 6) == [1, 10, 2, 20, 3, 40]


def test_six_rows_with_distinct_families():
    for level in (1, 2, 3):
        puz = make(level, 1)
        assert len(puz["rows"]) == 6
        assert all(reeksen.explain(r["rule"]) for r in puz["rows"])


def test_verify_rejects_wrong_term():
    puz = make(1, 1)
    puz["rows"][0]["terms"][-1] += 1
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
