"""Preview with the actual GitHub Pages project prefix."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from docs import BASE, OUT


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT), **kwargs)

    def do_GET(self):
        if not self.path.startswith(BASE + "/"):
            self.send_error(404)
            return
        self.path = self.path[len(BASE) :]
        super().do_GET()


print(f"http://localhost:8001{BASE}/en/dev/index/", flush=True)
ThreadingHTTPServer(("0.0.0.0", 8001), Handler).serve_forever()
