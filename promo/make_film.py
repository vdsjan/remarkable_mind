"""Render the Remarkable Mind promo film (1920x1080, 30 fps, 66 s).

    python promo/make_film.py [--out promo/RemarkableMind-promo.mp4] [--preview]

Ingredients
  * promo/clips/*.mp4   four illustrated clips (ElevenLabs image -> video)
  * promo/audio/*.mp3   Flemish voice-over lines + score (ElevenLabs)
  * promo/art/*.jpg     the risograph artwork (ElevenLabs image)
  * dist/RemarkableMind.pdf  the real app: every screen in the film is an
    actual page of the book, rendered straight from the PDF.

The film is cut to the music: the tense intro ends on a hit at 5.7 s, the
groove starts at 11.4 s and the final chord lands at 62.9 s.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.pdfgen import canvas as rl_canvas  # noqa: E402

from mind import book, games  # noqa: E402
from mind.pages import puzzle_page  # noqa: E402
from mind.theme import H as PH, W as PW, register_fonts  # noqa: E402

PROMO = ROOT / "promo"
FONTS = ROOT / "mind" / "fonts"
FPS, W, H, DUR = 30, 1920, 1080, 66.0
PAPER, INK = (246, 241, 230), (20, 20, 20)
RED, TEAL, MUSTARD, WHITE = (216, 67, 43), (15, 127, 134), (226, 160, 25), (255, 255, 255)

# --- timeline (seconds), cut to the score -------------------------------------
T_RUST, T_HERO, T_SHOW, T_TRAIN, T_WALL, T_END = 5.7, 11.4, 17.4, 46.0, 53.0, 57.0
VO = {"vo1": 0.9, "vo2": 7.3, "vo3": 12.0, "vo4": 18.0, "vo5": 31.0,
      "vo6": 46.5, "vo7": 57.0}
CHORD = 62.9
SCREEN = (630, 840)                     # device screen in film pixels (3:4)
DEV_X, DEV_Y = 1150, 120                # top-left of the screen


# --- small helpers --------------------------------------------------------------
_fonts = {}


def font(name, size):
    key = (name, int(size))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(FONTS / f"{name}.ttf"), int(size))
    return _fonts[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def fade(t, t_in, t_out=None, d=0.35):
    """0..1 visibility: fades in at t_in and (optionally) out before t_out."""
    a = smooth((t - t_in) / d)
    if t_out is not None:
        a *= smooth((t_out - t) / d)
    return a


def put_text(frame, x, y, s, fnt, fill=INK, alpha=1.0, anchor="la"):
    if alpha <= 0.003:
        return
    if alpha >= 0.997:
        ImageDraw.Draw(frame).text((x, y), s, font=fnt, fill=fill, anchor=anchor)
        return
    l, t, r, b = ImageDraw.Draw(frame).textbbox((x, y), s, font=fnt, anchor=anchor)
    l, t, r, b = int(l) - 2, int(t) - 2, int(r) + 3, int(b) + 3
    layer = Image.new("RGBA", (r - l, b - t), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((x - l, y - t), s, font=fnt, fill=fill + (255,),
                               anchor=anchor)
    a = layer.getchannel("A").point(lambda v: int(v * alpha))
    frame.paste(layer.convert("RGB"), (l, t), a)


def pill(frame, cx, cy, s, fnt, bg=INK, fg=WHITE, alpha=1.0, pad=(34, 18)):
    if alpha <= 0.003:
        return
    l, t, r, b = fnt.getbbox(s)
    w, h = r - l + 2 * pad[0], fnt.size + 2 * pad[1]
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg + (255,))
    d.text((w / 2, h / 2), s, font=fnt, fill=fg + (255,), anchor="mm")
    a = layer.getchannel("A").point(lambda v: int(v * alpha))
    frame.paste(layer.convert("RGB"), (int(cx - w / 2), int(cy - h / 2)), a)


def caption(frame, s, alpha):
    """Subtitle bar on the illustrated clips."""
    pill(frame, W / 2, H - 92, s, font("Inter-600", 40), bg=PAPER, fg=INK,
         alpha=alpha, pad=(40, 22))


_grain = None


def paper_bg():
    """Cream paper with a little printed grain."""
    global _grain
    if _grain is None:
        rng = np.random.default_rng(7)
        n = rng.normal(0, 3.2, (H, W, 1))
        _grain = np.clip(np.array(PAPER, dtype=np.float32) + n, 0, 255).astype(np.uint8)
    return Image.fromarray(_grain)


# --- clips ------------------------------------------------------------------------
class Clip:
    """Sequential 30 fps frames of a clip, time-stretched to `seconds`."""

    def __init__(self, name, seconds):
        src = PROMO / "clips" / f"{name}.mp4"
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
             "csv=p=0", str(src)], capture_output=True, text=True).stdout)
        k = seconds / dur
        self.n = int(round(seconds * FPS))
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-i", str(src), "-vf",
             f"setpts=PTS*{k:.5f},framerate=fps={FPS},scale={W}:{H}",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def frame(self):
        raw = self.proc.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            self.last = Image.frombuffer("RGB", (W, H), raw).copy()
        return self.last.copy()

    def close(self):
        self.proc.stdout.close()
        self.proc.wait()


def shift_right(img, dx):
    """Slide an illustration on cream paper to the right, extending the paper."""
    edge = np.asarray(img.crop((0, 0, 8, H))).reshape(-1, 3).mean(0)
    out = Image.new("RGB", (W, H), tuple(int(v) for v in edge))
    mask = Image.new("L", (W, H), 255)
    ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((160, H))
    mask.paste(ramp, (0, 0))
    out.paste(img, (dx, 0), mask)
    return out


# --- pages of the real book -------------------------------------------------------
class Pages:
    def __init__(self, pdf, seed):
        self.doc = pymupdf.open(str(pdf))
        self.index = json.loads(Path(pdf).with_suffix(".json").read_text())["pages"]
        self.cache = {}
        self.seed = seed
        self.puzzles = book.build_puzzles(seed, ROOT / "build" / "cache",
                                          log=lambda *a: None,
                                          all_games=games.all_games(strict=False))

    def page(self, key):
        if key not in self.cache:
            pg = self.doc[self.index[key]]
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(SCREEN[0] / PW, SCREEN[1] / PH))
            self.cache[key] = Image.frombytes("RGB", (pix.width, pix.height),
                                              pix.samples).resize(SCREEN)
        return self.cache[key]

    def link_center(self, key, target):
        """Centre (in screen pixels) of the button on page `key` that leads to
        page `target` - used to place the tap animation on the real button."""
        pg = self.doc[self.index[key]]
        best = None
        for l in pg.get_links():
            if l.get("page") == self.index[target]:
                r = l["from"]
                if best is None or r.get_area() < best.get_area():
                    best = r
        s = SCREEN[0] / PW
        return ((best.x0 + best.x1) / 2 * s, (best.y0 + best.y1) / 2 * s)

    def solved(self, game_key, n):
        """The puzzle page with the answer written on it (as if by pen)."""
        key = f"solved:{game_key}:{n}"
        if key not in self.cache:
            register_fonts()
            game = games.get(game_key)
            puz = self.puzzles[game_key][n - 1]
            tmp = ROOT / "build" / "film-solved.pdf"
            tmp.parent.mkdir(exist_ok=True)
            c = rl_canvas.Canvas(str(tmp), pagesize=(PW, PH))

            class Solved:                       # same page, solution drawn in
                def __getattr__(self, name):
                    return getattr(game, name)

                def draw(self, c, box, puz, solved=False, part=0):
                    game.draw(c, box, puz, solved=True, part=part)

            puzzle_page(c, Solved(), puz, n, book.level_of(game, n - 1),
                        len(self.puzzles[game_key]), part=game.parts - 1)
            c.showPage()
            c.save()
            pix = pymupdf.open(str(tmp))[0].get_pixmap(
                matrix=pymupdf.Matrix(SCREEN[0] / PW, SCREEN[1] / PH))
            self.cache[key] = Image.frombytes("RGB", (pix.width, pix.height),
                                              pix.samples).resize(SCREEN)
        return self.cache[key]


def wipe(base, top, p, soft=60):
    """Reveal `top` over `base` from the top edge downwards, p in 0..1."""
    if p <= 0:
        return base
    if p >= 1:
        return top
    w, h = base.size
    y = int(-soft + p * (h + soft))
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    if y > 0:
        d.rectangle((0, 0, w, y), fill=255)
    grad = Image.linear_gradient("L").rotate(180).resize((w, soft))
    mask.paste(grad, (0, y))
    return Image.composite(top, base, mask)


_shadow = None


def device(frame, screen, dy=0):
    """Draw the paper tablet with `screen` (630x840) on the frame."""
    global _shadow
    bz = 30
    x0, y0 = DEV_X - bz, DEV_Y - bz + int(dy)
    w, h = SCREEN[0] + 2 * bz, SCREEN[1] + 2 * bz
    if _shadow is None:
        sh = Image.new("L", (w + 240, h + 240), 0)
        ImageDraw.Draw(sh).rounded_rectangle((120, 150, w + 120, h + 150), 44, fill=110)
        _shadow = sh.filter(ImageFilter.GaussianBlur(46))
    frame.paste((60, 48, 30), (x0 - 120, y0 - 120), _shadow)
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 40, fill=(34, 34, 36))
    d.rounded_rectangle((x0 + 3, y0 + 3, x0 + w - 3, y0 + h - 3), 38, outline=(70, 70, 74), width=2)
    frame.paste(screen, (DEV_X, DEV_Y + int(dy)))


def tap(frame, sx, sy, p):
    """Finger-tap ripple at screen position (sx, sy); p runs 0..1."""
    if not 0 < p < 1:
        return
    cx, cy = DEV_X + sx, DEV_Y + sy
    layer = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = 22 + 70 * ease(p)
    a = int(230 * (1 - p))
    d.ellipse((110 - r, 110 - r, 110 + r, 110 + r), outline=RED + (a,), width=9)
    d.ellipse((110 - 20, 110 - 20, 110 + 20, 110 + 20), fill=RED + (int(200 * (1 - p)),))
    frame.paste(layer, (int(cx - 110), int(cy - 110)), layer)


def pen(frame, sx, sy):
    """A stylus whose tip touches screen position (sx, sy)."""
    cx, cy = DEV_X + sx, DEV_Y + sy
    ang = math.radians(-52)
    ux, uy = math.cos(ang), math.sin(ang)          # along the pen, away from tip
    px, py = -uy, ux
    def pt(a, b):
        return (cx + ux * a + px * b, cy + uy * a + py * b)
    d = ImageDraw.Draw(frame)
    d.polygon([pt(0, 0), pt(46, -13), pt(46, 13)], fill=(60, 60, 64))
    d.polygon([pt(46, -13), pt(430, -13), pt(430, 13), pt(46, 13)], fill=(236, 236, 232),
              outline=(40, 40, 44))
    d.polygon([pt(430, -13), pt(452, -9), pt(452, 9), pt(430, 13)], fill=(190, 190, 186),
              outline=(40, 40, 44))
    d.line([pt(60, 13), pt(425, 13)], fill=(150, 150, 146), width=3)


# --- scenes -------------------------------------------------------------------------
def scene_clip(clip, t, lines):
    f = clip.frame()
    for (a, b, s) in lines:
        caption(f, s, fade(t, a, b))
    return f


def scene_hero(clip, t):
    f = shift_right(clip.frame(), 440)
    t0 = VO["vo3"]
    a1, a2 = fade(t, t0 + 0.80, d=0.3), fade(t, t0 + 1.60, d=0.3)
    put_text(f, 120, 360 + 24 * (1 - a1), "Remarkable", font("Fraunces-900", 118), INK, a1)
    put_text(f, 120, 490 + 24 * (1 - a2), "Mind", font("Fraunces-900", 118), INK, a2)
    a3 = fade(t, t0 + 2.45, d=0.4)
    put_text(f, 127, 660, "HERSENGYM OP PAPIER", font("Inter-700", 40), RED, a3)
    return f


def left_title(f, t, t_in, t_out, small, big, big2=None, color=INK):
    a = fade(t, t_in, t_out)
    dy = 30 * (1 - ease((t - t_in) / 0.5))
    if small:
        put_text(f, 130, 300 + dy, small, font("Inter-700", 34), RED, a)
    put_text(f, 126, 360 + dy, big, font("Fraunces-900", 118), color, a)
    if big2:
        put_text(f, 126, 495 + dy, big2, font("Fraunces-900", 118), color, a)


def scene_show(P, t):
    f = paper_bg()
    v4, v5 = VO["vo4"], VO["vo5"]
    flips = ["p:calcudoku:6", "p:binairo:14", "p:nonogram:5", "p:kleurlink:12",
             "p:wolkenkrabbers:20", "p:piramide:3", "p:lucifers:8", "p:woordzoeker:4",
             "p:bruggen:21", "p:reeksen:2", "p:letterchaos:11", "p:sudoku:9"]
    named = [(v4 + 3.12, "p:sudoku:20", "Sudoku", RED),
             (v4 + 3.84, "p:logigram:11", "Logigram", TEAL),
             (v4 + 4.88, "p:doolhof:19", "Doolhof", MUSTARD),
             (v4 + 5.52, "p:bruggen:13", "Bruggen", TEAL),
             (v4 + 6.24, "p:codekraker:6", "Codekraker", INK)]
    one = v4 + 7.2                       # "En elke puzzel heeft precies een oplossing"
    home2 = v4 + 11.6
    tap1, tap2 = v5 + 0.15, v5 + 0.85
    penstart = v5 + 1.3
    plan = v5 + 2.9
    cats = [(v5 + 6.68, "Getallen", RED, WHITE, "p:calcudoku:12"),
            (v5 + 7.36, "Logica", TEAL, WHITE, "p:binairo:12"),
            (v5 + 8.24, "Ruimte", MUSTARD, INK, "p:nonogram:12"),
            (v5 + 9.04, "Geheugen", INK, WHITE, "p:geheugen:4")]
    colour = v5 + 10.2

    # ---- what is on the tablet -------------------------------------------------
    pen_at = None
    if t < v4 + 0.2:
        scr = P.page("cover")
    elif t < v4 + 1.5:
        scr = P.page("home")
    elif t < named[0][0]:
        scr = P.page(flips[int((t - v4 - 1.5) / 0.135) % len(flips)])
    elif t < one:
        scr = [k for (ts, k, _, _) in named if t >= ts][-1]
        scr = P.page(scr)
    elif t < home2:
        base, top = P.page("p:sudoku:20"), P.solved("sudoku", 20)
        p = clamp((t - (v4 + 8.3)) / 2.6)
        scr = wipe(base, top, p)
        if 0 < p < 1:
            pen_at = (300 + 220 * math.sin(t * 9), 150 + p * 560)
    elif t < tap1 + 0.3:
        scr = P.page("home")
    elif t < tap2 + 0.3:
        scr = P.page("hub:doolhof")
    elif t < plan:
        base, top = P.page("p:doolhof:19"), P.solved("doolhof", 19)
        p = clamp((t - penstart) / 1.4)
        scr = wipe(base, top, p)
        if 0 < p < 1:
            pen_at = (315 + 200 * math.sin(t * 8), 190 + p * 520)
    elif t < cats[0][0]:
        scr = P.page("training1")
    elif t < colour:
        scr = P.page([c[4] for c in cats if t >= c[0]][-1])
    else:
        seq = [("kleurlink", 20), ("nonogram", 14), ("woordzoeker", 6)]
        k = min(int((t - colour) / 1.4), len(seq) - 1)
        g, n = seq[k]
        p = clamp(((t - colour) - k * 1.4 - 0.15) / 0.85)
        scr = wipe(P.page(f"p:{g}:{n}"), P.solved(g, n), p)
        if 0 < p < 1:
            pen_at = (315 + 210 * math.sin(t * 8), 170 + p * 540)

    dy = (1 - ease((t - T_SHOW) / 0.9)) * 1100
    dy += ease((t - (T_TRAIN - 0.5)) / 0.5) * 1100 if t > T_TRAIN - 0.5 else 0
    device(f, scr, dy)
    if pen_at and abs(dy) < 1:
        pen(f, *pen_at)
    hx, hy = P.link_center("home", "hub:doolhof")
    tap(f, hx, hy, (t - tap1) / 0.5)
    bx, by = P.link_center("hub:doolhof", "p:doolhof:19")
    tap(f, bx, by, (t - tap2) / 0.5)

    # ---- the story on the left ---------------------------------------------------
    n16 = int(round(16 * ease((t - v4 - 0.2) / 0.6)))
    left_title(f, t, v4 + 0.2, v4 + 1.45, None, f"{n16} spellen")
    n400 = int(round(400 * ease((t - v4 - 1.5) / 0.8)))
    left_title(f, t, v4 + 1.5, named[0][0] - 0.05, None, f"{n400} puzzels")
    for i, (ts, _, name, col) in enumerate(named):
        a = fade(t, ts, one - 0.1, d=0.22)
        y = 250 + i * 112
        if a > 0:
            lay = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
            ImageDraw.Draw(lay).ellipse((6, 6, 54, 54), fill=col + (int(255 * a),))
            f.paste(lay, (130, y + 22), lay)
        put_text(f, 210 + 30 * (1 - ease((t - ts) / 0.3)), y, name,
                 font("Fraunces-700", 88), INK, a)
    put_text(f, 136, 830, "… en nog 11 andere spellen", font("Inter-600", 38),
             (110, 110, 110), fade(t, named[-1][0] + 0.6, one - 0.1))
    left_title(f, t, one + 0.1, home2 - 0.1, "ELKE PUZZEL IS NAGEREKEND", "Precies één",
               "oplossing.")
    put_text(f, 130, 670, "Gokken hoeft nooit.", font("Fraunces-700", 66), RED,
             fade(t, v4 + 10.0, home2 - 0.1))
    left_title(f, t, v5 + 0.05, penstart - 0.05, "NAVIGEREN", "Tik om te", "bladeren.")
    left_title(f, t, penstart, plan - 0.05, "OPLOSSEN", "Los op met", "je pen.")
    left_title(f, t, plan, colour - 0.05, "ELKE DAG VIER DENKSPIEREN", "30 dagen",
               "hersengym.")
    x = 130
    for (ts, name, bg, fg, _) in cats:
        fnt = font("Inter-700", 40)
        wpx = fnt.getbbox(name)[2] + 56
        pill(f, x + wpx / 2, 700 + 20 * (1 - ease((t - ts) / 0.3)), name, fnt, bg, fg,
             fade(t, ts, colour - 0.05, d=0.2), pad=(28, 16))
        x += wpx + 16
    left_title(f, t, colour + 0.1, T_TRAIN - 0.45, "GEMAAKT VOOR KLEUREN-E-INK", "In kleur.",
               "Op papier.")
    put_text(f, 132, 670, "reMarkable Paper Pro · 11,8 inch", font("Inter-600", 40),
             (110, 110, 110), fade(t, colour + 0.8, T_TRAIN - 0.45))
    return f


_wall = None


def scene_wall(P, t):
    """A drifting wall of real pages."""
    global _wall
    keys = [k for k in P.index if k.startswith("p:") and k.count(":") == 2]
    if _wall is None:
        tw, th, gap = 300, 400, 26
        rows, cols = 4, 12
        step = max(1, len(keys) // (rows * cols))
        picks = keys[::step][:rows * cols]
        _wall = []
        for r in range(rows):
            strip = Image.new("RGB", (cols * (tw + gap), th), PAPER)
            for c in range(cols):
                k = picks[(r * cols + c * 5 + r * 3) % len(picks)]
                im = P.page(k).resize((tw, th), Image.LANCZOS)
                ImageDraw.Draw(im).rectangle((0, 0, tw - 1, th - 1), outline=(40, 40, 40), width=2)
                strip.paste(im, (c * (tw + gap), 0))
            _wall.append(strip)
    big = Image.new("RGB", (2500, 1760), PAPER)
    u = t - T_WALL
    for r, strip in enumerate(_wall):
        off = int(140 + u * 120) if r % 2 == 0 else int(900 - u * 120)
        big.paste(strip.crop((off, 0, off + 2500, strip.height)), (0, 20 + r * 430))
    big = big.rotate(7, resample=Image.BICUBIC, fillcolor=PAPER)
    f = big.crop((290, 340, 290 + W, 340 + H))
    a = fade(t, T_WALL + 0.35, T_END - 0.1, d=0.3)
    pill(f, W / 2, H / 2 - 62, "400 puzzels. Eén PDF.", font("Fraunces-900", 104), INK, WHITE,
         a, pad=(70, 42))
    pill(f, W / 2, H / 2 + 112, "Geen app-store. Geen wifi. Geen meldingen.",
         font("Inter-700", 44), RED, WHITE, fade(t, T_WALL + 1.3, T_END - 0.1, d=0.3),
         pad=(44, 24))
    return f


_end_bg = None


def scene_end(t):
    global _end_bg
    if _end_bg is None:
        art = Image.open(PROMO / "art" / "film_hero.jpg").convert("RGB").resize((W, H), Image.LANCZOS)
        _end_bg = shift_right(art, 440)
    z = 1.0 + 0.035 * (t - T_END) / (DUR - T_END)
    f = _end_bg.resize((int(W * z), int(H * z)), Image.BICUBIC)
    ox, oy = (f.width - W), (f.height - H) // 2
    f = f.crop((ox, oy, ox + W, oy + H))
    v = VO["vo7"]
    a = fade(t, v + 0.1, d=0.35)
    put_text(f, 120, 200, "Remarkable", font("Fraunces-900", 118), INK, a)
    put_text(f, 120, 330, "Mind", font("Fraunces-900", 118), INK, a)
    put_text(f, 127, 500, "HERSENGYM OP PAPIER", font("Inter-700", 40), RED, fade(t, v + 0.8))
    put_text(f, 125, 610, "Geen meldingen.", font("Fraunces-600", 56), INK, fade(t, v + 1.68))
    put_text(f, 125, 686, "Alleen jij, je pen", font("Fraunces-600", 56), INK, fade(t, v + 2.8))
    put_text(f, 125, 762, "en een goed raadsel.", font("Fraunces-600", 56), INK, fade(t, v + 4.5))
    a = fade(t, CHORD, d=0.25)
    pill(f, 120 + 400, 920 + 16 * (1 - ease((t - CHORD) / 0.4)),
         "16 spellen · 400 puzzels · 100% offline", font("Inter-700", 36), INK, WHITE, a,
         pad=(36, 20))
    if t > DUR - 0.8:                                   # fade to paper
        k = smooth((t - (DUR - 0.8)) / 0.7)
        f = Image.blend(f, Image.new("RGB", (W, H), PAPER), k)
    return f


# --- audio ----------------------------------------------------------------------------
def build_audio(out_wav):
    sr = 48000

    def load(path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar",
                              str(sr), "-f", "f32le", "-"], capture_output=True).stdout
        return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()

    n = int(DUR * sr)
    music = load(PROMO / "audio" / "music.mp3")[:n]
    music = np.pad(music, ((0, n - len(music)), (0, 0)))
    voice = np.zeros((n, 2), dtype=np.float32)
    duck = np.ones(n, dtype=np.float32)
    for name, start in VO.items():
        v = load(PROMO / "audio" / f"{name}.mp3")
        i = int(start * sr)
        voice[i:i + len(v)] += v[:n - i]
        a, b = max(0, i - int(0.25 * sr)), min(n, i + len(v) + int(0.3 * sr))
        if a < CHORD * sr < b + 0.4 * sr:     # let the final chord ring at full level
            b = int((CHORD - 0.3) * sr)
        duck[a:b] = 0.34                      # music steps back under the voice
    k = int(0.35 * sr)
    kernel = np.hanning(k)
    kernel /= kernel.sum()
    duck = np.convolve(duck, kernel, mode="same")
    env = np.ones(n, dtype=np.float32)
    f = int(1.0 * sr)
    env[-f:] = np.linspace(1, 0, f)
    mix = voice * 1.25 + music * (0.62 * duck * env)[:, None]
    mix = np.clip(mix, -1.0, 1.0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2",
                    "-i", "-", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", str(out_wav)],
                   input=mix.astype(np.float32).tobytes(), check=True)


# --- main -------------------------------------------------------------------------------
def render(out, preview=False, stills=None):
    pdf = ROOT / "dist" / "RemarkableMind.pdf"
    seed = json.loads(pdf.with_suffix(".json").read_text())["seed"]
    P = Pages(pdf, seed)
    if stills:                                  # debug: save single frames
        clips = {}
        for ts in stills:
            f = frame_at(P, clips, float(ts), seek=True)
            p = Path(out).parent / f"still-{float(ts):05.1f}.jpg"
            f.save(p, quality=88)
            print(p)
        return
    wav = ROOT / "build" / "film-audio.wav"
    wav.parent.mkdir(exist_ok=True)
    build_audio(wav)
    scale = ["-vf", "scale=960:540"] if preview else []
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
         f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav), *scale, "-c:v", "libx264",
         "-preset", "medium", "-crf", "28" if preview else "21", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)],
        stdin=subprocess.PIPE)
    clips = {}
    for i in range(int(DUR * FPS)):
        f = frame_at(P, clips, i / FPS)
        enc.stdin.write(f.tobytes())
        if i % 150 == 0:
            print(f"  {i / FPS:5.1f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    print(out, f"{Path(out).stat().st_size / 1e6:.1f} MB")


CLIPS = {"ruis": (0.0, T_RUST), "rust": (T_RUST, T_HERO), "hero": (T_HERO, T_SHOW),
         "onderweg": (T_TRAIN, T_WALL)}


def frame_at(P, clips, t, seek=False):
    def clip(name):
        a, b = CLIPS[name]
        if name not in clips:
            clips[name] = Clip(name, b - a)
            if seek:                            # debug stills: skip ahead
                for _ in range(int((t - a) * FPS)):
                    clips[name].frame()
        return clips[name]

    if t < T_RUST:
        return scene_clip(clip("ruis"), t, [
            (VO["vo1"] - 0.1, T_RUST - 0.25,
             "Elke dag vechten honderden meldingen om jouw aandacht.")])
    if t < T_HERO:
        return scene_clip(clip("rust"), t, [
            (VO["vo2"] - 0.1, T_HERO - 0.3, "Tijd om je brein iets beters te geven.")])
    if t < T_SHOW:
        return scene_hero(clip("hero"), t)
    if t < T_TRAIN:
        return scene_show(P, t)
    if t < T_WALL:
        v = VO["vo6"]
        return scene_clip(clip("onderweg"), t, [
            (v - 0.1, v + 3.75, "Thuis, op de trein, of ver weg van elke wifi."),
            (v + 3.85, T_WALL - 0.2, "100% offline.")])
    if t < T_END:
        return scene_wall(P, t)
    return scene_end(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PROMO / "RemarkableMind-promo.mp4"))
    ap.add_argument("--preview", action="store_true", help="fast 540p render")
    ap.add_argument("--stills", nargs="*", help="only save frames at these times")
    a = ap.parse_args()
    render(a.out, a.preview, a.stills)
