from multiai.manifest.schema import Manifest, Artifact, ArtifactType
def test_manifest():
    m = Manifest(sprint_id="s1", sprint_purpose="test", artifacts=[
        Artifact(artifact_id="file:src/main.py", type=ArtifactType.CODE, path="src/main.py", purpose="entry")
    ])
    assert m.sprint_id == "s1"
