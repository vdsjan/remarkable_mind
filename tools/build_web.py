"""Build the static website in web/public from the Python generator.

    python tools/build_web.py

What it produces (all committed, so Cloudflare only has to serve files):

  web/public/pyodide/   Pyodide runtime + the Pillow wheel (self-hosted, so
                        the site works without third-party CDNs and offline)
  web/public/py/        app.<hash>.zip with the `mind` package and reportlab,
                        manifest.json with games, devices and file names
  web/public/img/       game icons, artwork and page previews per device
  web/public/fonts/     Fraunces, Inter and Caveat as woff2
  web/public/downloads/ the three ready-made editions
  web/public/media/     a web version of the promo film

Needs: npm (to fetch Pyodide once), PyMuPDF, fontTools + brotli, ffmpeg.
"""
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.pdfgen import canvas  # noqa: E402

from mind import __version__, book, games, theme  # noqa: E402

PUBLIC = ROOT / "web" / "public"
CACHE = ROOT / "build" / "web-cache"
PYODIDE_VERSION = "314.0.8"
PYODIDE_FILES = ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm",
                 "python_stdlib.zip", "pyodide-lock.json"]
PYODIDE_CDN = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"
EXTRA_PACKAGES = ["pillow"]               # reportlab imports PIL at start-up


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


# --- Pyodide ---------------------------------------------------------------------
def build_pyodide():
    dst = PUBLIC / "pyodide"
    dst.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    tgz = CACHE / f"pyodide-{PYODIDE_VERSION}.tgz"
    if not tgz.exists():
        subprocess.run(["npm", "pack", f"pyodide@{PYODIDE_VERSION}", "--silent"],
                       cwd=CACHE, check=True, capture_output=True)
    with tarfile.open(tgz) as tar:
        for name in PYODIDE_FILES:
            data = tar.extractfile(f"package/{name}").read()
            (dst / name).write_bytes(data)
    lock = json.loads((dst / "pyodide-lock.json").read_text())
    for pkg in EXTRA_PACKAGES:
        info = lock["packages"][pkg]
        for dep in info.get("depends", []):
            assert dep in EXTRA_PACKAGES, f"{pkg} needs {dep}"
        target = dst / info["file_name"]
        if not target.exists() or sha256(target.read_bytes()) != info["sha256"]:
            cached = CACHE / info["file_name"]
            if not cached.exists():
                cached.write_bytes(fetch(PYODIDE_CDN + info["file_name"]))
            data = cached.read_bytes()
            assert sha256(data) == info["sha256"], f"checksum mismatch for {pkg}"
            target.write_bytes(data)
    print("pyodide:", sum(p.stat().st_size for p in dst.iterdir()) // 1_000_000, "MB")


# --- the Python app ------------------------------------------------------------------
def build_app_zip():
    import reportlab
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        def add_tree(src, arc, keep):
            for p in sorted(src.rglob("*")):
                if p.is_dir() or "__pycache__" in p.parts or p.suffix == ".pyc":
                    continue
                if keep(p):
                    zi = zipfile.ZipInfo(str(Path(arc) / p.relative_to(src)),
                                         date_time=(2026, 1, 1, 0, 0, 0))
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    z.writestr(zi, p.read_bytes())

        add_tree(ROOT / "mind", "mind",
                 lambda p: p.suffix in (".py", ".ttf", ".txt")
                 or (p.suffix == ".jpg" and p.parent.name == "assets"))
        rl = Path(reportlab.__file__).parent
        add_tree(rl, "reportlab",
                 lambda p: p.suffix in (".py", ".afm", ".pfb", ".ttf")
                 and "graphics/samples" not in p.as_posix())
    data = buf.getvalue()
    name = f"app.{sha256(data)[:12]}.zip"
    out = PUBLIC / "py"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("app.*.zip"):
        old.unlink()
    (out / name).write_bytes(data)
    print("app zip:", name, len(data) // 1000, "kB")
    return name


# --- images ------------------------------------------------------------------------
def render_icons():
    """Each game's own vector pictogram, rendered once for the website."""
    out = PUBLIC / "img" / "icons"
    out.mkdir(parents=True, exist_ok=True)
    theme.register_fonts()
    theme.set_device("paperpro")
    tmp = CACHE / "icons.pdf"
    c = canvas.Canvas(str(tmp), pagesize=(64, 64))
    order = games.ORDER
    for key in order:
        games.get(key).icon(c, 32, 32, 44, theme.INK)
        c.showPage()
    c.save()
    doc = pymupdf.open(str(tmp))
    for key, page in zip(order, doc):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), alpha=True)
        pix.save(str(out / f"{key}.png"))


def webp(src, dst, width, quality=82):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=quality, method=6)


