import pytest, asyncio, tempfile, json
from pathlib import Path
from multiai.schema.enhanced_manifest import SprintManifest, Artifact, ArtifactType, RiskLevel, RiskAssessment
from multiai.core.deterministic_ledger import DeterministicLedger
from multiai.core.deterministic_validator import DeterministicValidator
from multiai.core.manifest_processor import ManifestProcessor

@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def artifact():
    return Artifact(
        artifact_id="test_comp", type=ArtifactType.CODE, path="src/t.py",
        purpose="test", expected_behavior="pass", acceptance_criteria=["t1"],
        risk_assessment=RiskAssessment(level=RiskLevel.LOW, score=0.1),
        estimated_effort=2, priority=1
    )

@pytest.fixture
def manifest(artifact):
    return SprintManifest(
        sprint_id="s2025", sprint_purpose="test", artifacts=[artifact],
        dependency_graph={"test_comp": []}, overall_risk=RiskAssessment(level=RiskLevel.LOW, score=0.1)
    )

def test_artifact_hash(artifact):
    h1, h2 = artifact.calculate_expected_hash(), artifact.calculate_expected_hash()
    assert h1 == h2 and len(h1) == 64

def test_manifest_hash(manifest):
    h1, h2 = manifest.calculate_manifest_hash(), manifest.calculate_manifest_hash()
    assert h1 == h2 and len(h1) == 64

def test_ledger(tmp_path, manifest):
    ledger = DeterministicLedger(tmp_path / "l.db")
    ledger_id = ledger.record_sprint_manifest(manifest.sprint_id, manifest.calculate_manifest_hash(), None, "tester")
    assert ledger_id
    assert ledger.verify_sprint_integrity(manifest.sprint_id)["valid"]

def test_validator(tmp_path, manifest, artifact):
    ledger = DeterministicLedger(tmp_path / "l.db")
    validator = DeterministicValidator(tmp_path, ledger)
    test_file = tmp_path / artifact.path
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("def t(): return 1")

    # 🔧 hash'i gerçekten ata:
    artifact.expected_sha256 = validator.compute_file_hash(test_file)

    result = validator.validate_artifact(artifact, manifest)
    assert result["validation_passed"] is True


@pytest.mark.asyncio
async def test_manifest_processor(tmp_path, manifest):
    processor = ManifestProcessor(tmp_path)
    for artifact in manifest.artifacts:
        test_file = tmp_path / artifact.path
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# impl")
    result = await processor.process_manifest(manifest)
    assert result["success"] is True
    assert result["validation_results"]["overall_validation"] is True

def test_dependency_cycle(manifest):
    manifest = manifest.model_copy(update={"dependency_graph": {"test_comp": ["test_comp"]}})
    assert manifest.validate_dependencies() is False
