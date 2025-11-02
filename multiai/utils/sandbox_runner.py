# multiai/core/ledger_sign.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from pathlib import Path
import base64, json, os
from typing import Optional

KEY_DIR = Path("keys")
PRIV_PATH = KEY_DIR / "private.pem"
PUB_PATH = KEY_DIR / "public.pem"

def _ensure_keys():
    """
    Ensure keys exist locally (development fallback only).
    Production: use MULTIAI_PRIV_PEM / MULTIAI_PUB_PEM env secrets or KMS.
    """
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if not PRIV_PATH.exists() or not PUB_PATH.exists():
        # Generate ephemeral keypair for local dev only
        priv = ec.generate_private_key(ec.SECP256R1())
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub = priv.public_key()
        pub_pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        PRIV_PATH.write_bytes(priv_pem)
        PUB_PATH.write_bytes(pub_pem)

def load_private_pem() -> bytes:
    """
    Load private key from: (1) MULTIAI_PRIV_PEM env (base64 or raw), (2) keys/private.pem file.
    Raise if not available.
    """
    env_val = os.getenv("MULTIAI_PRIV_PEM")
    if env_val:
        # If base64 encoded, attempt decode, else assume raw PEM
        try:
            return base64.b64decode(env_val)
        except Exception:
            return env_val.encode("utf-8")
    if PRIV_PATH.exists():
        return PRIV_PATH.read_bytes()
    raise RuntimeError("Private key not found. Set MULTIAI_PRIV_PEM or place keys/private.pem (dev only).")

def load_public_pem() -> bytes:
    env_val = os.getenv("MULTIAI_PUB_PEM")
    if env_val:
        try:
            return base64.b64decode(env_val)
        except Exception:
            return env_val.encode("utf-8")
    if PUB_PATH.exists():
        return PUB_PATH.read_bytes()
    raise RuntimeError("Public key not found. Set MULTIAI_PUB_PEM or place keys/public.pem (dev only).")

def sign_manifest(manifest_input) -> str:
    """
    Accepts either bytes (already serialized) or a dict/object (will JSON serialize deterministically).
    Returns base64(signature).
    """
    if isinstance(manifest_input, (bytes, bytearray)):
        manifest_bytes = bytes(manifest_input)
    else:
        # deterministic json serialization
        manifest_bytes = json.dumps(manifest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    # Ensure keys exist or environment has them
    _ensure_keys()
    priv_pem = load_private_pem()
    key = serialization.load_pem_private_key(priv_pem, password=None)
    sig = key.sign(manifest_bytes, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode("ascii")

def verify_manifest(manifest_input, signature_b64: str) -> bool:
    if isinstance(manifest_input, (bytes, bytearray)):
        manifest_bytes = bytes(manifest_input)
    else:
        manifest_bytes = json.dumps(manifest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    pub_pem = load_public_pem()
    pub = serialization.load_pem_public_key(pub_pem)
    try:
        pub.verify(base64.b64decode(signature_b64), manifest_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
