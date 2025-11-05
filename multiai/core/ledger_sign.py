# multiai/core/ledger_sign.py
import os
import base64
import logging
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

class LedgerSigner:
    """ECDSA signing for ledger entries with KMS/ENV support"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        priv_key_pem = os.getenv('MULTIAI_PRIV_PEM')
        pub_key_pem = os.getenv('MULTIAI_PUB_PEM')

        if priv_key_pem and pub_key_pem:
            try:
                self.private_key = serialization.load_pem_private_key(
                    priv_key_pem.encode(),
                    password=None,
                    backend=default_backend()
                )
                self.public_key = serialization.load_pem_public_key(
                    pub_key_pem.encode(),
                    backend=default_backend()
                )
                self.logger.info("Loaded ECDSA keys from environment")
                return
            except Exception as e:
                self.logger.error(f"Failed to load keys from ENV: {e}")
                raise

        # Development: Generate new keys
        self.logger.warning("Generating new ECDSA keys for development")
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()
        self._save_dev_keys()

    def _save_dev_keys(self):
        try:
            priv_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            pub_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            os.makedirs('keys', exist_ok=True)
            with open('keys/private_dev.pem', 'wb') as f:
                f.write(priv_pem)
            with open('keys/public_dev.pem', 'wb') as f:
                f.write(pub_pem)
            self.logger.info("Saved development keys to keys/ directory")
        except Exception as e:
            self.logger.warning(f"Could not save dev keys: {e}")

    def sign_data(self, data: str) -> str:
        if not self.private_key:
            raise Exception("No private key available for signing")
        signature = self.private_key.sign(
            data.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, data: str, signature: str) -> bool:
        if not self.public_key:
            raise Exception("No public key available for verification")
        try:
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                data.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            self.logger.error(f"Signature verification error: {e}")
            return False

    def get_public_key_fingerprint(self) -> str:
        pub_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(pub_pem).hexdigest()[:16]

# Singleton instance
ledger_signer = LedgerSigner()