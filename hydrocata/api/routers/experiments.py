from fastapi import APIRouter, Depends, HTTPException
from hydrocata.core.schemas import (
    ExperimentInput,
    ExperimentOutput,
    RecommendationOutput,
)
from hydrocata.storage.database_storage import DatabaseStorage
from hydrocata.optimization.bayesian import BayesianOptimizer
from typing import List
from fastapi.responses import JSONResponse

router = APIRouter()

# Shared database storage instance
_storage = DatabaseStorage()


def get_storage():
    """Provide the shared DatabaseStorage instance."""
    return _storage


def get_optimizer():
    """Provide a new BayesianOptimizer instance."""
    return BayesianOptimizer()


@router.post("/record", response_model=ExperimentOutput)
async def record_experiment(
    experiment: ExperimentInput,
    storage: DatabaseStorage = Depends(get_storage),
    optimizer: BayesianOptimizer = Depends(get_optimizer),
):
    """Record a new experimental result (x1, hydrogen production rate)."""
    try:
        await storage.add_experiment(experiment.x1, experiment.hydrogen_rate)
        optimizer.update_data(experiment.x1, experiment.hydrogen_rate)
        return ExperimentOutput(
            x1=experiment.x1, hydrogen_rate=experiment.hydrogen_rate
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record experiment: {str(e)}"
        )


@router.get("/recommend", response_model=RecommendationOutput)
async def recommend_next(optimizer: BayesianOptimizer = Depends(get_optimizer)):
    """Recommend the next x1 value using Bayesian optimization."""
    try:
        next_x1 = optimizer.recommend()
        return RecommendationOutput(x1=next_x1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recommend: {str(e)}")


@router.get("/experiments", response_model=List[ExperimentOutput])
async def list_experiments(storage: DatabaseStorage = Depends(get_storage)):
    """List all recorded experiments."""
    try:
        experiments = await storage.get_experiments()
        return [ExperimentOutput(x1=x1, hydrogen_rate=rate) for x1, rate in experiments]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list experiments: {str(e)}"
        )


@router.get("/all_experiments", response_model=List[ExperimentOutput])
async def list_all_experiments(storage: DatabaseStorage = Depends(get_storage)):
    """List all recorded experiments (alternative endpoint)."""
    try:
        experiments = await storage.get_experiments()
        return [ExperimentOutput(x1=x1, hydrogen_rate=rate) for x1, rate in experiments]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list all experiments: {str(e)}"
        )


@router.delete("/experiments")
async def delete_all_experiments(storage: DatabaseStorage = Depends(get_storage)):
    """Delete all recorded experiments."""
    try:
        await storage.delete_all_experiments()
        return JSONResponse(
            content={"message": "All experiments deleted"}, status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete all experiments: {str(e)}"
        )
