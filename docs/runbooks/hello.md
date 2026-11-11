# Runbook: hello

Start with the Grafana dashboard named `hello`, then use the section for the
alert that fired.

Useful commands:

```bash
kubectl -n hello get pods -o wide
```

```bash
kubectl -n hello logs -l app.kubernetes.io/name=hello --tail=100
```

```bash
git log --oneline -5 -- deploy/envs/dev/values.yaml
```

## HelloDown

No pod has been scraped successfully for 5 minutes.

1. Check whether pods exist and are ready. `Pending` points at capacity or
   scheduling; `ImagePullBackOff` at the registry or a bad tag;
   `CrashLoopBackOff` at the app, so read the logs.
2. If pods are healthy, the problem is the scrape. Check that the
   ServiceMonitor exists and that the NetworkPolicy still allows the
   `monitoring` namespace.
3. If the alert started right after a deploy, revert the commit that changed
   the image tag. Argo CD rolls the previous version back out.

## HelloHighErrorRate

More than 5% of requests have returned 5xx for 10 minutes.

1. Compare the start of the errors with the last deploy. If they line up,
   revert the tag change first and investigate afterwards.
2. Read the logs for the failing requests.
3. Check whether the errors come from one pod or one node. If so, delete that
   pod and look at the node.

## HelloHighLatency

p99 latency of `/` has been above 500 ms for 10 minutes.

1. Check CPU throttling and memory against the limits in the chart values.
2. Check whether the request rate has risen. If it has, enable the
   HorizontalPodAutoscaler or raise `replicaCount`.
3. Check the nodes for noisy neighbours or pressure conditions.
