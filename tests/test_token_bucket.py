from multiai.core.token_bucket import TokenBucket
def test_bucket_basic():
    b = TokenBucket(rate=10, capacity=2)
    assert b.allow() is True
    assert b.allow() is True
    assert b.allow() is False
