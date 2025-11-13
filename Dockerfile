FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl sqlite3 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY multiai/ ./multiai/
COPY tests/ ./tests/
COPY *.py ./
COPY *.txt ./
RUN useradd --create-home --shell /bin/bash olla2 && chown -R olla2:olla2 /app
USER olla2
ENV PATH=/root/.local/bin:
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/healthz || exit 1
EXPOSE 8000
CMD ["python", "-m", "multiai.entrypoint"]
