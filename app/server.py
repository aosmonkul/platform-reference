"""hello: a deliberately small HTTP service.

The service is not the point of this repository; the platform around it is.
It still behaves the way a workload should on Kubernetes: separate liveness
and readiness endpoints, Prometheus metrics with bounded label cardinality,
structured logs on stdout, and a graceful shutdown on SIGTERM.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

VERSION = os.environ.get("APP_VERSION", "dev")
KNOWN_PATHS = frozenset({"/", "/healthz", "/readyz", "/metrics"})
QUIET_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})


class App:
    """Holds the state shared by all requests: metrics and readiness."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "http_requests_total",
            "HTTP requests served, by method, path and status code.",
            ["method", "path", "status"],
            registry=self.registry,
        )
        self.latency = Histogram(
            "http_request_duration_seconds",
            "Time spent serving an HTTP request, by path.",
            ["path"],
            registry=self.registry,
        )
        self.ready = threading.Event()
        self.ready.set()

    def route(self, path: str) -> tuple[int, str, bytes]:
        if path == "/":
            body = {"service": "hello", "version": VERSION, "host": socket.gethostname()}
            return 200, "application/json", json.dumps(body).encode()
        if path == "/healthz":
            return 200, "text/plain", b"ok\n"
        if path == "/readyz":
            if self.ready.is_set():
                return 200, "text/plain", b"ready\n"
            return 503, "text/plain", b"shutting down\n"
        if path == "/metrics":
            return 200, CONTENT_TYPE_LATEST, generate_latest(self.registry)
        return 404, "text/plain", b"not found\n"


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802 (name is fixed by http.server)
            started = time.perf_counter()
            path = self.path.split("?", 1)[0]
            status, content_type, body = app.route(path)

            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

            # Unknown paths share one label value so a scanner cannot blow up
            # the number of time series.
            label = path if path in KNOWN_PATHS else "other"
            elapsed = time.perf_counter() - started
            app.requests.labels(self.command, label, str(status)).inc()
            app.latency.labels(label).observe(elapsed)

            if path not in QUIET_PATHS:
                log(
                    "request",
                    method=self.command,
                    path=path,
                    status=status,
                    duration_ms=round(elapsed * 1000, 2),
                )

        def log_message(self, format: str, *args: object) -> None:
            # Replaced by the structured log line in do_GET.
            return

    return Handler


def log(message: str, **fields: object) -> None:
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "msg": message}
    record.update(fields)
    print(json.dumps(record), file=sys.stdout, flush=True)


def serve(app: App, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(app))
    server.daemon_threads = True
    return server


def main() -> None:
    app = App()
    port = int(os.environ.get("PORT", "8080"))
    drain_seconds = float(os.environ.get("SHUTDOWN_DELAY_SECONDS", "5"))
    server = serve(app, port)

    def drain_and_stop() -> None:
        # Fail readiness first and keep serving for a moment, so the endpoint
        # is removed from the Service before the listener closes.
        app.ready.clear()
        log("shutdown started", drain_seconds=drain_seconds)
        time.sleep(drain_seconds)
        server.shutdown()

    def on_signal(signum: int, _frame: object) -> None:
        threading.Thread(target=drain_and_stop, daemon=True).start()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    log("listening", port=port, version=VERSION)
    server.serve_forever()
    server.server_close()
    log("stopped")


if __name__ == "__main__":
    main()