def build_images():
    art = ROOT / "promo" / "art"
    img = PUBLIC / "img"
    webp(art / "cover.jpg", img / "cover.webp", 900)
    webp(art / "film_hero.jpg", img / "hero.webp", 1600)
    webp(art / "banner_training.jpg", img / "plan.webp", 900)
    for cat in theme.CATEGORY_ORDER:
        webp(art / f"cat_{cat}.jpg", img / f"cat_{cat}.webp", 420)
    webp(art / "film_rust.jpg", img / "poster.webp", 1280)


def build_previews(manifest_devices):
    """Home and one puzzle page of each ready-made edition, for the device cards."""
    out = PUBLIC / "img" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    for dev in manifest_devices:
        pdf = ROOT / "dist" / f"RemarkableMind{theme.DEVICES[dev]['suffix']}.pdf"
        idx = json.loads(pdf.with_suffix(".json").read_text())["pages"]
        doc = pymupdf.open(str(pdf))
        for name, key in (("home", "home"), ("puzzle", "p:kleurlink:20")):
            page = doc[idx[key]]
            z = 520 / page.rect.width
            pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z))
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.save(out / f"{dev}-{name}.webp", "WEBP", quality=86, method=6)


def build_fonts():
    from fontTools.ttLib import TTFont
    out = PUBLIC / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("Fraunces-700", "Fraunces-900", "Inter-400", "Inter-500",
                 "Inter-600", "Inter-700", "Caveat-700"):
        f = TTFont(str(ROOT / "mind" / "fonts" / f"{name}.ttf"))
        f.flavor = "woff2"
        f.save(str(out / f"{name}.woff2"))
    for lic in (ROOT / "mind" / "fonts").glob("LICENSE-*.txt"):
        shutil.copy(lic, out / lic.name)


def build_downloads():
    out = PUBLIC / "downloads"
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for dev, info in theme.DEVICES.items():
        src = ROOT / "dist" / f"RemarkableMind{info['suffix']}.pdf"
        dst = out / src.name
        shutil.copy(src, dst)
        meta = json.loads(src.with_suffix(".json").read_text())
        files[dev] = {"file": f"downloads/{src.name}",
                      "mb": round(dst.stat().st_size / 1e6, 1),
                      "pages": len(meta["pages"])}
    return files


def build_film():
    src = ROOT / "promo" / "RemarkableMind-promo.mp4"
    dst = PUBLIC / "media" / "remarkable-mind.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=1280:720",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)],
                   check=True)
    print("film:", dst.stat().st_size // 1_000_000, "MB")


# --- manifest ----------------------------------------------------------------------
def build_manifest(app_zip, downloads):
    lock = json.loads((PUBLIC / "pyodide" / "pyodide-lock.json").read_text())
    theme.set_device("paperpro")
    manifest = {
        "version": __version__,
        "app": f"py/{app_zip}",
        "pyodide": PYODIDE_VERSION,
        "packages": EXTRA_PACKAGES,
        "python": lock["info"]["python"],
        "maxPerGame": book.MAX_PER_GAME,
        "difficulties": book.DIFFICULTIES,
        "categories": [{"key": k, "name": theme.CATEGORIES[k]["name"],
                        "blurb": theme.CATEGORIES[k]["blurb"],
                        "color": "#%02X%02X%02X" % tuple(
                            round(v * 255) for v in theme.CATEGORIES[k]["color"].rgb())}
                       for k in theme.CATEGORY_ORDER],
        "games": [{"key": g.key, "name": g.name, "category": g.category,
                   "tagline": g.tagline, "parts": g.parts,
                   "new": g.key in games.NEW,
                   "rules": [theme.localize(r) for r in g.rules]}
                  for g in games.all_games()],
        "totals": {"games": len(games.ORDER),
                   "puzzles": sum(sum(g.counts) for g in games.all_games())},
        "devices": [{"key": k, "label": v["label"], "screen": v["screen"],
                     "px": v["px"], "mono": v["mono"], "suffix": v["suffix"],
                     "download": downloads[k]}
                    for k, v in (("paperpro", theme.DEVICES["paperpro"]),
                                 ("move", theme.DEVICES["move"]),
                                 ("rm2", theme.DEVICES["rm2"]))],
    }
    (PUBLIC / "py" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1))
    return manifest


def main():
    build_pyodide()
    app_zip = build_app_zip()
    render_icons()
    build_images()
    build_fonts()
    downloads = build_downloads()
    build_previews(["paperpro", "move", "rm2"])
    build_film()
    build_manifest(app_zip, downloads)
    total = sum(p.stat().st_size for p in PUBLIC.rglob("*") if p.is_file())
    biggest = max((p for p in PUBLIC.rglob("*") if p.is_file()), key=lambda p: p.stat().st_size)
    print(f"web/public: {total / 1e6:.1f} MB, largest {biggest.relative_to(PUBLIC)} "
          f"{biggest.stat().st_size / 1e6:.1f} MB")
    assert biggest.stat().st_size < 25 * 1024 * 1024, "Cloudflare limit is 25 MiB per file"


if __name__ == "__main__":
    main()
