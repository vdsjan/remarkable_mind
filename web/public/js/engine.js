// Remarkable Mind engine: runs the Python generator in this Web Worker.
//
// Messages in:  {type: "init", manifest}           load Python + the app once
//               {type: "build", id, spec}          build a book
// Messages out: {type: "status", text}             loading steps
//               {type: "ready", seconds}
//               {type: "progress", id, stage, done, total}
//               {type: "done", id, pdf (ArrayBuffer), stats}
//               {type: "error", id, message}
import { loadPyodide } from "../pyodide/pyodide.mjs";

let ready = null;
let py = null;

const base = new URL("../", import.meta.url);

async function init(manifest) {
  const t0 = performance.now();
  postMessage({ type: "status", text: "Rekenmotor laden" });
  py = await loadPyodide({ indexURL: new URL("pyodide/", base).href });
  postMessage({ type: "status", text: "Bibliotheken laden" });
  await py.loadPackage(manifest.packages, { messageCallback: () => {} });
  postMessage({ type: "status", text: "Puzzelgenerator uitpakken" });
  const zip = await fetch(new URL(manifest.app, base)).then((r) => {
    if (!r.ok) throw new Error(`app download failed (${r.status})`);
    return r.arrayBuffer();
  });
  py.unpackArchive(zip, "zip", { extractDir: "/app" });
  py.runPython(`
import json, sys
sys.path.insert(0, "/app")
from pathlib import Path
from mind import book, theme

def build_book(spec_json, progress):
    spec = json.loads(spec_json)
    sel = book.Selection(spec["counts"], spec["difficulty"], spec["plan"],
                         spec["solutions"])
    out = Path("/tmp/remarkable-mind.pdf")
    stats = book.build(seed=int(spec["seed"]), out=out, jobs=1, cache=None,
                       device=spec["device"], selection=sel,
                       progress=progress, log=lambda *a: None)
    return json.dumps(stats)
`);
  postMessage({ type: "ready", seconds: (performance.now() - t0) / 1000 });
}

self.onmessage = async (event) => {
  const msg = event.data;
  try {
    if (msg.type === "init") {
      ready = ready || init(msg.manifest);
      await ready;
      return;
    }
    if (msg.type === "build") {
      if (!ready) throw new Error("engine not initialised");
      await ready;
      let last = 0;
      const progress = (stage, done, total) => {
        const now = performance.now();
        if (now - last > 60 || done === total) {
          last = now;
          postMessage({ type: "progress", id: msg.id, stage, done, total });
        }
      };
      const t0 = performance.now();
      const buildBook = py.globals.get("build_book");
      const statsJson = buildBook(JSON.stringify(msg.spec), progress);
      buildBook.destroy();
      const stats = JSON.parse(statsJson);
      stats.browserSeconds = (performance.now() - t0) / 1000;
      const bytes = py.FS.readFile("/tmp/remarkable-mind.pdf");
      py.FS.unlink("/tmp/remarkable-mind.pdf");
      const pdf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      postMessage({ type: "done", id: msg.id, pdf, stats }, [pdf]);
    }
  } catch (err) {
    const text = String(err && err.message ? err.message : err);
    // Python tracebacks are long: the last line says what went wrong
    const lines = text.trim().split("\n");
    postMessage({ type: "error", id: msg.id, message: lines[lines.length - 1], detail: text });
  }
};
