# encoding: utf-8
# MultiAI Hardened Runtime Setup (UTF-8 Safe, No Emoji)
# -----------------------------------------------------
# Run with:
#   powershell -ExecutionPolicy Bypass -File .\setup_multiai.ps1
# -----------------------------------------------------

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n=== MultiAI Hardened Runtime Setup Başlıyor ==="

# 1) Python 3.11 kontrolü
Write-Host "Python 3.11 kontrol ediliyor..."
$pythonVersion = & py -3.11 --version 2>$null
if (-not $pythonVersion) {
    Write-Host "Python 3.11 bulunamadı. Lütfen kurun." -ForegroundColor Red
    exit 1
}
Write-Host "Python bulundu: $pythonVersion"

# 2) Sanal ortam
if (-not (Test-Path ".\.venv")) {
    Write-Host "Sanal ortam (.venv) oluşturuluyor..."
    & py -3.11 -m venv .venv
} else {
    Write-Host ".venv zaten mevcut, geçiliyor."
}
$venvPython = ".\.venv\Scripts\python.exe"
$venvPip    = ".\.venv\Scripts\pip.exe"

# 3) Paket kurulumu
Write-Host "Paketler yükleniyor..."
& $venvPip install --upgrade pip
& $venvPip install fastapi uvicorn docker cryptography prometheus-client pytest pyyaml

# 4) Klasör yapısı
$dirs = @("multiai","multiai\core","multiai\utils","multiai\api","config","monitoring","keys","tests")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "Klasör oluşturuldu: $d"
    }
}

# 5) __init__.py dosyaları
" " | Out-File "multiai\__init__.py" -Encoding utf8
" " | Out-File "multiai\core\__init__.py" -Encoding utf8
" " | Out-File "multiai\utils\__init__.py" -Encoding utf8
" " | Out-File "multiai\api\__init__.py" -Encoding utf8

# 6) Ledger Signer
@'
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from pathlib import Path
from datetime import datetime, timezone
import base64, json

KEY_DIR = Path("keys")
PRIV_PATH = KEY_DIR / "private.pem"
PUB_PATH = KEY_DIR / "public.pem"

def _ensure_keys():
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if not PRIV_PATH.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        PRIV_PATH.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ))
        PUB_PATH.write_bytes(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def sign_manifest(manifest: dict) -> str:
    _ensure_keys()
    private_key = serialization.load_pem_private_key(PRIV_PATH.read_bytes(), None)
    payload = {**manifest, "timestamp": datetime.now(timezone.utc).isoformat()}
    data = json.dumps(payload, sort_keys=True).encode()
    sig = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode()

def verify_manifest(manifest: dict, sig_b64: str) -> bool:
    _ensure_keys()
    pub = serialization.load_pem_public_key(PUB_PATH.read_bytes())
    data = json.dumps(manifest, sort_keys=True).encode()
    try:
        pub.verify(base64.b64decode(sig_b64), data, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
'@ | Out-File "multiai\core\ledger_sign.py" -Encoding utf8

# 7) Sandbox Runner
@'
import docker, os
def _get_client(): return docker.from_env()
def run_in_sandbox(cmd=("python","-c","print('ok')")):
    c=_get_client()
    cont=c.containers.run("python:3.11-slim",cmd,detach=True,network_mode="none",user="1000:1000",cap_drop=["ALL"],read_only=True)
    r=cont.wait(timeout=30)
    logs=cont.logs().decode(errors="ignore")
    cont.remove(force=True)
    return r,logs
'@ | Out-File "multiai\utils\sandbox_runner.py" -Encoding utf8

# 8) Metrics
@'
import time
from fastapi import APIRouter, Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
router = APIRouter()
agent_calls = Counter("multiai_agent_calls_total","Total agent calls",["agent","outcome"])
current_budget = Gauge("multiai_budget_usage","Current budget usage")
agent_latency = Histogram("multiai_agent_latency_seconds","Latency seconds",["agent"])
@router.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
async def metrics_middleware(request:Request, call_next):
    s=time.time(); resp=await call_next(request); agent_latency.labels(agent="api").observe(time.time()-s); return resp
'@ | Out-File "multiai\api\metrics.py" -Encoding utf8

# 9) Policy ve Alerts
@'
version: "1.0"
budget_limits:
  daily: 10.0
  monthly: 100.0
  per_request: 0.1
security:
  sandbox_enforced: true
agents:
  developer:
    allowed_actions: ["execute_code"]
'@ | Out-File "config\policy.yaml" -Encoding utf8

@'
alerts:
  - name: "SandboxEscapeAttempt"
    condition: "sandbox_violation_count > 0"
    severity: "critical"
'@ | Out-File "monitoring\alerts.yaml" -Encoding utf8

# 10) Basit test dosyası
@'
from multiai.core.ledger_sign import sign_manifest, verify_manifest
def test_sign_verify():
    m={"test":"ok"}
    sig=sign_manifest(m)
    assert verify_manifest(m,sig)
'@ | Out-File "tests\test_ledger_sign.py" -Encoding utf8

# 11) pytest
Write-Host "`npytest çalıştırılıyor..."
& $venvPython -m pytest -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "Tüm testler başarıyla geçti."
} else {
    Write-Host "Bazı testler başarısız veya atlandı."
}

Write-Host "`nKurulum tamamlandı. Dosyalar oluşturuldu."
Write-Host "Ledger anahtarları: keys/private.pem, keys/public.pem"
Write-Host "Sandbox runner aktif. Policy ve metrics dosyaları yazıldı."
