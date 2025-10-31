from pathlib import Path
import hashlib, sqlite3
from typing import Tuple, List, Dict
from ..manifest.schema import Manifest
from ..config import settings
DB = Path(settings.ledger_path)
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""): h.update(ch)
    return h.hexdigest()
def validate_against_manifest(workdir: Path, manifest: Manifest) -> Tuple[bool, List[Dict]]:
    mismatches, ok = [], True
    for art in manifest.artifacts:
        if not art.sha256:
            ok = False; mismatches.append({"artifact_id": art.artifact_id, "reason": "no_expected_hash"}); continue
        p = (workdir / art.path)
        if not p.exists():
            ok = False; mismatches.append({"artifact_id": art.artifact_id, "reason": "file_missing"}); continue
        actual = sha256_of(p)
        if actual != art.sha256:
            ok = False; mismatches.append({"artifact_id": art.artifact_id, "reason":"hash_mismatch","expected":art.sha256,"actual":actual})
    return ok, mismatches
def record_sprint(sprint_id: str, manifest: Manifest, workdir: Path):
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS sprint_artifact(
          sprint_id TEXT, artifact_id TEXT, path TEXT, expected_hash TEXT, actual_hash TEXT,
          recorded_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (sprint_id, artifact_id)
        ) WITHOUT ROWID;""")
        for art in manifest.artifacts:
            p = workdir / art.path
            actual = sha256_of(p) if p.exists() else None
            c.execute("INSERT OR REPLACE INTO sprint_artifact(sprint_id,artifact_id,path,expected_hash,actual_hash) VALUES (?,?,?,?,?)",
                      (sprint_id, art.artifact_id, art.path, art.sha256, actual))
        c.commit()
