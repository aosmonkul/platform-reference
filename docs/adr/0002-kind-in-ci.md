# ADR 2: Prove deployments on kind in CI

## Context

Linting a chart and validating its schemas catch syntax errors. They do not
show that the pods start, pass their probes and serve traffic under the
security context and network policy the chart sets.

## Decision

Every pull request builds the image, creates a kind cluster on the runner,
installs the chart with `helm --wait`, runs a smoke test, then does a rolling
restart and runs the smoke test again.

## Why

- It tests the thing that ships: the same image and chart, on a real API
  server and kubelet.
- It costs nothing and needs no cloud account, so forks and outside
  contributors get the same signal.
- It takes a couple of minutes, which is short enough to run on every change.

## Costs

- kind is not EKS. Cloud load balancers, IAM, the VPC CNI and storage classes
  are not covered.
- The monitoring stack is not installed in CI, so the ServiceMonitor and alert
  rules are only schema-checked there.
