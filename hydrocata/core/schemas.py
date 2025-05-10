from pydantic import BaseModel, Field


class ExperimentInput(BaseModel):
    """Schema for recording an experimental result."""

    x1: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of LrO2 (between 0 and 1)"
    )
    hydrogen_rate: float = Field(..., gt=0.0, description="Hydrogen production rate")


class ExperimentOutput(BaseModel):
    """Schema for returning a recorded experimental result."""

    x1: float
    hydrogen_rate: float


class RecommendationOutput(BaseModel):
    """Schema for recommending the next x1 value."""

    x1: float = Field(..., ge=0.0, le=1.0, description="Recommended ratio of LrO2")
