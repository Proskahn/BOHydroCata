import pytest
import os
from fastapi.testclient import TestClient
from hydrocata.api.main import app
from hydrocata.storage.database_storage import DatabaseStorage, Base
from hydrocata.optimization.bayesian import BayesianOptimizer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import aiosqlite
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a TestClient instance for the FastAPI app
client = TestClient(app)


@pytest.fixture(scope="function")
async def dependencies(tmp_path):
    """Provide DatabaseStorage and BayesianOptimizer for a test, with reliable database cleanup."""
    db_file = tmp_path / f"test_experiments_{id(tmp_path)}.db"
    db_path = f"sqlite:///{db_file}"

    storage = DatabaseStorage(db_path=db_path)
    optimizer = BayesianOptimizer()

    # Initialize database
    engine = create_engine(db_path, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    async_connection = None
    try:
        async_connection = await aiosqlite.connect(str(db_file))
        yield storage, optimizer
    finally:
        try:
            Base.metadata.drop_all(engine)
            engine.dispose()
            if async_connection:
                await async_connection.close()
            if os.path.exists(db_file):
                os.remove(db_file)
                logger.debug(f"Deleted temporary database file: {db_file}")
        except Exception as e:
            logger.error(f"Failed to clean up database file {db_file}: {str(e)}")


@pytest.mark.asyncio
async def test_create_experiment(dependencies, monkeypatch, tmp_path):
    """Test creating a new experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    response = client.post(
        "/api/v1/experiments",
        json={"name": "test_exp", "comments": "Anode catalyst with IrO2 and RuO2"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "test_exp",
        "comments": "Anode catalyst with IrO2 and RuO2",
    }

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp")
        logger.debug("Cleaned up test_exp from test_create_experiment")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp: {str(e)}")


@pytest.mark.asyncio
async def test_add_variable(dependencies, monkeypatch, tmp_path):
    """Test adding a design variable to an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": "test_exp"})

    response = client.post(
        "/api/v1/experiments/test_exp/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "ratio of IrO2",
        "lower_bound": 0.0,
        "upper_bound": 1.0,
    }

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp")
        logger.debug("Cleaned up test_exp from test_add_variable")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp: {str(e)}")


@pytest.mark.asyncio
async def test_add_objective(dependencies, monkeypatch, tmp_path):
    """Test adding an objective to an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": "test_exp2"})

    response = client.post(
        "/api/v1/experiments/test_exp2/objectives",
        json={"name": "hydrogen production rate"},
    )
    assert response.status_code == 200
    assert response.json() == {"name": "hydrogen production rate"}

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp2")
        logger.debug("Cleaned up test_exp2 from test_add_objective")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp2: {str(e)}")


@pytest.mark.asyncio
async def test_record_experiment_result(dependencies, monkeypatch, tmp_path):
    """Test recording an experimental result."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": "test_exp3"})
    client.post(
        "/api/v1/experiments/test_exp3/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )

    response = client.post(
        "/api/v1/experiments/test_exp3/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )
    assert response.status_code == 200
    assert response.json() == {"x1": 0.5, "objective_value": 100.0}

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp3")
        logger.debug("Cleaned up test_exp from test_record_experiment_result")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp3: {str(e)}")


@pytest.mark.asyncio
async def test_delete_experiment_result(dependencies, monkeypatch, tmp_path):
    """Test deleting a specific experiment result."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": "test_exp4"})
    client.post(
        "/api/v1/experiments/test_exp4/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        "/api/v1/experiments/test_exp4/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )

    response = client.get("/api/v1/experiments/test_exp4")
    assert response.status_code == 200
    assert {"x1": 0.5, "objective_value": 100.0} in response.json()["results"]

    response = client.request(
        "DELETE", "/api/v1/experiments/test_exp4/results", json={"x1": 0.5}
    )

    assert response.status_code == 200
    assert (
        response.json().get("message")
        == "Result x1=0.5 deleted for experiment 'test_exp4'"
    )

    response = client.get("/api/v1/experiments/test_exp4")
    assert response.status_code == 200
    assert {"x1": 0.5, "objective_value": 100.0} not in response.json()["results"]

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp4")
        logger.debug("Cleaned up test_exp4 from test_delete_experiment_result")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp4: {str(e)}")


@pytest.mark.asyncio
async def test_list_experiments(dependencies, monkeypatch, tmp_path):
    """Test listing all experiment names and comments."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post(
        "/api/v1/experiments", json={"name": "exp5", "comments": "Experiment 1"}
    )
    client.post(
        "/api/v1/experiments", json={"name": "exp6", "comments": "Experiment 2"}
    )

    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()["experiments"]
    assert {"comments": "Experiment 1", "name": "exp5"} in data
    assert {"comments": "Experiment 2", "name": "exp6"} in data

    # Clean up: Delete the test experiments
    try:
        await storage.delete_experiment("exp5")
        await storage.delete_experiment("exp6")
        logger.debug("Cleaned up exp1 and exp5 from test_list_experiments")
    except Exception as e:
        logger.error(f"Failed to clean up exp1 or exp6: {str(e)}")


@pytest.mark.asyncio
async def test_recommend_next(dependencies, monkeypatch, tmp_path):
    """Test recommending the next x1 value."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": "test_exp7"})
    client.post(
        "/api/v1/experiments/test_exp7/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        "/api/v1/experiments/test_exp7/results",
        json={"x1": 0.3, "objective_value": 80.0},
    )
    client.post(
        "/api/v1/experiments/test_exp7/results",
        json={"x1": 0.7, "objective_value": 120.0},
    )

    response = client.get("/api/v1/experiments/test_exp7/recommend")
    assert response.status_code == 200
    x1 = response.json()["x1"]
    assert 0.0 <= x1 <= 1.0

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp7")
        logger.debug("Cleaned up test_exp7 from test_recommend_next")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp7: {str(e)}")


@pytest.mark.asyncio
async def test_get_experiment(dependencies, monkeypatch, tmp_path):
    """Test retrieving experiment details."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    comments = "Test experiment for get"
    client.post("/api/v1/experiments", json={"name": "test_exp8", "comments": comments})
    client.post(
        "/api/v1/experiments/test_exp8/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        "/api/v1/experiments/test_exp8/objectives",
        json={"name": "hydrogen production rate"},
    )
    client.post(
        "/api/v1/experiments/test_exp8/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )

    response = client.get("/api/v1/experiments/test_exp8")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_exp8"
    assert data["comments"] == comments
    assert {"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0} in data[
        "variables"
    ]
    assert {"name": "hydrogen production rate"} in data["objectives"]
    assert {"x1": 0.5, "objective_value": 100.0} in data["results"]

    # Clean up: Delete the test experiment
    try:
        await storage.delete_experiment("test_exp8")
        logger.debug("Cleaned up test_exp from test_get_experiment")
    except Exception as e:
        logger.error(f"Failed to clean up test_exp8: {str(e)}")


@pytest.mark.asyncio
async def test_delete_experiment(dependencies, monkeypatch, tmp_path):
    """Test deleting an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": "test_exp9"})
    client.post(
        "/api/v1/experiments/test_exp9/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )

    response = client.get("/api/v1/experiments/test_exp9")
    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1

    response = client.delete("/api/v1/experiments/test_exp9")
    assert response.status_code == 200
    assert response.json() == {"message": "Experiment 'test_exp9' deleted"}

    response = client.get("/api/v1/experiments/test_exp9")
    assert response.status_code == 500

    # Clean up: Already deleted by the test, but ensure no residual data
    try:
        await storage.delete_experiment("test_exp9")
        logger.debug(
            "Attempted cleanup of test_exp9 from test_delete_experiment (may already be deleted)"
        )
    except Exception as e:
        logger.debug(f"No cleanup needed for test_exp9: {str(e)}")


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
