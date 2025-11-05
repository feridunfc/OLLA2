# tests/test_ledger_sign.py
from multiai.core.ledger_sign import LedgerSigner

class TestLedgerSigner:
    def test_key_generation(self):
        signer = LedgerSigner()
        assert signer.private_key is not None
        assert signer.public_key is not None

    def test_sign_and_verify(self):
        signer = LedgerSigner()
        data = "test manifest data"
        signature = signer.sign_data(data)
        assert signer.verify_signature(data, signature) is True

    def test_tampered_data(self):
        signer = LedgerSigner()
        data = "original data"
        signature = signer.sign_data(data)
        tampered = "tampered data"
        assert signer.verify_signature(tampered, signature) is False

    def test_public_key_fingerprint(self):
        signer = LedgerSigner()
        fp = signer.get_public_key_fingerprint()
        assert isinstance(fp, str) and len(fp) == 16