# multiai/api/metrics.py
from fastapi import APIRouter
import time
import psutil
import platform

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "timestamp": time.time()}


@router.get("/system")
async def system_metrics():
    """Return system metrics like CPU and memory usage"""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "uptime_seconds": time.time() - psutil.boot_time(),
    }
# Prometheus metrics endpoints
