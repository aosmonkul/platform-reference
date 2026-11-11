# syntax=docker/dockerfile:1

FROM python:3.13-slim AS deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --target=/deps -r /tmp/requirements.txt

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/deps \
    PORT=8080
COPY --from=deps /deps /deps
COPY server.py /app/server.py
# Numeric, non-root user so Kubernetes can enforce runAsNonRoot.
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python", "/app/server.py"]
