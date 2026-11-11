# ADR 1: Deploy by pull (GitOps), not by push from CI

## Context

A pipeline can deploy in two ways. It can push: CI holds cluster credentials
and runs `helm upgrade` or `kubectl apply`. Or the cluster can pull: an agent
inside it watches a Git repository and applies what it finds.

## Decision

Argo CD pulls from this repository. CI builds the image and then changes one
line in Git, the image tag in `deploy/envs/dev/values.yaml`. It has no access
to the cluster.

## Why

- **Credentials.** A push model puts cluster-admin credentials in CI, where
  every workflow and third-party action can reach them. With pull, the only
  secret CI uses is the short-lived `GITHUB_TOKEN`.
- **Audit and rollback.** What runs in the cluster is what is in Git. A
  rollback is `git revert`, and the history shows who deployed what and when.
- **Drift.** Argo CD self-heals, so a manual `kubectl edit` is reverted rather
  than silently kept.

## Costs

- Argo CD is one more component to run and upgrade.
- A deployment is asynchronous. The release workflow finishing does not mean
  the rollout has succeeded; that signal comes from Argo CD and the alerts.
- CI commits to `main`, so branch protection has to allow that bot, or the
  promotion has to become a pull request.
