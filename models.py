from __future__ import annotations

from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high"]
RiskType = Literal["liability", "termination", "payment", "confidentiality", "compliance"]
TaskName = Literal["easy", "medium", "hard"]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    clause: str = Field(..., min_length=1, description="The contract clause to analyze.")
    contract_type: str = Field(..., min_length=1, description="Type of agreement containing the clause.")
    jurisdiction: str = Field(..., min_length=1, description="Jurisdiction relevant to the clause.")


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    risk_level: Optional[RiskLevel] = Field(default=None, description="Predicted risk level.")
    risk_type: Optional[RiskType] = Field(default=None, description="Predicted legal risk category.")
    rewrite: str = Field(default="", description="Safer contract language.")
    reason: str = Field(default="", description="Explanation of the identified legal risk.")
    explanation: str = Field(default="", description="In-depth legal breakdown.")
    impact: str = Field(default="", description="Potential business/legal impact.")
    confidence: int = Field(default=85, ge=0, le=100, description="Analysis confidence score.")
    highlights_red: list[str] = Field(default_factory=list, description="High risk phrases.")
    highlights_yellow: list[str] = Field(default_factory=list, description="Medium risk phrases.")
    phrases: Dict[str, str] = Field(default_factory=dict, description="Map of phrases to their specific risk descriptions.")



class Reward(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(..., ge=0.0, le=1.0, description="Dense reward clipped to [0.0, 1.0].")


class TaskSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    task: TaskName
    observation: Observation
    ground_truth: Action
