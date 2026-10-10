from __future__ import annotations

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from game import WORLD

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


class DualStackThreadingHTTPServer(ThreadingHTTPServer):
    """Serve both IPv4 and IPv6 localhost clients from one listener."""
    address_family = socket.AF_INET6

    def server_bind(self) -> None:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    server_version = "Gauntlet/0.1"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: dict | str | bytes, content_type: str = "application/json; charset=utf-8") -> None:
        raw = body if isinstance(body, bytes) else body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        size = min(int(self.headers.get("Content-Length", "0")), 16_384)
        return json.loads(self.rfile.read(size) or b"{}")

    def _error(self, message: str, status: int = 400) -> None:
        self._send(status, {"error": message})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            return self._send(200, {"ok": True})
        host_header = self.headers.get("Host", "")
        if host_header.lower().startswith("localhost:"):
            port = host_header.rsplit(":", 1)[-1]
            self.send_response(308)
            self.send_header("Location", f"http://127.0.0.1:{port}{self.path}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if parsed.path == "/":
            return self._file("index.html", "text/html; charset=utf-8")
        if parsed.path in ("/app.js", "/audio.js", "/coordination.js", "/progression.js", "/town-sprites.js", "/combat-environment.js", "/ability-animations.js", "/movement.js", "/equipment-comparison.js", "/style.css"):
            name = parsed.path.lstrip("/")
            mime = "text/javascript; charset=utf-8" if name.endswith(".js") else "text/css; charset=utf-8"
            return self._file(name, mime)
        if parsed.path.startswith("/audio/"):
            name = parsed.path.lstrip("/")
            asset = (STATIC / name).resolve()
            if not asset.is_relative_to((STATIC / "audio").resolve()) or asset.suffix.lower() != ".wav":
                return self._error("Not found.", 404)
            return self._file(name, "audio/wav")
        if parsed.path.startswith("/sprites/"):
            name = parsed.path.lstrip("/")
            asset = (STATIC / name).resolve()
            if not asset.is_relative_to((STATIC / "sprites").resolve()) or asset.suffix.lower() not in (".png", ".json"):
                return self._error("Not found.", 404)
            mime = "image/png" if asset.suffix.lower() == ".png" else "application/json; charset=utf-8"
            return self._file(name, mime)
        if parsed.path in ("/api/state", "/api/stats"):
            query = parse_qs(parsed.query)
            try:
                read = WORLD.state if parsed.path == "/api/state" else WORLD.run_stats
                state = read(query.get("room", [""])[0], query.get("player", [""])[0])
            except ValueError as error:
                return self._error(str(error), 404)
            return self._send(200, state)
        return self._error("Not found.", 404)

    def _file(self, name: str, mime: str) -> None:
        path = STATIC / name
        if not path.is_file():
            return self._error("Client file not found.", 404)
        self._send(200, path.read_bytes(), mime)

    def do_POST(self) -> None:
        try:
            payload = self._body()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return self._error("Invalid request body.")
        try:
            if self.path == "/api/rooms":
                name = str(payload.get("name", "Player")).strip()[:18] or "Player"
                code, player_id = WORLD.create_room(name)
                return self._send(201, {"room": code, "player": player_id})
            if self.path == "/api/join":
                name = str(payload.get("name", "Player")).strip()[:18] or "Player"
                code, player_id = WORLD.join_room(str(payload.get("room", "")), name)
                return self._send(201, {"room": code, "player": player_id})
            if self.path == "/api/action":
                WORLD.action(str(payload.get("room", "")), str(payload.get("player", "")), payload)
                return self._send(200, {"ok": True})
        except ValueError as error:
            return self._error(str(error))
        return self._error("Not found.", 404)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def _simulation_loop() -> None:
    while True:
        WORLD.tick()
        time.sleep(0.05)


def main() -> None:
    host = os.environ.get("HOST", "::")
    port = int(os.environ.get("PORT", "8000"))
    server_class = DualStackThreadingHTTPServer if ":" in host else ThreadingHTTPServer
    server = server_class((host, port), Handler)
    threading.Thread(target=_simulation_loop, daemon=True).start()
    print(f"The Gauntlet listening on port {port} (open http://localhost:{port} on this computer)")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
