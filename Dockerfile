FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl sqlite3 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --shell /bin/bash olla2 && chown -R olla2:olla2 /app
USER olla2
ENV PATH=/home/olla2/.local/bin:$PATH
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/healthz || exit 1
EXPOSE 8000
CMD ["python", "-m", "multiai.entrypoint"]
