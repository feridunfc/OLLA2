# tests/test_determinism.py
from multiai.core.deterministic_validator import DeterministicValidator

class TestDeterministicValidator:
    def test_compute_manifest_hash_determinism(self):
        v = DeterministicValidator()
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "b": 2, "a": 1}
        assert v.compute_manifest_hash(data1) == v.compute_manifest_hash(data2)

    def test_manifest_with_hash(self):
        v = DeterministicValidator()
        sprint_data = {"sprint_id": "test-123", "goal": "Test sprint", "artifacts": ["code.py", "test.py"]}
        m = v.create_sprint_manifest_with_hash(sprint_data)
        assert "expected_sha256" in m
        recomputed = v.compute_manifest_hash({
            "sprint_id": "test-123",
            "goal": "Test sprint",
            "artifacts": ["code.py", "test.py"],
            "version": "v1",
            "hash_algorithm": "SHA-256"
        })
        assert m["expected_sha256"] == recomputed