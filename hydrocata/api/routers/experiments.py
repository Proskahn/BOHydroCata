from fastapi import APIRouter, Depends, HTTPException, Path
from hydrocata.core.schemas import (
    ExperimentInput,
    VariableInput,
    ObjectiveInput,
    ResultInput,
    DeleteResultInput,
    ExperimentOutput,
    ExperimentListOutput,
    RecommendationOutput,
)
from hydrocata.storage.database_storage import DatabaseStorage
from hydrocata.optimization.bayesian import BayesianOptimizer
from typing import Dict
from fastapi.responses import JSONResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_storage():
    return DatabaseStorage(db_path="sqlite:///experiments.db")


async def get_optimizer(
    experiment_name: str = Path(...), storage: DatabaseStorage = Depends(get_storage)
):
    details = await storage.get_experiment_details(experiment_name)
    logger.debug(f"Experiment details for {experiment_name}: {details}")
    pbounds = {
        var["name"]: (
            var["lower_bound"] if var["lower_bound"] is not None else 0.0,
            var["upper_bound"] if var["upper_bound"] is not None else 1.0,
        )
        for var in details["variables"]
    }
    if not pbounds:
        logger.debug(f"No variables defined for {experiment_name}")
        raise HTTPException(
            status_code=400, detail="No variables defined for experiment"
        )
    try:
        return BayesianOptimizer(pbounds=pbounds)
    except Exception as e:
        logger.error(f"Failed to initialize optimizer for {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize optimizer: {str(e)}"
        )


@router.post("/experiments", response_model=ExperimentInput)
async def create_experiment(
    experiment: ExperimentInput, storage: DatabaseStorage = Depends(get_storage)
):
    try:
        await storage.create_experiment(experiment.name, experiment.comments)
        return experiment
    except Exception as e:
        logger.error(f"Failed to create experiment {experiment.name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create experiment: {str(e)}"
        )


@router.post("/experiments/{experiment_name}/variables", response_model=VariableInput)
async def add_variable(
    experiment_name: str,
    variable: VariableInput,
    storage: DatabaseStorage = Depends(get_storage),
):
    try:
        await storage.add_variable(
            experiment_name, variable.name, variable.lower_bound, variable.upper_bound
        )
        return variable
    except Exception as e:
        logger.error(f"Failed to add variable to {experiment_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add variable: {str(e)}")


@router.post("/experiments/{experiment_name}/objectives", response_model=ObjectiveInput)
async def add_objective(
    experiment_name: str,
    objective: ObjectiveInput,
    storage: DatabaseStorage = Depends(get_storage),
):
    try:
        await storage.add_objective(experiment_name, objective.name)
        return objective
    except Exception as e:
        logger.error(f"Failed to add objective to {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to add objective: {str(e)}"
        )


@router.post("/experiments/{experiment_name}/results", response_model=ResultInput)
async def record_experiment(
    experiment_name: str,
    result: ResultInput,
    storage: DatabaseStorage = Depends(get_storage),
    optimizer: BayesianOptimizer = Depends(get_optimizer),
):
    try:
        await storage.add_experiment_result(
            experiment_name, result.variables, result.objective_value
        )
        optimizer.update_data(result.variables, result.objective_value)
        return result
    except Exception as e:
        logger.error(f"Failed to record result for {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to record experiment: {str(e)}"
        )


@router.delete("/experiments/{experiment_name}/results")
async def delete_experiment_result(
    experiment_name: str,
    result: DeleteResultInput,
    storage: DatabaseStorage = Depends(get_storage),
):
    try:
        await storage.delete_experiment_result(experiment_name, result.variables)
        return JSONResponse(
            content={
                "message": f"Result variables={result.variables} deleted for experiment '{experiment_name}'"
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Failed to delete result for {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete result: {str(e)}"
        )


@router.get("/experiments", response_model=ExperimentListOutput)
async def list_experiments(storage: DatabaseStorage = Depends(get_storage)):
    try:
        experiments = await storage.list_experiments()
        return ExperimentListOutput(experiments=experiments)
    except Exception as e:
        logger.error(f"Failed to list experiments: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list experiments: {str(e)}"
        )


@router.get(
    "/experiments/{experiment_name}/recommend", response_model=RecommendationOutput
)
async def recommend_next(
    experiment_name: str,
    storage: DatabaseStorage = Depends(get_storage),
    optimizer: BayesianOptimizer = Depends(get_optimizer),
):
    try:
        experiments = await storage.get_experiments(experiment_name)
        for experiment in experiments:
            variables = experiment["variables"]
            objective_value = experiment["objective_value"]
            optimizer.update_data(variables, objective_value)
        next_variables = optimizer.recommend()
        return RecommendationOutput(variables=next_variables)
    except Exception as e:
        logger.error(f"Failed to recommend for {experiment_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to recommend: {str(e)}")


@router.get("/experiments/{experiment_name}", response_model=ExperimentOutput)
async def get_experiment(
    experiment_name: str, storage: DatabaseStorage = Depends(get_storage)
):
    try:
        details = await storage.get_experiment_details(experiment_name)
        logger.debug(f"Experiment details retrieved for {experiment_name}: {details}")
        return ExperimentOutput(**details)
    except Exception as e:
        logger.error(f"Failed to retrieve experiment {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve experiment: {str(e)}"
        )


@router.delete("/experiments/{experiment_name}")
async def delete_experiment(
    experiment_name: str, storage: DatabaseStorage = Depends(get_storage)
):
    try:
        await storage.delete_experiment(experiment_name)
        return JSONResponse(
            content={"message": f"Experiment '{experiment_name}' deleted"},
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Failed to delete experiment {experiment_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete experiment: {str(e)}"
        )
