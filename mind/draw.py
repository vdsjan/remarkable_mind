"""Small drawing toolkit shared by the book layout and every game.

All coordinates are reportlab points with the origin at the bottom-left.
A *box* is always ``(x, y, w, h)`` with ``y`` the bottom edge.
"""
import math

from reportlab.pdfbase.pdfmetrics import stringWidth

from . import theme
from .theme import INK, WHITE, PEN, MID, GREY


# --- text -------------------------------------------------------------------
def text(c, x, y, s, font="Sans", size=10, color=INK, align="l"):
    """Draw one line of text. align: 'l', 'c' or 'r' relative to x."""
    c.setFont(font, size)
    c.setFillColor(color)
    s = theme.localize(str(s))
    if align == "c":
        c.drawCentredString(x, y, s)
    elif align == "r":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)


def text_mid(c, cx, cy, s, font="SansS", size=12, color=INK):
    """Draw text centred horizontally *and* vertically on (cx, cy)."""
    k = 0.30 if font.startswith("Hand") else 0.355
    text(c, cx, cy - size * k, s, font, size, color, "c")


def wrap(s, font, size, width):
    """Greedy word wrap; returns a list of lines."""
    lines, cur = [], ""
    for word in theme.localize(str(s)).split():
        trial = (cur + " " + word).strip()
        if stringWidth(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def paragraph(c, x, y_top, width, s, font="Sans", size=10, leading=None,
              color=INK, align="l"):
    """Draw wrapped text starting below y_top; returns the y under the block."""
    leading = leading or size * 1.38
    y = y_top - size
    for line in wrap(s, font, size, width):
        ax = x if align == "l" else (x + width / 2 if align == "c" else x + width)
        text(c, ax, y, line, font, size, color, align)
        y -= leading
    return y + leading - size * 0.35


def fit_size(s, font, width, size, min_size=6):
    """Largest font size <= size at which s fits in width."""
    while size > min_size and stringWidth(str(s), font, size) > width:
        size -= 0.5
    return size


# --- shapes -----------------------------------------------------------------
def rrect(c, x, y, w, h, r=6, fill=None, stroke=INK, lw=1.0):
    c.saveState()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke is not None else 0,
                fill=1 if fill is not None else 0)
    c.restoreState()


def line(c, x1, y1, x2, y2, lw=1.0, color=INK, cap=1, dash=None):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.setLineCap(cap)
    if dash:
        c.setDash(dash)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def polyline(c, pts, lw=1.0, color=INK, close=False, fill=None, join=1):
    c.saveState()
    c.setLineWidth(lw)
    c.setLineJoin(join)
    c.setLineCap(1)
    if color is not None:
        c.setStrokeColor(color)
    if fill is not None:
        c.setFillColor(fill)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    if close:
        p.close()
    c.drawPath(p, stroke=1 if color is not None else 0,
               fill=1 if fill is not None else 0)
    c.restoreState()


def circle(c, cx, cy, r, fill=None, stroke=INK, lw=1.0):
    c.saveState()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.circle(cx, cy, r, stroke=1 if stroke is not None else 0,
             fill=1 if fill is not None else 0)
    c.restoreState()


def star(c, cx, cy, r, fill=INK, stroke=None, lw=0.8):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    polyline(c, pts, lw=lw, color=stroke, close=True, fill=fill)


def stars(c, x, cy, level, r=5.0, color=INK, total=3):
    """Difficulty stars: `level` filled out of `total`, starting at x."""
    for i in range(total):
        filled = i < level
        star(c, x + r + i * (2 * r + 3), cy, r,
             fill=color if filled else None,
             stroke=None if filled else color)
    return x + total * (2 * r + 3)


# --- links ------------------------------------------------------------------
def link(c, box, dest):
    """Make box a tappable internal link to the named destination."""
    x, y, w, h = box
    c.linkRect("", dest, (x, y, x + w, y + h), relative=0, thickness=0)


def button(c, x, y, w, h, label, dest=None, fill=None, fg=INK, stroke=INK,
           font="SansS", size=10.5, r=None, lw=1.2):
    """Rounded button with centred label; tappable when dest is given."""
    r = h / 2 if r is None else r
    rrect(c, x, y, w, h, r, fill=fill, stroke=stroke, lw=lw)
    if label:
        size = fit_size(label, font, w - 10, size)
        text_mid(c, x + w / 2, y + h / 2, label, font, size, fg)
    if dest:
        link(c, (x, y, w, h), dest)


# --- icons (drawn, so they stay razor sharp on e-ink) -------------------------
def icon_home(c, cx, cy, s, color=INK, lw=1.6):
    h = s / 2
    polyline(c, [(cx - h, cy), (cx, cy + h), (cx + h, cy)], lw, color)
    polyline(c, [(cx - h * 0.72, cy - 0.05 * s), (cx - h * 0.72, cy - h),
                 (cx + h * 0.72, cy - h), (cx + h * 0.72, cy - 0.05 * s)], lw, color)


