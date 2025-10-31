from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
class ArtifactType(str, Enum): CODE="code"; TEST="test"; DOCUMENTATION="documentation"; CONFIG="config"
class Artifact(BaseModel):
    artifact_id:str; type:ArtifactType; path:str; purpose:str
    dependencies:List[str]=Field(default_factory=list); expected_behavior:str=""; sha256:str=""
class Manifest(BaseModel):
    sprint_id:str; sprint_purpose:str; artifacts:List[Artifact]; created_at:Optional[str]=None
