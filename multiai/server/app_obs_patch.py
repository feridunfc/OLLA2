# multiai/server/app_obs_patch.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from ..api import audit as audit_api
from ..api import test_metrics as test_api

def wire_observability(app: FastAPI):
    # CORS
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    # /metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    # Routers
    app.include_router(audit_api.router, prefix="/api")
    app.include_router(test_api.router, prefix="/api")
    return app
