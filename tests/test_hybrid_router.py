
import pytest
from multiai.core.hybrid_intelligence_router import HybridIntelligenceRouter

@pytest.mark.asyncio
async def test_router_local_fallback():
    router = HybridIntelligenceRouter()
    # coding -> local (because no cloud keys in test env)
    res = await router.route_task("coding", "write simple function to add numbers")
    assert isinstance(res, str)
