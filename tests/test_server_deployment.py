import json
import threading
import unittest
from urllib.request import Request, urlopen
from unittest.mock import patch

import server
from game import GameWorld


class DeploymentTests(unittest.TestCase):
    def test_render_host_and_port(self):
        with patch.dict(server.os.environ, {"HOST": "0.0.0.0", "PORT": "10000"}), \
                patch.object(server, "ThreadingHTTPServer") as listener, \
                patch.object(server.threading, "Thread"):
            server.main()
        listener.assert_called_once_with(("0.0.0.0", 10000), server.Handler)
        listener.return_value.serve_forever.assert_called_once()

    def test_local_defaults_preserve_dual_stack(self):
        with patch.dict(server.os.environ, {}, clear=True), \
                patch.object(server, "DualStackThreadingHTTPServer") as listener, \
                patch.object(server.threading, "Thread"):
            server.main()
        listener.assert_called_once_with(("::", 8000), server.Handler)

    def test_http_health_client_and_party_on_hosted_origin(self):
        with patch.object(server, "WORLD", GameWorld()), \
                server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler) as listener:
            worker = threading.Thread(target=listener.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{listener.server_port}"

            def request(path, payload=None):
                data = json.dumps(payload).encode() if payload is not None else None
                req = Request(base + path, data=data, headers={
                    "Host": "the-gauntlet.onrender.com", "Content-Type": "application/json"})
                with urlopen(req, timeout=5) as response:
                    return response.status, response.read()

            try:
                self.assertEqual(json.loads(request("/healthz")[1]), {"ok": True})
                self.assertIn(b"<html", request("/")[1].lower())
                self.assertEqual(request("/ability-animations.js")[0], 200)
                status, raw = request("/api/rooms", {"name": "Host"})
                self.assertEqual(status, 201)
                room = json.loads(raw)
                status, raw = request("/api/join", {"room": room["room"], "name": "Guest"})
                self.assertEqual(status, 201)
                self.assertEqual(json.loads(raw)["room"], room["room"])
                self.assertEqual(request(f'/api/state?room={room["room"]}&player={room["player"]}')[0], 200)
            finally:
                listener.shutdown()
                worker.join(timeout=5)
