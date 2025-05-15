from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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
    variables: Dict[str, float] = Field(..., min_length=1)
    objective_value: float = Field(..., gt=0.0)

    class Config:
        json_schema_extra = {
            "example": {
                "variables": {"variable_name_1": 0.5, "variable_name_2": 1.0},
                "objective_value": 1.0,
            }
        }


class DeleteResultInput(BaseModel):
    variables: Dict[str, float] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "variables": {"variable_name_1": 0.5, "variable_name_2": 1.0},
            }
        }


class ExperimentListOutput(BaseModel):
    experiments: List[Dict[str, Optional[str]]]


class ExperimentOutput(BaseModel):
    name: str
    comments: Optional[str]
    variables: List[
        Dict[str, Any]
    ]  # name 为 str，lower_bound/upper_bound 为 float 或 None
    objectives: List[Dict[str, str]]
    results: List[
        Dict[str, Any]
    ]  # variables 为 Dict[str, float]，objective_value 为 float

    class Config:
        json_schema_extra = {
            "example": {
                "name": "test_exp",
                "comments": "Test experiment",
                "variables": [
                    {"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
                    {"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
                ],
                "objectives": [{"name": "hydrogen_production_rate"}],
                "results": [
                    {
                        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
                        "objective_value": 100.0,
                    }
                ],
            }
        }


class RecommendationOutput(BaseModel):
    variables: Dict[str, float] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "variables": {"variable_name_1": 0.5, "variable_name_2": 1.0},
            }
        }
