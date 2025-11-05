# App entry point
# multiai/server/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from fastapi.routing import Mount
import logging

# Import API routers
from multiai.api import collaboration
from multiai.api import ledger
from multiai.api import audit
from multiai.api import test_metrics

# Observability
from multiai.core.advanced_metrics import metrics_collector
from multiai.core.audit_logger import audit_logger

app = FastAPI(title="MULTIAI Backend API", version="4.0")

# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["collaboration"])
app.include_router(ledger.router, prefix="/api/ledger", tags=["ledger"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(test_metrics.router, prefix="/api/test", tags=["test"])

# --- Prometheus metrics endpoint ---
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- Startup & shutdown events ---
@app.on_event("startup")
async def startup_event():
    logging.info("🚀 MULTIAI API started with observability & audit stack")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("🛑 MULTIAI API shutting down...")

@app.get("/")
async def root():
    return {"status": "ok", "message": "MULTIAI API v4 - Observability Enabled"}

