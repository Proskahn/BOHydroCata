from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql import select, delete
from typing import List, Dict, Any
import aiosqlite
import logging
import os
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Base = declarative_base()


class DuplicateResultError(Exception):
    """Exception raised when a duplicate variables value is replaced."""

    pass


class Experiment(Base):
    """SQLAlchemy model for experiments."""

    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    comments = Column(String, nullable=True)
    variables = relationship("Variable", back_populates="experiment")
    objectives = relationship("Objective", back_populates="experiment")
    results = relationship("Result", back_populates="experiment")


class Variable(Base):
    """SQLAlchemy model for design variables."""

    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    name = Column(String, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    experiment = relationship("Experiment", back_populates="variables")


class Objective(Base):
    """SQLAlchemy model for optimization objectives."""

    __tablename__ = "objectives"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    name = Column(String, nullable=False)
    experiment = relationship("Experiment", back_populates="objectives")


class Result(Base):
    """SQLAlchemy model for experimental results."""

    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    variables = Column(String, nullable=False)  # JSON string of variable values
    objective_value = Column(Float, nullable=False)
    experiment = relationship("Experiment", back_populates="results")


class DatabaseStorage:
    """Database-backed storage for experimental results using SQLite."""

    def __init__(self, db_path: str = "sqlite:///experiments.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.engine = create_engine(db_path, echo=False, pool_size=5, max_overflow=10)
        self.async_engine = create_async_engine(
            db_path.replace("sqlite:///", "sqlite+aiosqlite:///"), echo=False
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.AsyncSessionLocal = sessionmaker(
            bind=self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_experiment(self, name: str, comments: str = None) -> None:
        """Create a new experiment with a unique name."""
        async with self.AsyncSessionLocal() as session:
            try:
                existing = await session.execute(
                    select(Experiment).filter_by(name=name)
                )
                if existing.scalars().first():
                    raise ValueError(f"Experiment '{name}' already exists")
                experiment = Experiment(name=name, comments=comments)
                session.add(experiment)
                await session.commit()
                logger.debug(f"Created experiment: {name}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create experiment: {str(e)}")
                raise

    async def add_variable(
        self,
        experiment_name: str,
        name: str,
        lower_bound: float = None,
        upper_bound: float = None,
    ) -> None:
        """Add a design variable to an experiment."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")
                variable = Variable(
                    experiment_id=experiment.id,
                    name=name,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                )
                session.add(variable)
                await session.commit()
                logger.debug(
                    f"Added variable '{name}' to experiment '{experiment_name}'"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add variable: {str(e)}")
                raise

    async def add_objective(self, experiment_name: str, name: str) -> None:
        """Add an optimization objective to an experiment."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")
                objective = Objective(experiment_id=experiment.id, name=name)
                session.add(objective)
                await session.commit()
                logger.debug(
                    f"Added objective '{name}' to experiment '{experiment_name}'"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add objective: {str(e)}")
                raise

    async def add_experiment_result(
        self, experiment_name: str, variables: Dict[str, float], objective_value: float
    ) -> None:
        """Add an experimental result to an experiment, replacing if variables exist."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")

                # Validate variable bounds
                db_variables = await session.execute(
                    select(Variable).filter_by(experiment_id=experiment.id)
                )
                db_variables = db_variables.scalars().all()
                variable_map = {v.name: v for v in db_variables}

                for var_name, var_value in variables.items():
                    if var_name not in variable_map:
                        raise ValueError(
                            f"Variable '{var_name}' not defined for experiment '{experiment_name}'"
                        )
                    variable = variable_map[var_name]
                    lower = (
                        variable.lower_bound
                        if variable.lower_bound is not None
                        else float("-inf")
                    )
                    upper = (
                        variable.upper_bound
                        if variable.upper_bound is not None
                        else float("inf")
                    )
                    if not (lower <= var_value <= upper):
                        raise ValueError(
                            f"Variable '{var_name}' value {var_value} is outside bounds [{lower}, {upper}]"
                        )

                # Convert variables dict to JSON string
                variables_json = json.dumps(variables)

                # Check for existing result
                existing_result = await session.execute(
                    select(Result).filter_by(
                        experiment_id=experiment.id, variables=variables_json
                    )
                )
                existing_result = existing_result.scalars().first()
                if existing_result:
                    existing_result.objective_value = objective_value
                    await session.commit()
                    logger.debug(
                        f"Replaced result: variables={variables_json}, objective_value={objective_value} for experiment '{experiment_name}'"
                    )
                    raise DuplicateResultError(
                        f"Duplicate variables {variables} found for experiment '{experiment_name}'. Replaced with objective_value={objective_value}."
                    )

                result = Result(
                    experiment_id=experiment.id,
                    variables=variables_json,
                    objective_value=objective_value,
                )
                session.add(result)
                await session.commit()
                logger.debug(
                    f"Added result: variables={variables_json}, objective_value={objective_value} to experiment '{experiment_name}'"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to add result: {str(e)}")
                raise

    async def delete_experiment_result(
        self, experiment_name: str, variables: Dict[str, float]
    ) -> None:
        """Delete a specific result for an experiment based on variables."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")

                variables_json = json.dumps(variables)
                result = await session.execute(
                    select(Result).filter_by(
                        experiment_id=experiment.id, variables=variables_json
                    )
                )
                result = result.scalars().first()
                if not result:
                    raise ValueError(
                        f"Result with variables {variables} not found for experiment '{experiment_name}'"
                    )

                await session.execute(
                    delete(Result).filter_by(
                        experiment_id=experiment.id, variables=variables_json
                    )
                )
                await session.commit()
                logger.debug(
                    f"Deleted result: variables={variables_json} for experiment '{experiment_name}'"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete result: {str(e)}")
                raise

    async def list_experiments(self) -> List[Dict[str, str]]:
        """List all experiment names and their comments."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiments = await session.execute(
                    select(Experiment.name, Experiment.comments)
                )
                experiments = experiments.fetchall()
                logger.debug(f"Retrieved {len(experiments)} experiments")
                return [
                    {"name": name, "comments": comments}
                    for name, comments in experiments
                ]
            except Exception as e:
                logger.error(f"Failed to list experiments: {str(e)}")
                raise

    async def get_experiments(self, experiment_name: str) -> List[Dict[str, Any]]:
        """Retrieve all results for an experiment."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")
                result = await session.execute(
                    select(Result.variables, Result.objective_value).filter_by(
                        experiment_id=experiment.id
                    )
                )
                experiments = result.fetchall()
                logger.debug(
                    f"Retrieved {len(experiments)} results for experiment '{experiment_name}'"
                )
                return [
                    {
                        "variables": json.loads(variables),
                        "objective_value": float(objective_value),
                    }
                    for variables, objective_value in experiments
                ]
            except Exception as e:
                logger.error(f"Failed to get experiments: {str(e)}")
                raise

    async def get_experiment_details(self, experiment_name: str) -> dict:
        """Retrieve details of an experiment, including variables and objectives."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")

                variables = await session.execute(
                    select(Variable).filter_by(experiment_id=experiment.id)
                )
                variables = variables.scalars().all()
                objectives = await session.execute(
                    select(Objective).filter_by(experiment_id=experiment.id)
                )
                objectives = objectives.scalars().all()
                results = await session.execute(
                    select(Result).filter_by(experiment_id=experiment.id)
                )
                results = results.scalars().all()

                return {
                    "name": experiment.name,
                    "comments": experiment.comments,
                    "variables": [
                        {
                            "name": v.name,
                            "lower_bound": v.lower_bound,
                            "upper_bound": v.upper_bound,
                        }
                        for v in variables
                    ],
                    "objectives": [{"name": o.name} for o in objectives],
                    "results": [
                        {
                            "variables": json.loads(r.variables),
                            "objective_value": r.objective_value,
                        }
                        for r in results
                    ],
                }
            except Exception as e:
                logger.error(f"Failed to get experiment details: {str(e)}")
                raise

    async def delete_experiment(self, experiment_name: str) -> None:
        """Delete an experiment and its associated data."""
        async with self.AsyncSessionLocal() as session:
            try:
                experiment = await session.execute(
                    select(Experiment).filter_by(name=experiment_name)
                )
                experiment = experiment.scalars().first()
                if not experiment:
                    raise ValueError(f"Experiment '{experiment_name}' not found")

                await session.execute(
                    delete(Result).filter_by(experiment_id=experiment.id)
                )
                await session.execute(
                    delete(Variable).filter_by(experiment_id=experiment.id)
                )
                await session.execute(
                    delete(Objective).filter_by(experiment_id=experiment.id)
                )
                await session.execute(delete(Experiment).filter_by(id=experiment.id))
                await session.commit()
                logger.debug(f"Deleted experiment '{experiment_name}'")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete experiment: {str(e)}")
                raise
