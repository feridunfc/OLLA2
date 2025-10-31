"""
Secure Sandbox Enforcement Layer
Sprint B – v4.9
Zorunlu Docker sandbox kontrolü ve subprocess intercept.
"""

import os
import subprocess
import json
import sys
from pathlib import Path


def is_inside_sandbox() -> bool:
    """
    Şu anda Docker sandbox içinde miyiz?
    Basit kontrol: /.dockerenv dosyası var mı?
    """
    return Path("/.dockerenv").exists()


def run_in_sandbox(command: str, timeout: int = 60):
    """
    Komutu güvenli Docker sandbox içinde çalıştır.
    """
    image = "python:3.12-slim"
    sandbox_dir = os.getcwd()

    docker_cmd = [
        "docker", "run",
        "--rm",
        "--network", "none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt", "no-new-privileges:true",
        "-v", f"{sandbox_dir}:/workspace",
        "-w", "/workspace",
        image,
        "bash", "-c", command,
    ]

    print(f"[🛡️] Sandbox başlatılıyor: {command}")
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[❌] Sandbox hata: {e.stderr}")
        raise
    except FileNotFoundError:
        raise RuntimeError("Docker yüklü değil veya PATH'te bulunamadı!")


def secure_subprocess_run(cmd: list[str], **kwargs):
    """
    Subprocess çağrılarının hepsi bu fonksiyon üzerinden geçmeli.
    Sandbox dışındaysa hata verir.
    """
    if not is_inside_sandbox():
        raise PermissionError(
            f"🚫 Sandbox dışı subprocess denemesi tespit edildi! Komut: {' '.join(cmd)}"
        )
    return subprocess.run(cmd, **kwargs)


def verify_docker_installation() -> bool:
    """Docker mevcut mu kontrol et."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # Manuel test
    if not verify_docker_installation():
        sys.exit("[⚠️] Docker yüklü değil. Lütfen Docker Desktop kurun.")

    print("[✅] Docker bulundu, sandbox testi başlıyor...")
    out = run_in_sandbox("python --version")
    print("[✅] Sandbox çıktı:", out)
