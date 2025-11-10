from multiai.agents.patch_agent import PatchAgent

def test_generate_patch_basic(tmp_path):
    agent = PatchAgent()
    critic = {"impact": "low", "severity": "low", "recommendations": []}
    old = "print('a')\n"
    new = "print('b')\n"
    res = agent.generate_patch(critic, old, new, "sample.py")
    assert res["status"] == "success"
    assert res["format"] == "unified_diff"
    assert res["patch_file"]
