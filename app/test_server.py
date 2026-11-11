import json
import threading
import unittest
import urllib.error
import urllib.request

import server


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = server.App()
        self.httpd = server.serve(self.app, 0)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    def get(self, path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode()

    def test_root_reports_service_and_version(self) -> None:
        status, body = self.get("/")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["service"], "hello")
        self.assertEqual(payload["version"], server.VERSION)

    def test_health_and_readiness(self) -> None:
        self.assertEqual(self.get("/healthz"), (200, "ok\n"))
        self.assertEqual(self.get("/readyz"), (200, "ready\n"))

    def test_readiness_fails_while_draining_but_liveness_holds(self) -> None:
        self.app.ready.clear()
        self.assertEqual(self.get("/readyz")[0], 503)
        self.assertEqual(self.get("/healthz")[0], 200)

    def test_unknown_path_is_404(self) -> None:
        self.assertEqual(self.get("/nope")[0], 404)

    def test_metrics_count_requests_with_bounded_path_label(self) -> None:
        self.get("/")
        self.get("/some/random/path")
        self.get("/another/random/path")
        _, metrics = self.get("/metrics")
        self.assertIn('http_requests_total{method="GET",path="/",status="200"} 1.0', metrics)
        self.assertIn('http_requests_total{method="GET",path="other",status="404"} 2.0', metrics)
        self.assertNotIn("random", metrics)
        self.assertIn("http_request_duration_seconds_bucket", metrics)


if __name__ == "__main__":
    unittest.main()
