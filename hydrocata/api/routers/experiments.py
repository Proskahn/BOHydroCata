from fastapi import APIRouter, Depends, HTTPException
from hydrocata.core.schemas import ExperimentInput, VariableInput, ObjectiveInput, ResultInput, DeleteResultInput, ExperimentOutput, ExperimentListOutput, ExperimentResultOutput, RecommendationOutput
from hydrocata.storage.database_storage import DatabaseStorage
from hydrocata.optimization.bayesian import BayesianOptimizer
from typing import List
from fastapi.responses import JSONResponse

router = APIRouter()

def get_storage():
    """Provide a new DatabaseStorage instance."""
    return DatabaseStorage(db_path="sqlite:///experiments.db")

def get_optimizer():
    """Provide a new BayesianOptimizer instance."""
    return BayesianOptimizer()

@router.post("/experiments", response_model=ExperimentInput)
async def create_experiment(
    experiment: ExperimentInput,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Create a new experiment."""
    try:
        await storage.create_experiment(experiment.name, experiment.comments)
        return experiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")

@router.post("/experiments/{experiment_name}/variables", response_model=VariableInput)
async def add_variable(
    experiment_name: str,
    variable: VariableInput,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Add a design variable to an experiment."""
    try:
        await storage.add_variable(experiment_name, variable.name, variable.lower_bound, variable.upper_bound)
        return variable
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add variable: {str(e)}")

@router.post("/experiments/{experiment_name}/objectives", response_model=ObjectiveInput)
async def add_objective(
    experiment_name: str,
    objective: ObjectiveInput,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Add an optimization objective to an experiment."""
    try:
        await storage.add_objective(experiment_name, objective.name)
        return objective
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add objective: {str(e)}")

@router.post("/experiments/{experiment_name}/results", response_model=ResultInput)
async def record_experiment(
    experiment_name: str,
    result: ResultInput,
    storage: DatabaseStorage = Depends(get_storage),
    optimizer: BayesianOptimizer = Depends(get_optimizer)
):
    """Record an experimental result."""
    try:
        await storage.add_experiment_result(experiment_name, result.x1, result.objective_value)
        optimizer.update_data(result.x1, result.objective_value)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record experiment: {str(e)}")

@router.delete("/experiments/{experiment_name}/results")
async def delete_experiment_result(
    experiment_name: str,
    result: DeleteResultInput,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Delete a specific result for an experiment."""
    try:
        await storage.delete_experiment_result(experiment_name, result.x1)
        return JSONResponse(content={"message": f"Result x1={result.x1} deleted for experiment '{experiment_name}'"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")

@router.get("/experiments", response_model=ExperimentListOutput)
async def list_experiments(
    storage: DatabaseStorage = Depends(get_storage)
):
    """List all experiment names and their comments."""
    try:
        experiments = await storage.list_experiments()
        return ExperimentListOutput(experiments=experiments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")

@router.get("/experiments/{experiment_name}/recommend", response_model=RecommendationOutput)
async def recommend_next(
    experiment_name: str,
    storage: DatabaseStorage = Depends(get_storage),
    optimizer: BayesianOptimizer = Depends(get_optimizer)
):
    """Recommend the next x1 value using Bayesian optimization."""
    try:
        experiments = await storage.get_experiments(experiment_name)
        for x1, objective_value in experiments:
            optimizer.update_data(x1, objective_value)
        next_x1 = optimizer.recommend()
        return RecommendationOutput(x1=next_x1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recommend: {str(e)}")

@router.get("/experiments/{experiment_name}", response_model=ExperimentOutput)
async def get_experiment(
    experiment_name: str,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Retrieve all data for an experiment."""
    try:
        details = await storage.get_experiment_details(experiment_name)
        return ExperimentOutput(**details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve experiment: {str(e)}")

@router.delete("/experiments/{experiment_name}")
async def delete_experiment(
    experiment_name: str,
    storage: DatabaseStorage = Depends(get_storage)
):
    """Delete an experiment."""
    try:
        await storage.delete_experiment(experiment_name)
        return JSONResponse(content={"message": f"Experiment '{experiment_name}' deleted"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete experiment: {str(e)}")