"""The website bundle in web/public must match the Python sources.

If this fails, run:  python tools/build_web.py
"""
import json
import zipfile
from pathlib import Path

from mind import games

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "web" / "public"


def manifest():
    return json.loads((PUBLIC / "py" / "manifest.json").read_text())


def test_app_zip_contains_the_current_generator():
    m = manifest()
    with zipfile.ZipFile(PUBLIC / m["app"]) as z:
        names = set(z.namelist())
        for src in sorted((ROOT / "mind").rglob("*.py")):
            arc = str(src.relative_to(ROOT))
            assert arc in names, f"{arc} missing from the web bundle"
            assert z.read(arc) == src.read_bytes(), f"{arc} is stale in the web bundle"
        assert "reportlab/pdfgen/canvas.py" in names


def test_manifest_lists_every_game_and_device():
    m = manifest()
    assert [g["key"] for g in m["games"]] == games.ORDER
    assert [d["key"] for d in m["devices"]] == ["paperpro", "move", "rm2"]
    for d in m["devices"]:
        assert (PUBLIC / d["download"]["file"]).exists()
        for name in ("home", "puzzle"):
            assert (PUBLIC / "img" / "preview" / f"{d['key']}-{name}.webp").exists()
    for g in m["games"]:
        assert (PUBLIC / "img" / "icons" / f"{g['key']}.png").exists()


def test_pyodide_runtime_is_self_hosted():
    m = manifest()
    lock = json.loads((PUBLIC / "pyodide" / "pyodide-lock.json").read_text())
    for name in ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip"):
        assert (PUBLIC / "pyodide" / name).exists()
    for pkg in m["packages"]:
        assert (PUBLIC / "pyodide" / lock["packages"][pkg]["file_name"]).exists()


def test_every_file_fits_cloudflare_limits():
    files = [p for p in PUBLIC.rglob("*") if p.is_file()]
    assert len(files) < 20_000
    assert max(p.stat().st_size for p in files) < 25 * 1024 * 1024
