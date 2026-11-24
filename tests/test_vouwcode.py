"""Tests for Vouwcode: two independent ways to compute the holes must agree."""
import io
import json
import random

import pytest

from mind import theme
from mind.games.vouwcode import (GAME, N_FOLDS, SIZE, fold_rect, holes_by_reflection,
                                 possible_folds, simulate)

CASES = [(level, seed) for level in (1, 2, 3) for seed in (1, 2, 3)]


def make(level, seed):
    return GAME.generate(random.Random(f"vouwcode-{level}-{seed}"), level)


@pytest.mark.parametrize("level,seed", CASES)
def test_generate_and_verify(level, seed):
    puz = make(level, seed)
    GAME.verify(puz)
    assert puz["n"] == SIZE[level] and len(puz["folds"]) == N_FOLDS[level]
    assert 1 <= len(puz["punches"]) <= 2 and len(puz["holes"]) > len(puz["punches"])


@pytest.mark.parametrize("level,seed", CASES)
def test_deterministic_and_json_safe(level, seed):
    a, b = make(level, seed), make(level, seed)
    assert a == b
    assert json.loads(json.dumps(a)) == a


def test_metadata():
    assert GAME.key == "vouwcode" and GAME.category == "ruimte" and GAME.example is False
    assert GAME.name and GAME.tagline and 2 <= len(GAME.rules) <= 4
    assert 1 <= len(GAME.tips) <= 2 and sum(GAME.counts) == 25


def test_known_folds():
    # left half over right half, punch next to the crease: mirror image across x = 2
    assert holes_by_reflection(4, [["v", 2, "l"]], [(2, 0)]) == [(1, 0), (2, 0)]
    # then top over bottom: four holes around the centre
    folds = [["v", 2, "l"], ["h", 2, "t"]]
    assert holes_by_reflection(4, folds, [(2, 2)]) == [(1, 1), (1, 2), (2, 1), (2, 2)]
    # a narrow strip folded over: only cells under the strip get a second hole
    folds = [["v", 2, "l"]]                       # 6 wide: columns 0-1 land on 3-2
    assert holes_by_reflection(6, folds, [(2, 0)]) == [(1, 0), (2, 0)]
    assert holes_by_reflection(6, folds, [(5, 0)]) == [(5, 0)]
    # the folded part may never be larger than the part it lands on
    assert fold_rect((0, 6, 0, 6), ["v", 4, "l"]) is None
    assert fold_rect((0, 6, 0, 6), ["v", 4, "r"]) == ((0, 4, 0, 6), (2, 4, 0, 6))


def test_layer_simulation_matches_reflection_on_random_folds():
    rng = random.Random("vouwcode-property")
    for _ in range(400):
        n = rng.choice((4, 6, 8))
        folds, rect = [], (0, n, 0, n)
        for _ in range(rng.randint(1, 4)):
            options = possible_folds(rect)
            if not options:
                break
            folds.append(rng.choice(options))
            rect = fold_rect(rect, folds[-1])[0]
        states = simulate(n, folds)
        final = states[-1]
        assert final["rect"] == rect
        # no paper is lost: every sheet cell is in exactly one stack
        cells = [cell for stack in final["layers"].values() for cell in stack]
        assert sorted(cells) == [(x, y) for x in range(n) for y in range(n)]
        for cell, stack in final["layers"].items():
            assert sorted(stack) == holes_by_reflection(n, folds, [cell])


def test_verify_rejects_tampering():
    puz = make(2, 1)
    bad = json.loads(json.dumps(puz))
    bad["holes"] = bad["holes"][:-1]              # a missing hole
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    bad["folds"][0][2] = {"l": "r", "r": "l", "t": "b", "b": "t"}[bad["folds"][0][2]]
    with pytest.raises(AssertionError):
        GAME.verify(bad)
    bad = json.loads(json.dumps(puz))
    bad["punches"] = [[9, 9]]                     # outside the packet
    with pytest.raises(AssertionError):
        GAME.verify(bad)


def test_level_three_has_an_uneven_fold():
    for seed in range(10):
        puz = make(3, seed)
        rect, uneven = (0, puz["n"], 0, puz["n"]), False
        for axis, at, _ in puz["folds"]:
            lo, hi = (rect[0], rect[1]) if axis == "v" else (rect[2], rect[3])
            uneven |= 2 * at != lo + hi
            rect = fold_rect(rect, [axis, at, _])[0]
        assert uneven and 5 <= len(puz["holes"]) <= 14


def test_plenty_of_different_puzzles():
    for level in (1, 2, 3):
        seen = {json.dumps(make(level, seed)) for seed in range(60)}
        assert len(seen) >= 30


def draw_pages(puz):
    from reportlab.pdfgen import canvas
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
            if device == "move" and level == 3:   # no one-cell strips on the small page
                rect = (0, puz["n"], 0, puz["n"])
                for fold in puz["folds"]:
                    new = fold_rect(rect, fold)[0]
                    part = (rect[1] - rect[0]) - (new[1] - new[0]) or \
                        (rect[3] - rect[2]) - (new[3] - new[2])
                    assert part >= 2
                    rect = new
    finally:
        theme.set_device("paperpro")
