"""Tests for Sterrenstelsels: validity, uniqueness, determinism, JSON-safety."""
import json
import random

import pytest

from mind import theme
from mind.games.sterrenstelsels import (GAME, core_cells, count_solutions,
                                        mirror)

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"sterrenstelsels-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    GAME.verify(make(level, seed))


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a, b = make(level, seed), make(level, seed)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "sterrenstelsels" and GAME.category == "ruimte"
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25
    assert GAME.instruction(make(1, 1))


def test_geometry_helpers():
    assert core_cells((3, 3)) == [(1, 1)]                    # cell centre
    assert core_cells((3, 4)) == [(1, 1), (1, 2)]            # on a vertical line
    assert core_cells((4, 4)) == [(1, 1), (1, 2), (2, 1), (2, 2)]   # corner
    assert mirror((3, 3), 1, 1) == (1, 1)
    assert mirror((3, 4), 1, 1) == (1, 2)
    assert mirror((4, 4), 0, 3) == (3, 0)


def test_solver_counts_known_cases():
    # one dot in the middle of a 3 x 3 grid: the whole grid is one galaxy
    out = []
    assert count_solutions(3, [(3, 3)], 5, out) == 1
    assert out == [[0] * 3 for _ in range(3)]
    # 2 x 2 with two dots on the vertical edges: left and right halves
    assert count_solutions(2, [(2, 1), (2, 3)], 5) == 1
    # a dot in a corner cell of a 2 x 2 grid cannot reach the other cells
    assert count_solutions(2, [(1, 1)], 5) == 0
    # two dots claiming the same cell
    assert count_solutions(2, [(1, 1), (1, 2)], 5) == 0


def test_level_sizes_and_region_count():
    for level, n in {1: 5, 2: 7, 3: 9}.items():
        puz = make(level, 4)
        assert puz["n"] == n
        used = {k for row in puz["regions"] for k in row}
        assert used == set(range(len(puz["dots"])))
        assert puz["dots"] == sorted(puz["dots"])


def test_verify_rejects_tampering():
    puz = make(2, 2)
    n = puz["n"]
    # give one border cell to a neighbouring region: symmetry breaks
    bad = json.loads(json.dumps(puz))
    done = False
    for r in range(n):
        for c in range(n - 1):
            if not done and bad["regions"][r][c] != bad["regions"][r][c + 1]:
                bad["regions"][r][c] = bad["regions"][r][c + 1]
                done = True
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    # dropping a dot leaves cells without an owner
    bad = json.loads(json.dumps(puz))
    bad["dots"] = bad["dots"][:-1]
    with pytest.raises((AssertionError, KeyError)):
        GAME.verify(bad)


def test_fits_the_move_page(tmp_path):
    """Paper Pro Move: smaller grids; generate, verify and draw without error."""
    from reportlab.pdfgen import canvas
    try:
        theme.set_device("move")
        theme.register_fonts()
        assert theme.COMPACT
        c = canvas.Canvas(str(tmp_path / "move.pdf"), pagesize=(theme.W, theme.H))
        for level, n in ((1, 5), (2, 6), (3, 7)):
            for seed in range(3):
                puz = GAME.generate(random.Random(f"move-{seed}"), level)
                GAME.verify(puz)
                assert puz["n"] == n
                assert theme.PLAY_BOX[2] / n >= 18          # cells stay drawable
                for solved in (False, True):
                    GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
        GAME.icon(c, 30, 30, 26, theme.INK)
        c.save()
    finally:
        theme.set_device("paperpro")
