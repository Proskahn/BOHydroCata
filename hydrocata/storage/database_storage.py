from sqlalchemy import create_engine, Column, Float, Integer, select, delete
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import List, Tuple
import aiosqlite
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Experiment(Base):
    """SQLAlchemy model for experiments."""

    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    x1 = Column(Float, nullable=False)
    hydrogen_rate = Column(Float, nullable=False)


class DatabaseStorage:
    """Database-backed storage for experimental results using SQLite."""

    def __init__(self, db_path: str = "sqlite:///experiments.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        # Sync engine for initialization
        self.engine = create_engine(db_path, echo=False)
        # Async engine for operations
        self.async_engine = create_async_engine(
            db_path.replace("sqlite:///", "sqlite+aiosqlite:///"), echo=False
        )
        # Create tables
        Base.metadata.create_all(self.engine)
        # Session factory
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.AsyncSessionLocal = sessionmaker(
            bind=self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def add_experiment(self, x1: float, hydrogen_rate: float) -> None:
        """Add a new experimental result to the database."""
        if not (0.0 <= x1 <= 1.0):
            raise ValueError("x1 must be between 0 and 1")
        if hydrogen_rate <= 0.0:
            raise ValueError("Hydrogen production rate must be positive")

        try:
            async with self.AsyncSessionLocal() as session:
                experiment = Experiment(x1=x1, hydrogen_rate=hydrogen_rate)
                session.add(experiment)
                await session.commit()
                logger.debug(
                    f"Added experiment: x1={x1}, hydrogen_rate={hydrogen_rate}"
                )
        except Exception as e:
            logger.error(f"Failed to add experiment: {str(e)}")
            raise

    async def get_experiments(self) -> List[Tuple[float, float]]:
        """Retrieve all stored experiments."""
        try:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Experiment.x1, Experiment.hydrogen_rate)
                )
                experiments = result.fetchall()
                logger.debug(f"Retrieved {len(experiments)} experiments")
                return [
                    (float(x1), float(hydrogen_rate))
                    for x1, hydrogen_rate in experiments
                ]
        except Exception as e:
            logger.error(f"Failed to get experiments: {str(e)}")
            raise

    async def delete_all_experiments(self) -> None:
        """Delete all experiments from the database."""
        try:
            async with self.AsyncSessionLocal() as session:
                await session.execute(delete(Experiment))
                await session.commit()
                logger.debug("Deleted all experiments")
        except Exception as e:
            logger.error(f"Failed to delete all experiments: {str(e)}")
            raise
