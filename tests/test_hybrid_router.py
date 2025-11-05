# tests/test_hybrid_router.py
import pytest
import asyncio
from multiai.core.hybrid_router import LLM

@pytest.mark.asyncio
async def test_llm_router_basic():
    """Test basic router functionality"""
    llm = LLM()

    # Test safe_json
    result = llm.safe_json('{"test": "value"}')
    assert result == {"test": "value"}

    # Test JSON with markdown
    result = llm.safe_json('```json\n{"code": true}\n```')
    assert result == {"code": True}

@pytest.mark.asyncio  
async def test_llm_complete_smoke():
    """Smoke test for complete method"""
    llm = LLM()

    # This should not crash; during Sprint-0 it will short-circuit
    try:
        await llm.complete("Hello, world!")
        assert False, "Expected an exception due to Sprint-0 budget short-circuit"
    except Exception as e:
        # Expected until providers are configured
        msg = str(e)
        assert ("Budget exceeded" in msg) or ("Policy violation" in msg)