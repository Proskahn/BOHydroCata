from typing import List, Optional

from pydantic import BaseModel, Field


class ExperimentInput(BaseModel):
    name: str = Field(..., min_length=1)
    comments: Optional[str] = None


class VariableInput(BaseModel):
    name: str = Field(..., min_length=1)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ObjectiveInput(BaseModel):
    name: str = Field(..., min_length=1)


class ResultInput(BaseModel):
    x1: float = Field(..., ge=0.0)
    objective_value: float = Field(..., gt=0.0)


class ExperimentOutput(BaseModel):
    name: str
    comments: Optional[str]
    variables: List[dict]
    objectives: List[dict]
    results: List[dict]


class ExperimentResultOutput(BaseModel):
    x1: float
    objective_value: float


class RecommendationOutput(BaseModel):
    x1: float = Field(..., ge=0.0, le=1.0)
