// Offline support: once the engine has been used, the site keeps working
// without a connection. Pyodide files and the content-hashed app zip never
// change under the same name, so they are served cache-first; everything
// else goes to the network first and falls back to the cache.
const CACHE = "remarkable-mind-v1";
const IMMUTABLE = [/^\/pyodide\//, /^\/py\/app\.[0-9a-f]+\.zip$/, /^\/fonts\//];

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/downloads/") || url.pathname.startsWith("/media/")) return;
  if (IMMUTABLE.some((re) => re.test(url.pathname))) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(event.request);
      if (hit) return hit;
      const res = await fetch(event.request);
      if (res.ok) cache.put(event.request, res.clone());
      return res;
    })());
    return;
  }
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const res = await fetch(event.request);
      if (res.ok) cache.put(event.request, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(event.request);
      if (hit) return hit;
      throw err;
    }
  })());
});
