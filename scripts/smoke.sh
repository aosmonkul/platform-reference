#!/usr/bin/env bash
# Smoke test: port-forward to the Service and check the endpoints a platform
# depends on. Usage: scripts/smoke.sh <namespace>
set -euo pipefail

namespace="${1:-hello}"
port=18080

kubectl -n "$namespace" port-forward svc/hello "${port}:80" >/dev/null &
forward_pid=$!
trap 'kill "$forward_pid" 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${port}/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:${port}/healthz"
curl -fsS "http://127.0.0.1:${port}/readyz"
curl -fsS "http://127.0.0.1:${port}/" | grep -q '"service": "hello"'
curl -fsS "http://127.0.0.1:${port}/metrics" | grep -q '^http_requests_total'
echo "smoke test passed"
