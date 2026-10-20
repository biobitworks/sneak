"""SNEAK local web app. Stdlib only; binds loopback only; GET only; no accounts.

    python3 -m apps.sneak_mvp.server [--port 8765]
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import APP_DIR
from . import graph
from .sanitize import assert_clean_json, redact

STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/audit": ("audit.html", "text/html; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/audit.js": ("audit.js", "text/javascript; charset=utf-8"),
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
}
API = {"/api/graph": graph.build_graph, "/api/audit": graph.build_audit,
       "/api/health": lambda: {"status": "serving", "service": "sneak-mvp",
                               "evidence_integrity": graph.build_graph().get("integrity")}}
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                               "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "SNEAK"
    sys_version = ""

    def log_message(self, fmt, *args):  # path + status only, never headers
        sys.stderr.write("%s %s\n" % (self.command, redact(fmt % args)[0]))

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _host_ok(self) -> bool:
        # DNS-rebinding guard: only loopback Host headers are served.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return is_loopback(host)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b'{"error":"forbidden host"}', "application/json")
        path = self.path.split("?", 1)[0]
        if path in API:
            try:
                body = assert_clean_json(API[path]())
            except ValueError:
                return self._send(500, b'{"error":"response withheld: failed secret check"}', "application/json")
            except Exception:  # noqa: BLE001 - never leak tracebacks
                return self._send(500, b'{"error":"internal error"}', "application/json")
            return self._send(200, body, "application/json")
        if path in STATIC:
            name, ctype = STATIC[path]
            return self._send(200, (APP_DIR / "web" / name).read_bytes(), ctype)
        return self._send(404, b'{"error":"not found"}', "application/json")

    do_HEAD = do_GET

    def _reject(self):
        self._send(405, b'{"error":"method not allowed"}', "application/json")

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _reject


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if not is_loopback(host):
        raise ValueError("SNEAK MVP binds loopback only")
    return ThreadingHTTPServer((host, port), Handler)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sneak-mvp")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args(argv)
    srv = make_server(a.host, a.port)
    print(f"SNEAK MVP on http://{a.host}:{srv.server_address[1]}/  (audit: /audit)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
