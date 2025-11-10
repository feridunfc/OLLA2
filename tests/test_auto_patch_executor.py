import asyncio, os
from multiai.core.auto_patch_executor import AutoPatchExecutor

async def _run():
    ex = AutoPatchExecutor(sandbox_enabled=False, run_tests=False)
    fname = "tmp_patch.diff"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("--- a/x\n+++ b/x\n")
    res = await ex.apply_and_test_patch(fname)
    os.remove(fname)
    return res

def test_apply_and_test_patch():
    res = asyncio.run(_run())
    assert "success" in res and "test_results" in res
    assert res["success"] is True
