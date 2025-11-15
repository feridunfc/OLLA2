import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from multiai.core.enhanced_orchestrator import enhanced_orchestrator


async def test_autonomous_sprint():
    """Test autonomous sprint execution"""
    print("🚀 Testing Autonomous Sprint System...")

    test_cases = [
        {
            "goal": "Review and fix authentication module security issues",
            "context": {"priority": "high", "domain": "security"}
        },
        {
            "goal": "Design and test new user management system architecture",
            "context": {"complexity": "high", "domain": "architecture"}
        },
        {
            "goal": "Optimize database queries and add performance tests",
            "context": {"focus": "performance", "domain": "optimization"}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['goal']}")
        print("-" * 50)

        try:
            result = await enhanced_orchestrator.execute_autonomous_sprint(
                test_case["goal"],
                test_case["context"]
            )

            if result["status"] == "success":
                print(f"✅ SUCCESS: Autonomous sprint completed")
                print(f"   Workflow: {' -> '.join(result['workflow'])}")
                print(f"   Performance Score: {result['performance_metrics']['score']:.2f}")
                print(f"   Success Rate: {result['performance_metrics']['success_rate']:.1%}")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"💥 ERROR: {e}")

    # Show learned patterns
    print(f"\n🎓 LEARNING SUMMARY:")
    patterns = enhanced_orchestrator.self_orchestrator.workflow_patterns
    for pattern, count in patterns.items():
        print(f"   {pattern}: {count} executions")


if __name__ == "__main__":
    print("OLLA2 Sprint F - Autonomous System Test")
    print("=" * 60)
    asyncio.run(test_autonomous_sprint())