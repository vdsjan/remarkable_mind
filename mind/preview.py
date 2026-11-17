"""Developer preview: render one game's puzzle and solution pages to PNG.

    python -m mind.preview sudoku [--level 2] [--seed 1] [--out DIR]

Writes <out>/<key>-L<level>-puzzle.png, -solution.png (and -part2.png for
two-page games) at the exact reMarkable Paper Pro resolution (1620 x 2160).
"""
import argparse
import random
import sys
import time
from pathlib import Path

import pymupdf as fitz
from reportlab.pdfgen import canvas

from . import games
from .pages import puzzle_page, solution_page
from .theme import W, H, register_fonts


def render(key, level, seed, out):
    register_fonts()
    game = games.get(key)
    t0 = time.time()
    puz = game.generate(random.Random(f"{key}-{level}-{seed}"), level)
    dt = time.time() - t0
    game.verify(puz)
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / f"{key}-L{level}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    names = []
    for part in range(game.parts):
        puzzle_page(c, game, puz, index=1, level=level, total=25, part=part)
        c.showPage()
        names.append("puzzle" if part == 0 else f"part{part + 1}")
    solution_page(c, game, puz, index=1, level=level, total=25)
    c.showPage()
    names.append("solution")
    c.save()
    doc = fitz.open(str(pdf))
    paths = []
    for page, name in zip(doc, names):
        pix = page.get_pixmap(matrix=fitz.Matrix(1620 / W, 2160 / H))
        p = out / f"{key}-L{level}-{name}.png"
        pix.save(str(p))
        paths.append(p)
    print(f"{key} L{level}: generated in {dt:.2f}s, verified OK")
    for p in paths:
        print("  ", p)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--level", type=int, default=0, help="1-3, 0 = all")
    ap.add_argument("--seed", default="1")
    ap.add_argument("--out", default="build/preview")
    a = ap.parse_args(argv)
    for level in ([a.level] if a.level else [1, 2, 3]):
        render(a.key, level, a.seed, Path(a.out))


if __name__ == "__main__":
    sys.exit(main())
