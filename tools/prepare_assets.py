"""Turn the generated artwork in promo/art into e-ink friendly PDF assets.

The illustrations were generated on cream "riso paper". On a colour e-ink
panel a cream background would be dithered, so the paper tone is mapped to
pure white while the four inks keep their strength. Each asset also gets a
greyscale twin (``*_grey.jpg``) for the monochrome reMarkable 2.

    python tools/prepare_assets.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "promo" / "art"
DST = ROOT / "mind" / "assets"

JOBS = {                      # name: (source, max width in px)
    "cover": ("cover.jpg", 1536),
    "cat_getallen": ("cat_getallen.jpg", 760),
    "cat_logica": ("cat_logica.jpg", 760),
    "cat_ruimte": ("cat_ruimte.jpg", 760),
    "cat_taal": ("cat_taal.jpg", 760),
    "banner_training": ("banner_training.jpg", 1280),
}


def whiten(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    k = max(8, min(h, w) // 40)
    corners = np.concatenate([a[:k, :k].reshape(-1, 3), a[:k, -k:].reshape(-1, 3),
                              a[-k:, :k].reshape(-1, 3), a[-k:, -k:].reshape(-1, 3)])
    paper = np.median(corners, axis=0)
    out = a / (paper * 0.955) * 255.0      # paper (and its grain) -> white
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def grey(im):
    """Greyscale for the monochrome reMarkable 2.

    A plain luminance conversion turns the red and the teal ink into the same
    grey. This channel mix keeps the four inks apart: black, teal (dark),
    red (middle) and mustard (light)."""
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    g = 0.45 * a[..., 0] + 0.45 * a[..., 1] + 0.10 * a[..., 2]
    g = 255.0 * (g / 255.0) ** 1.08          # a touch more contrast
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "L")


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for name, (src, width) in JOBS.items():
        im = Image.open(SRC / src)
        im = whiten(im)
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        out = DST / f"{name}.jpg"
        im.save(out, quality=88, optimize=True)
        print(f"{out.relative_to(ROOT)}  {im.size}  {out.stat().st_size // 1024} kB")
        out = DST / f"{name}_grey.jpg"
        grey(im).save(out, quality=88, optimize=True)
        print(f"{out.relative_to(ROOT)}  {im.size}  {out.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
