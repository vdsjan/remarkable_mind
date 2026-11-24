"""Vouwcode - fold a sheet, punch it, and predict the holes after unfolding.

The sheet is an n x n guide grid; cell (x, y) has x counted from the left and
y from the top. A fold is ``[axis, line, side]``:

* axis "v": the crease is the vertical grid line x = line; side "l" lays the
  part left of the crease over the right part, side "r" the other way round;
* axis "h": the crease is the horizontal grid line y = line; side "t" lays the
  top part over the bottom part, side "b" the other way round.

The folded part is never larger than the part it lands on, so the packet stays
a rectangle that lies where it lies on the original sheet. Punches go through
every layer of one packet cell.

Two independent methods compute the holes: ``simulate`` keeps a stack of sheet
cells per packet cell (used by the generator), ``unfold`` mirrors the punch
points back through the creases (used by ``verify``).
"""
from .. import theme
from ..draw import circle, line, polyline, text, text_mid
from ..theme import GREY, INK, LIGHT, MID, PEN, RED, WHITE
from .base import Game

SIZE = {1: 4, 2: 4, 3: 6}
N_FOLDS = {1: 1, 2: 2, 3: 3}


# --- folding ---------------------------------------------------------------------
def fold_rect(rect, fold):
    """Rectangle (x0, x1, y0, y1) of the packet after a fold, plus the strip
    the folded part lands on. Returns None when the fold is not possible."""
    x0, x1, y0, y1 = rect
    axis, at, side = fold
    if axis == "v":
        if not x0 < at < x1:
            return None
        fw = at - x0 if side == "l" else x1 - at
        if fw > (x1 - x0) - fw or side not in "lr":
            return None
        if side == "l":
            return (at, x1, y0, y1), (at, at + fw, y0, y1)
        return (x0, at, y0, y1), (at - fw, at, y0, y1)
    if axis == "h":
        if not y0 < at < y1:
            return None
        fw = at - y0 if side == "t" else y1 - at
        if fw > (y1 - y0) - fw or side not in "tb":
            return None
        if side == "t":
            return (x0, x1, at, y1), (x0, x1, at, at + fw)
        return (x0, x1, y0, at), (x0, x1, at - fw, at)
    return None


def simulate(n, folds):
    """Fold step by step. Returns a list of states, one before each fold and
    one after the last: {"rect", "flap", "layers"} where layers maps a packet
    cell to the sheet cells stacked on it."""
    rect = (0, n, 0, n)
    layers = {(x, y): [(x, y)] for x in range(n) for y in range(n)}
    states = [{"rect": rect, "flap": None, "layers": layers}]
    for fold in folds:
        res = fold_rect(rect, fold)
        assert res, f"impossible fold {fold}"
        new_rect, flap = res
        axis, at, _ = fold
        nx0, nx1, ny0, ny1 = new_rect
        new = {}
        for (x, y), stack in layers.items():
            if nx0 <= x < nx1 and ny0 <= y < ny1:
                new[(x, y)] = list(stack)                      # stays below
        for (x, y), stack in layers.items():
            if not (nx0 <= x < nx1 and ny0 <= y < ny1):
                tx, ty = (2 * at - 1 - x, y) if axis == "v" else (x, 2 * at - 1 - y)
                new[(tx, ty)].extend(reversed(stack))           # flipped on top
        rect, layers = new_rect, new
        states.append({"rect": rect, "flap": flap, "layers": layers})
    return states


def unfold(n, folds, rects):
    """Mirror shapes on the folded packet back through all creases.

    rects are (x0, x1, y0, y1) in sheet units; a point or a crease is a
    rectangle without width. Returns everything those shapes become on the
    open sheet. Uses only the outlines of the packets, never the layers."""
    before = [(0, n, 0, n)]
    for fold in folds:
        before.append(fold_rect(before[-1], fold)[0])
    shapes = list(rects)
    for fold, rect in zip(reversed(folds), reversed(before[:-1])):
        axis, at, _ = fold
        _, flap = fold_rect(rect, fold)
        for a0, a1, b0, b1 in list(shapes):
            if axis == "v":
                lo, hi = max(a0, flap[0]), min(a1, flap[1])
                if lo <= hi and not (lo == hi and a0 != a1):
                    shapes.append((2 * at - hi, 2 * at - lo, b0, b1))
            else:
                lo, hi = max(b0, flap[2]), min(b1, flap[3])
                if lo <= hi and not (lo == hi and b0 != b1):
                    shapes.append((a0, a1, 2 * at - hi, 2 * at - lo))
    return shapes


