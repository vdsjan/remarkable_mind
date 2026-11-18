"""The book as an "app": geometry, navigation links and the training plan."""
import json

import pymupdf
import pytest

from mind import book, games
from mind.theme import CATEGORY_ORDER, H, W


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("book") / "mini.pdf"
    stats = book.build(seed=7, out=out, jobs=1, cache=out.parent / "cache",
                       log=lambda *a: None, only={"sudoku", "doolhof"})
    doc = pymupdf.open(str(out))
    index = json.loads(out.with_suffix(".json").read_text())["pages"]
    return stats, doc, index


def targets(doc, page_no):
    return {l["page"] for l in doc[page_no].get_links()}


def test_page_fills_the_paper_pro_screen(built):
    _, doc, _ = built
    assert W / H == pytest.approx(1620 / 2160)
    for page in doc:
        assert (page.rect.width, page.rect.height) == pytest.approx((W, H))


def test_page_count(built):
    stats, doc, index = built
    # cover, home, howto, 2x training, score, solutions intro, colophon = 8
    # per game: hub + 25 puzzles + 25 solutions
    assert doc.page_count == 8 + 2 * (1 + 25 + 25) == stats["pages"]
    assert len(index) == doc.page_count


def test_every_link_points_inside_the_book(built):
    stats, doc, _ = built
    n = 0
    for page in doc:
        for l in page.get_links():
            assert l["kind"] == pymupdf.LINK_GOTO      # explicit page links only
            assert 0 <= l["page"] < doc.page_count
            n += 1
    assert n == stats["links"] > 500


def test_home_reaches_every_game_and_tool(built):
    _, doc, index = built
    t = targets(doc, index["home"])
    for key in ("hub:sudoku", "hub:doolhof", "training1", "score", "howto"):
        assert index[key] in t


def test_puzzle_and_solution_link_to_each_other(built):
    _, doc, index = built
    for key in ("sudoku", "doolhof"):
        for n in range(1, 26):
            p, s = index[f"p:{key}:{n}"], index[f"s:{key}:{n}"]
            assert s in targets(doc, p), f"{key} {n}: no solution button"
            assert p in targets(doc, s), f"{key} {n}: no way back"
            assert index["home"] in targets(doc, p)
            assert index[f"hub:{key}"] in targets(doc, p)
        hub = targets(doc, index[f"hub:{key}"])
        assert all(index[f"p:{key}:{n}"] in hub for n in range(1, 26))


def test_solutions_come_after_all_puzzles(built):
    _, _, index = built
    last_puzzle = max(v for k, v in index.items() if k.startswith("p:"))
    first_solution = min(v for k, v in index.items() if k.startswith("s:"))
    assert last_puzzle < index["solutions"] < first_solution


def test_outline_lists_the_games(built):
    _, doc, _ = built
    titles = [t[1] for t in doc.get_toc()]
    assert {"Startscherm", "Sudoku", "Doolhof", "Oplossingen"} <= set(titles)
    # one game per category: 25 puzzles allow a 25-day plan without repeats
    assert "25 dagen hersengym" in titles


def test_training_plan_is_balanced_and_gets_harder():
    all_games = games.all_games()
    plan = book.training_plan(all_games)
    assert len(plan) == book.DAYS
    seen = set()
    for row in plan:
        assert [g.category for g, _ in row] == CATEGORY_ORDER
        for g, idx in row:
            assert 0 <= idx < sum(g.counts)
            assert (g.key, idx) not in seen, "a puzzle is planned twice"
            seen.add((g.key, idx))
    assert {g.key for row in plan for g, _ in row} == {g.key for g in all_games}

    def mean_level(rows):
        lv = [book.level_of(g, i) for row in rows for g, i in row]
        return sum(lv) / len(lv)

    assert mean_level(plan[:10]) < mean_level(plan[10:20]) < mean_level(plan[20:])


def test_sixteen_games_four_per_category():
    all_games = games.all_games()
    assert len(all_games) == 16
    assert sum(sum(g.counts) for g in all_games) == 400
    for cat in CATEGORY_ORDER:
        assert sum(g.category == cat for g in all_games) == 4
