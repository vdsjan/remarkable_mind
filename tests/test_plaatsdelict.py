"""Tests for the plaatsdelict game."""
import io
import json
import random

import pytest

from mind.games import plaatsdelict
from mind.games.plaatsdelict import GAME

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"plaatsdelict-{level}-{seed}"), level)


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
    GAME.verify(json.loads(json.dumps(puz)))


@pytest.mark.parametrize("level,seed", CASES)
def test_unique_solution_and_single_thief(level, seed):
    puz = make(level, seed)
    n, rooms, _plain, max_clues, _direct = plaatsdelict.LEVELS[level]
    assert puz["n"] == n == len(puz["solution"]) == len(puz["suspects"])
    assert len(puz["room_names"]) == rooms and len(puz["clues"]) <= max_clues
    assert plaatsdelict.solve(puz, limit=3) == [puz["solution"]]
    assert sorted(r for r, _ in puz["solution"]) == list(range(n))
    assert sorted(c for _, c in puz["solution"]) == list(range(n))
    r, c, _key = puz["objects"][puz["loot"]]
    inside = [i for i, (sr, sc) in enumerate(puz["solution"])
              if puz["rooms"][sr][sc] == puz["rooms"][r][c]]
    assert inside == [puz["thief"]]
    taken = {(orow, ocol) for orow, ocol, _ in puz["objects"]}
    assert not taken & {tuple(cell) for cell in puz["solution"]}


def test_scenarios_are_complete():
    for sc in plaatsdelict.SCENARIOS:
        text = json.dumps(sc, ensure_ascii=False)
        assert "­" not in text
    puz = make(3, 1)
    letters = [letter for letter, _role in puz["suspects"]]
    assert len(set(letters)) == len(letters)
    for clue in puz["clues"]:
        line = plaatsdelict.clue_text(puz, clue)
        assert line[0].isupper() and line.endswith(".")


def test_verify_rejects_swapped_suspects():
    puz = make(2, 1)
    sol = puz["solution"]
    sol[0], sol[1] = sol[1], sol[0]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_verify_rejects_missing_clue():
    puz = make(2, 2)
    puz["clues"] = puz["clues"][:1]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_verify_rejects_wrong_thief():
    puz = make(1, 3)
    puz["thief"] = (puz["thief"] + 1) % puz["n"]
    with pytest.raises(AssertionError):
        GAME.verify(puz)


def test_layout_on_paper_pro_move():
    """Generate, verify and draw every part on the 9:16 Move page."""
    from reportlab.pdfgen import canvas

    from mind import theme

    theme.register_fonts()
    try:
        theme.set_device("move")
        assert theme.COMPACT
        c = canvas.Canvas(io.BytesIO(), pagesize=(theme.W, theme.H))
        for seed in range(3):
            for level in (1, 2, 3):
                puz = GAME.generate(random.Random(f"move-{seed}"), level)
                GAME.verify(puz)
                assert puz["n"] == plaatsdelict.LEVELS_COMPACT[level][0]
                for solved in (False, True):
                    GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
                    c.showPage()
                assert GAME.last_cell >= 18
    finally:
        theme.set_device("paperpro")