def icon_chevron(c, cx, cy, s, direction=1, color=INK, lw=2.0):
    d = s * 0.28 * direction
    polyline(c, [(cx - d, cy + s * 0.42), (cx + d, cy), (cx - d, cy - s * 0.42)],
             lw, color)


def icon_check(c, cx, cy, s, color=INK, lw=2.0):
    polyline(c, [(cx - s * 0.42, cy), (cx - s * 0.1, cy - s * 0.32),
                 (cx + s * 0.45, cy + s * 0.36)], lw, color)


def icon_bulb(c, cx, cy, s, color=INK, lw=1.5):
    r = s * 0.34
    circle(c, cx, cy + s * 0.12, r, stroke=color, lw=lw)
    line(c, cx - r * 0.5, cy - s * 0.34, cx + r * 0.5, cy - s * 0.34, lw, color)
    line(c, cx - r * 0.35, cy - s * 0.46, cx + r * 0.35, cy - s * 0.46, lw, color)


def icon_calendar(c, cx, cy, s, color=INK, lw=1.5):
    h = s / 2
    rrect(c, cx - h, cy - h, s, s * 0.9, 2, stroke=color, lw=lw)
    line(c, cx - h, cy + h * 0.35, cx + h, cy + h * 0.35, lw, color)
    line(c, cx - h * 0.45, cy + h * 0.75, cx - h * 0.45, cy + h * 1.05, lw, color)
    line(c, cx + h * 0.45, cy + h * 0.75, cx + h * 0.45, cy + h * 1.05, lw, color)


def icon_grid(c, cx, cy, s, color=INK, lw=1.4):
    h = s / 2
    g = s * 0.16
    q = (s - g) / 2
    for dx in (0, q + g):
        for dy in (0, q + g):
            rrect(c, cx - h + dx, cy - h + dy, q, q, 1.5, stroke=color, lw=lw)


def checkbox(c, x, y, s, lw=1.2, color=INK):
    rrect(c, x, y, s, s, 2.5, stroke=color, lw=lw)


# --- grid helper --------------------------------------------------------------
class Grid:
    """Lays out a rows x cols grid centred in a box.

    ``left/top/right/bottom`` reserve extra space *in cell units* around the
    grid for clues. Row 0 is the top row.
    """

    def __init__(self, box, cols, rows, max_cell=46, left=0, top=0, right=0,
                 bottom=0, valign="center"):
        x, y, w, h = box
        self.cols, self.rows = cols, rows
        tw, th = cols + left + right, rows + top + bottom
        self.cell = cell = min(max_cell, w / tw, h / th)
        self.x0 = x + (w - tw * cell) / 2 + left * cell
        if valign == "top":
            self.ytop = y + h - top * cell
        else:
            self.ytop = y + h - (h - th * cell) / 2 - top * cell
        self.w, self.h = cols * cell, rows * cell

    # geometry
    def x(self, col):
        return self.x0 + col * self.cell

    def y(self, row):
        """y of the *top* edge of a row (row may equal rows for the bottom)."""
        return self.ytop - row * self.cell

    def cx(self, col):
        return self.x0 + (col + 0.5) * self.cell

    def cy(self, row):
        return self.ytop - (row + 0.5) * self.cell

    def rect(self, row, col):
        return (self.x(col), self.y(row + 1), self.cell, self.cell)

    # drawing
    def lines(self, c, lw=0.7, color=INK, outer=2.0, block=None, block_lw=1.8):
        """Grid lines; block=(rows, cols) draws heavier lines per block."""
        for i in range(self.cols + 1):
            heavy = block and i % block[1] == 0
            w = outer if i in (0, self.cols) else (block_lw if heavy else lw)
            line(c, self.x(i), self.y(0), self.x(i), self.y(self.rows), w, color, cap=2)
        for j in range(self.rows + 1):
            heavy = block and j % block[0] == 0
            w = outer if j in (0, self.rows) else (block_lw if heavy else lw)
            line(c, self.x(0), self.y(j), self.x(self.cols), self.y(j), w, color, cap=2)

    def fill(self, c, row, col, color, inset=0.0):
        x, y, s, _ = self.rect(row, col)
        c.saveState()
        c.setFillColor(color)
        c.rect(x + inset, y + inset, s - 2 * inset, s - 2 * inset, stroke=0, fill=1)
        c.restoreState()

    def put(self, c, row, col, s, font="SansS", scale=0.56, color=INK):
        text_mid(c, self.cx(col), self.cy(row), s, font, self.cell * scale, color)

    def given(self, c, row, col, s, scale=0.56):
        """A printed clue value."""
        self.put(c, row, col, s, "SansS", scale, INK)

    def answer(self, c, row, col, s, scale=0.72):
        """A solution value, in blue 'handwriting'."""
        self.put(c, row, col, s, "Hand", scale, PEN)


__all__ = [n for n in dir() if not n.startswith("_")]
