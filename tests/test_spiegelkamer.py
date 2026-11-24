"""Tests for Spiegelkamer: validity, uniqueness, determinism, JSON-safety."""
import itertools
import json
import random

import pytest

from mind import theme
from mind.games.spiegelkamer import GAME, LEVELS, solutions, trace

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"spiegelkamer-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = make(level, seed)
    GAME.verify(puz)
    n, k, fixed, gems, pillars = LEVELS[level]
    assert puz["n"] == n and puz["k"] == k == len(puz["mirrors"])
    assert fixed[0] <= len(puz["fixed"]) <= fixed[1]
    assert gems[0] <= len(puz["gems"]) <= gems[1]


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a, b = make(level, seed), make(level, seed)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "spiegelkamer" and GAME.category == "ruimte"
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25
    assert str(make(2, 1)["k"]) in GAME.instruction(make(2, 1))


def brute_force(puz):
    """Every set of k mirrors on free cells, checked by tracing the beam."""
    n, k = puz["n"], puz["k"]
    src, exit_, gems, fixed, pillars = GAME._parts(puz)
    taken = set(gems) | set(fixed) | pillars
    free = [(a, b) for a in range(n) for b in range(n) if (a, b) not in taken]
    found = []
    for cells in itertools.combinations(free, k):
        for kinds in itertools.product("/\\", repeat=k):
            mirrors = dict(fixed)
            mirrors.update(zip(cells, kinds))
            path, outcome = trace(n, src, mirrors, pillars)
            hit = set(path)
            if outcome == ("out",) + exit_ and all(g in hit for g in gems) \
                    and all(cell in hit for cell in cells):
                found.append(sorted([a, b, m] for (a, b), m in zip(cells, kinds)))
    return found


@pytest.mark.parametrize("level,seed", [(1, s) for s in range(6)] + [(2, s) for s in range(3)])
def test_solver_agrees_with_brute_force(level, seed):
    puz = make(level, seed)
    assert brute_force(puz) == [puz["mirrors"]]


def test_verify_rejects_tampering():
    puz = make(2, 1)
    bad = json.loads(json.dumps(puz))
    bad["mirrors"][0][2] = "/" if bad["mirrors"][0][2] == "\\" else "\\"
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    bad["gems"] = bad["gems"][:1]                   # fewer gems: no longer unique or wrong
    bad["k"] -= 1
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    bad["exit"][2] = (bad["exit"][2] + 2) % 4       # exit pointing into the room
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_solver_counts_more_than_one_when_ambiguous():
    # an empty 3x3 room, lamp top-left shining down, exit bottom-right going right:
    # the beam can turn in any of the three rows... but only row 2 leads to the exit
    found = solutions(3, (0, 0, 2), (2, 2, 1), [], {}, set(), 1, limit=5)
    assert found == [[[2, 0, "\\"]]]
    # with two mirrors and an exit on the right of row 0 there are several ways
    found = solutions(4, (0, 0, 1), (3, 3, 2), [], {}, set(), 1, limit=5)
    assert found == [[[0, 3, "\\"]]]
    many = solutions(4, (0, 0, 1), (3, 3, 1), [], {}, set(), 2, limit=9)
    assert len(many) > 1


def test_every_drawn_mirror_matters():
    for level, seed in CASES:
        puz = make(level, seed)
        src, exit_, gems, fixed, pillars = GAME._parts(puz)
        for skip in range(puz["k"]):
            mirrors = dict(fixed)
            mirrors.update({(a, b): m for i, (a, b, m) in enumerate(puz["mirrors"]) if i != skip})
            cells, outcome = trace(puz["n"], src, mirrors, pillars)
            ok = outcome == ("out",) + exit_ and all(g in set(cells) for g in gems)
            assert not ok, "the puzzle can be solved with fewer mirrors"


def draw_pages(puz):
    from reportlab.pdfgen import canvas
    import io
    theme.register_fonts()
    c = canvas.Canvas(io.BytesIO(), pagesize=(theme.W, theme.H))
    for solved in (False, True):
        GAME.draw(c, theme.PLAY_BOX, puz, solved=solved)
        c.showPage()
    c.save()


@pytest.mark.parametrize("device", ["move", "rm2"])
def test_other_devices(device):
    try:
        theme.set_device(device)
        for level, seed in CASES:
            puz = make(level, seed)
            GAME.verify(puz)
            draw_pages(puz)
            x, y, w, h = theme.PLAY_BOX
            # the grid plus one cell of margin for the lamp and the exit fits the box
            assert min(w, h) / (puz["n"] + 1.9) >= (18 if device == "move" else 30)
    finally:
        theme.set_device("paperpro")
