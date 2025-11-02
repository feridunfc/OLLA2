from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from pathlib import Path
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
    """Verilen manifest'i imzalar (timestamp eklemeden)."""
    _ensure_keys()
    private_key = serialization.load_pem_private_key(PRIV_PATH.read_bytes(), None)
    data = json.dumps(manifest, sort_keys=True).encode()
    sig = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode()

def verify_manifest(manifest: dict, sig_b64: str) -> bool:
    """Manifest imzasını doğrular."""
    _ensure_keys()
    pub = serialization.load_pem_public_key(PUB_PATH.read_bytes())
    try:
        data = json.dumps(manifest, sort_keys=True).encode()
        pub.verify(base64.b64decode(sig_b64), data, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
