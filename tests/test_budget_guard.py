from multiai.core.budget_guard import budget_guard
def test_budget_status():
    s = budget_guard.status()
    assert "limit" in s
