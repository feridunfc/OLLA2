from multiai.agents.critic_agent import CriticAgent

def test_analyze_diff_basic():
    agent = CriticAgent()
    old = "print('hello')\n"
    new = "print('hello world')\n"
    res = agent.analyze_diff(old, new)
    assert "impact" in res and "severity" in res and "recommendations" in res
    assert res["status"] == "success"

def test_analyze_diff_security():
    agent = CriticAgent()
    old = "x=1\n"
    new = "x = eval('1+1')\n"
    res = agent.analyze_diff(old, new)
    assert any(i.get("type") == "security" for i in res.get("security_issues", []))
    assert res["requires_approval"] is True