def holes_by_reflection(n, folds, punches):
    pts = unfold(n, folds, [(x + 0.5, x + 0.5, y + 0.5, y + 0.5) for x, y in punches])
    return sorted({(int(a), int(b)) for a, _, b, _ in pts})


def possible_folds(rect, only_half=False, min_part=1):
    """Folds that can be made on a packet. min_part is the smallest width (in
    cells) of the part that folds over."""
    x0, x1, y0, y1 = rect
    out = []
    for axis, lo, hi, sides in (("v", x0, x1, "lr"), ("h", y0, y1, "tb")):
        for at in range(lo + 1, hi):
            for side in sides:
                fold = [axis, at, side]
                part = at - lo if side in "lt" else hi - at
                if fold_rect(rect, fold) and part >= min_part \
                        and (not only_half or 2 * at == lo + hi):
                    out.append(fold)
    return out


class Vouwcode(Game):
    key = "vouwcode"
    name = "Vouwcode"
    category = "ruimte"
    tagline = "Vouw, prik en ontvouw in gedachten: waar zitten de gaatjes?"
    rules = [
        "Het blad wordt gevouwen zoals de genummerde stappen tonen: de pijl "
        "wijst aan welk deel over de stippellijn op de rest wordt gelegd.",
        "In het gevouwen pakje worden gaatjes geprikt, dwars door alle lagen.",
        "Teken op het lege blad waar alle gaatjes zitten wanneer het blad weer open ligt.",
    ]
    tips = [
        "Vouw in gedachten terug, één stap per keer: elk gaatje krijgt een "
        "spiegelbeeld aan de andere kant van de vouwlijn.",
        "Let op waar het pakje ligt: het gestippelde kader toont het hele blad.",
    ]
    counts = (9, 8, 8)
    example = False

    # -- generation -------------------------------------------------------------
    def generate(self, rng, level):
        n = SIZE[level]
        for _ in range(500):
            folds, rect = [], (0, n, 0, n)
            for i in range(N_FOLDS[level]):
                # on the small Move page a one-cell strip is too fine to read
                options = possible_folds(rect, only_half=level < 3,
                                         min_part=2 if level == 3 and theme.COMPACT else 1)
                if level == 2 and i == 1 and rng.random() < 0.7:      # mostly a quarter
                    options = [f for f in options if f[0] != folds[0][0]] or options
                if not options:
                    break
                fold = rng.choice(options)
                folds.append(fold)
                rect = fold_rect(rect, fold)[0]
            if len(folds) < N_FOLDS[level]:
                continue
            x0, x1, y0, y1 = rect
            cells = [(x, y) for x in range(x0, x1) for y in range(y0, y1)]
            k = rng.choice((1, 2, 2)) if level < 3 else 2
            if len(cells) < k + 1:
                continue
            punches = sorted(rng.sample(cells, k))
            final = simulate(n, folds)[-1]["layers"]
            holes = sorted({cell for p in punches for cell in final[p]})
            deepest = max(len(final[p]) for p in punches)
            if level == 3:
                uneven = any(2 * f[1] != sum(r[:2] if f[0] == "v" else r[2:])
                             for f, r in zip(folds, self._rects(n, folds)))
                if not uneven or deepest < 3 or not 5 <= len(holes) <= 14:
                    continue
            elif len(holes) < 2 or deepest < 2 or len(holes) > n * n // 2:
                continue
            return {"n": n, "folds": folds, "punches": [list(p) for p in punches],
                    "holes": [list(h) for h in holes]}
        raise AssertionError("could not generate a Vouwcode puzzle")

    @staticmethod
    def _rects(n, folds):
        rects = [(0, n, 0, n)]
        for fold in folds:
            rects.append(fold_rect(rects[-1], fold)[0])
        return rects

    def verify(self, puz):
        n, folds = puz["n"], puz["folds"]
        assert n in (4, 6) and 1 <= len(folds) <= 3
        rect = (0, n, 0, n)
        for fold in folds:
            res = fold_rect(rect, fold)
            assert res, f"impossible fold {fold}"
            rect = res[0]
        punches = [tuple(p) for p in puz["punches"]]
        assert 1 <= len(punches) == len(set(punches))
        assert all(rect[0] <= x < rect[1] and rect[2] <= y < rect[3] for x, y in punches), \
            "punches must hit the folded packet"
        holes = [tuple(h) for h in puz["holes"]]
        assert len(holes) == len(set(holes)) >= 2
        assert all(0 <= x < n and 0 <= y < n for x, y in holes)
        assert sorted(holes) == holes_by_reflection(n, folds, punches), \
            "holes do not match the folds"
        assert set(punches) <= set(holes)

    def instruction(self, puz, part=0):
        k = len(puz["folds"])
        times = "één keer" if k == 1 else f"{k} keer"
        return (f"Het blad wordt {times} gevouwen en daarna geprikt. "
                "Teken alle gaatjes op het open blad.")

    # -- drawing ------------------------------------------------------------------
    @staticmethod
    def _rect_xy(ox, oy, u, n, rect):
        """Page box (x, y, w, h) of a sheet rectangle; (ox, oy) is the sheet's
        bottom-left corner and u the size of one cell."""
        x0, x1, y0, y1 = rect
        return ox + x0 * u, oy + (n - y1) * u, (x1 - x0) * u, (y1 - y0) * u

    def _sheet(self, c, ox, oy, u, n, rect, layers=1, flap=None, lw=1.2):
        d = n * u
        if rect != (0, n, 0, n):                         # where the whole sheet lies
            c.saveState()
            c.setStrokeColor(MID)
            c.setLineWidth(0.7)
            c.setDash(1.5, 2.2)
            c.rect(ox, oy, d, d, stroke=1, fill=0)
            c.restoreState()
        x, y, w, h = self._rect_xy(ox, oy, u, n, rect)
        c.saveState()
        if layers > 1:                                   # the edge of the layers below
            off = min(2.4, u * 0.16)
            c.setStrokeColor(GREY)
            c.setFillColor(LIGHT)
            c.setLineWidth(0.7)
            c.rect(x + off, y - off, w, h, stroke=1, fill=1)
        c.setFillColor(WHITE)
        c.setStrokeColor(INK)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, stroke=0, fill=1)
        if flap and flap != rect:                        # the part that was just laid on top
            fx, fy, fw, fh = self._rect_xy(ox, oy, u, n, flap)
            c.setFillColor(LIGHT)
            c.rect(fx, fy, fw, fh, stroke=0, fill=1)
        c.setStrokeColor(MID)
        c.setLineWidth(0.45)
        x0, x1, y0, y1 = rect
        for i in range(x0 + 1, x1):
            c.line(ox + i * u, y, ox + i * u, y + h)
        for j in range(y0 + 1, y1):
            c.line(x, oy + (n - j) * u, x + w, oy + (n - j) * u)
        if flap and flap != rect:
            fx, fy, fw, fh = self._rect_xy(ox, oy, u, n, flap)
            c.setStrokeColor(INK)
            c.setLineWidth(0.8)
            c.rect(fx, fy, fw, fh, stroke=1, fill=0)
        c.setStrokeColor(INK)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, stroke=1, fill=0)
        c.restoreState()

    def _fold_marks(self, c, ox, oy, u, n, rect, fold):
        """Dashed crease and an arrow from the folding part to where it lands."""
        axis, at, side = fold
        x, y, w, h = self._rect_xy(ox, oy, u, n, rect)
        new_rect, flap = fold_rect(rect, fold)
        fx, fy, fw, fh = self._rect_xy(ox, oy, u, n, flap)
        over = 4.0
        c.saveState()
        c.setStrokeColor(INK)
        c.setLineWidth(1.1)
        c.setDash(3, 2.2)
        if axis == "v":
            cx = ox + at * u
            c.line(cx, y - over, cx, y + h + over)
            ex, ey = fx + fw / 2, fy + fh / 2            # landing point
            sx, sy = 2 * cx - ex, ey                     # where that paper is now
            bx, by = 0.0, min(h * 0.42, abs(ex - sx) * 0.75 + 4)
        else:
            cy = oy + (n - at) * u
            c.line(x - over, cy, x + w + over, cy)
            ex, ey = fx + fw / 2, fy + fh / 2
            sx, sy = ex, 2 * cy - ey
            bx, by = min(w * 0.42, abs(ey - sy) * 0.75 + 4), 0.0
        c.restoreState()
        c.saveState()
        c.setStrokeColor(RED)
        c.setFillColor(RED)
        c.setLineWidth(1.5)
        c.setLineCap(1)
        x1, y1, x2, y2 = sx + bx, sy + by, ex + bx, ey + by
        c.bezier(sx, sy, x1, y1, x2, y2, ex, ey)
        # arrow head along the end tangent
        dx, dy = ex - x2, ey - y2
        norm = (dx * dx + dy * dy) ** 0.5 or 1.0
        dx, dy = dx / norm, dy / norm
        hsize = max(4.2, min(7.0, u * 0.42))
        p = c.beginPath()
        p.moveTo(ex + dx * 1.2, ey + dy * 1.2)
        p.lineTo(ex - dx * hsize - dy * hsize * 0.55, ey - dy * hsize + dx * hsize * 0.55)
        p.lineTo(ex - dx * hsize + dy * hsize * 0.55, ey - dy * hsize - dx * hsize * 0.55)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.circle(sx, sy, 1.6, stroke=0, fill=1)
        c.restoreState()

    def draw(self, c, box, puz, solved=False, part=0):
        x, y, w, h = box
        n, folds = puz["n"], puz["folds"]
        states = simulate(n, folds)
        count = len(states)                              # one diagram per fold + the punch
        compact = theme.COMPACT
        gap = 10.0 if compact else 16.0
        label_h = 17.0
        d = min((w - (count - 1) * gap) / count, 96.0 if compact else 132.0, h * 0.3)
        u = d / n
        row_w = count * d + (count - 1) * gap
        ox0 = x + (w - row_w) / 2
        oy = y + h - label_h - d
        for i, st in enumerate(states):
            ox = ox0 + i * (d + gap)
            last = i == count - 1
            circle(c, ox + 6.5, oy + d + 9.5, 6.5, fill=INK, stroke=None)
            text_mid(c, ox + 6.5, oy + d + 9.5, str(i + 1), "SansB", 8.5, WHITE)
            text(c, ox + 17, oy + d + 6.6, "PRIK" if last else "VOUW", "SansB", 7.6, GREY)
            deepest = max(len(s) for s in st["layers"].values())
            self._sheet(c, ox, oy, u, n, st["rect"], layers=deepest, flap=st["flap"])
            if last:
                for px, py in puz["punches"]:
                    circle(c, ox + (px + 0.5) * u, oy + (n - py - 0.5) * u,
                           max(2.3, u * 0.27), fill=INK, stroke=None)
            else:
                self._fold_marks(c, ox, oy, u, n, st["rect"], folds[i])
            if not last:                                 # a small "then" chevron
                mx, my = ox + d + gap / 2, oy + d / 2
                polyline(c, [(mx - 2.2, my + 4.5), (mx + 2.2, my), (mx - 2.2, my - 4.5)],
                         1.3, GREY)

        # the answer sheet
        top = oy - (12.0 if compact else 18.0)
        side = min(w, top - 13.0 - y, 300.0)
        ax = x + (w - side) / 2
        ay = top - 13.0 - side
        text(c, ax, top - 8.5, "ZO LIGGEN DE GAATJES" if solved else "TEKEN HIER ALLE GAATJES",
             "SansB", 7.8, GREY)
        cell = side / n
        self._sheet(c, ax, ay, cell, n, (0, n, 0, n), lw=1.8)
        if solved:
            creases = []
            rect = (0, n, 0, n)
            for i, fold in enumerate(folds):
                x0, x1, y0, y1 = rect
                seg = (fold[1], fold[1], y0, y1) if fold[0] == "v" else (x0, x1, fold[1], fold[1])
                creases += unfold(n, folds[:i], [seg])
                rect = fold_rect(rect, fold)[0]
            c.saveState()
            c.setStrokeColor(GREY)
            c.setLineWidth(0.9)
            c.setDash(3.5, 2.6)
            for a0, a1, b0, b1 in set(creases):
                if a0 == a1 in (0, n) or b0 == b1 in (0, n):
                    continue                             # the edge of the sheet is no crease
                c.line(ax + a0 * cell, ay + (n - b0) * cell, ax + a1 * cell, ay + (n - b1) * cell)
            c.restoreState()
            for hx, hy in puz["holes"]:
                circle(c, ax + (hx + 0.5) * cell, ay + (n - hy - 0.5) * cell, cell * 0.25,
                       fill=PEN, stroke=None)

    def icon(self, c, cx, cy, s, color):
        h = s / 2
        polyline(c, [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)],
                 lw=1.4, color=color, close=True)
        line(c, cx, cy - h, cx, cy + h, 1.0, color, dash=(2, 2))
        for dx, dy in ((-0.5, 0.42), (0.5, 0.42), (-0.5, -0.38), (0.5, -0.38)):
            circle(c, cx + dx * h, cy + dy * h, s * 0.085, fill=color, stroke=None)


GAME = Vouwcode()
