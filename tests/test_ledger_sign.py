from multiai.core.ledger_sign import sign_manifest, verify_manifest
def test_sign_verify():
    m={"test":"ok"}
    sig=sign_manifest(m)
    assert verify_manifest(m,sig)
