import pytest
import asyncio
from multiai.core.enhanced_llm_router import EnhancedLLMRouter

@pytest.mark.asyncio
async def test_code_path_smoke():
    router = EnhancedLLMRouter()
    res = await router.route_task("code_generation", {"requirements": "Write a Python function that adds two numbers."})
    assert "status" in res

@pytest.mark.asyncio
async def test_research_fallback_smoke():
    router = EnhancedLLMRouter()
    res = await router.route_task("research", {"topic": "LLM architectures", "depth": "short"})
    assert "status" in res

@pytest.mark.asyncio
async def test_search_fallback_smoke():
    router = EnhancedLLMRouter()
    res = await router.route_task("web_search", {"query": "What is vector DB?", "max_results": 3})
    assert "status" in res
