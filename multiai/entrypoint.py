from fastapi import FastAPI
import uvicorn
import os
import logging
from .github_app import router as github_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OLLA2 Multi-AI System", version="5.2.0")

# GitHub router'ını ekle
app.include_router(github_router, prefix="/api/github")

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "olla2", "version": "5.2.0"}

@app.get("/")
async def root():
    return {"message": "OLLA2 Multi-AI System Running in Docker"}

@app.get("/metrics")
async def metrics():
    return {"message": "Prometheus metrics endpoint - coming soon"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting OLLA2 server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
