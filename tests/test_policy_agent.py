from multiai.core.policy_agent import policy_agent
def test_policy_loaded():
    assert policy_agent.routing_policy is not None
