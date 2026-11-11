# syntax=docker/dockerfile:1

FROM python:3.13-slim AS deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --target=/deps -r /tmp/requirements.txt

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/deps \
    PORT=8080
# Take pending OS security fixes, and drop pip from the runtime image: nothing
# installs packages at runtime, and its vendored libraries only add CVEs.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y setuptools wheel pip
COPY --from=deps /deps /deps
COPY server.py /app/server.py
# Numeric, non-root user so Kubernetes can enforce runAsNonRoot.
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python", "/app/server.py"]
