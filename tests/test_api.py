import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from hydrocata.api.main import app
from hydrocata.optimization.bayesian import BayesianOptimizer
from hydrocata.storage.database_storage import Base, DatabaseStorage

# Create a TestClient instance for the FastAPI app
client = TestClient(app)


@pytest.fixture(scope="function")
async def dependencies():
    """Provide DatabaseStorage and BayesianOptimizer for a test, with database cleanup."""
    db_path = "sqlite:///test_experiments.db"
    if os.path.exists("test_experiments.db"):
        os.remove("test_experiments.db")

    storage = DatabaseStorage(db_path=db_path)
    optimizer = BayesianOptimizer()

    engine = create_engine(db_path, echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield storage, optimizer

    Base.metadata.drop_all(engine)
    engine.dispose()
    if os.path.exists("test_experiments.db"):
        os.remove("test_experiments.db")


@pytest.mark.asyncio
async def test_create_experiment(dependencies, monkeypatch):
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


@pytest.mark.asyncio
async def test_add_variable(dependencies, monkeypatch):
    """Test adding a design variable to an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    # Create experiment
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


@pytest.mark.asyncio
async def test_add_objective(dependencies, monkeypatch):
    """Test adding an objective to an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    # Create experiment
    client.post("/api/v1/experiments", json={"name": "test_exp"})

    response = client.post(
        "/api/v1/experiments/test_exp/objectives",
        json={"name": "hydrogen production rate"},
    )
    assert response.status_code == 200
    assert response.json() == {"name": "hydrogen production rate"}


@pytest.mark.asyncio
async def test_record_experiment_result(dependencies, monkeypatch):
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

    # Create experiment and variable
    client.post("/api/v1/experiments", json={"name": "test_exp2"})
    client.post(
        "/api/v1/experiments/test_exp/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )

    response = client.post(
        "/api/v1/experiments/test_exp/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )
    assert response.status_code == 200
    assert response.json() == {"x1": 0.5, "objective_value": 100.0}


@pytest.mark.asyncio
async def test_recommend_next(dependencies, monkeypatch):
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

    # Create experiment, variable, and result
    client.post("/api/v1/experiments", json={"name": "test_exp"})
    client.post(
        "/api/v1/experiments/test_exp/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        "/api/v1/experiments/test_exp/results",
        json={"x1": 0.3, "objective_value": 80.0},
    )
    client.post(
        "/api/v1/experiments/test_exp/results",
        json={"x1": 0.7, "objective_value": 120.0},
    )

    response = client.get("/api/v1/experiments/test_exp/recommend")
    assert response.status_code == 200
    x1 = response.json()["x1"]
    assert 0.0 <= x1 <= 1.0


@pytest.mark.asyncio
async def test_get_experiment(dependencies, monkeypatch):
    """Test retrieving experiment details."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    # Create experiment, variable, objective, and result
    client.post(
        "/api/v1/experiments",
        json={"name": "test_exp_2", "comments": "Test experiment"},
    )
    client.post(
        "/api/v1/experiments/test_exp_2/variables",
        json={"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        "/api/v1/experiments/test_exp_2/objectives",
        json={"name": "hydrogen production rate"},
    )
    client.post(
        "/api/v1/experiments/test_exp_2/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )

    response = client.get("/api/v1/experiments/test_exp_2")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_exp_2"
    assert data["comments"] == "Test experiment"
    assert {"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0} in data[
        "variables"
    ]
    assert {"name": "hydrogen production rate"} in data["objectives"]
    assert {"x1": 0.5, "objective_value": 100.0} in data["results"]


@pytest.mark.asyncio
async def test_delete_experiment(dependencies, monkeypatch):
    """Test deleting an experiment."""
    storage, _ = dependencies

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    # Create experiment and add data
    client.post("/api/v1/experiments", json={"name": "test_exp"})
    client.post(
        "/api/v1/experiments/test_exp/results",
        json={"x1": 0.5, "objective_value": 100.0},
    )

    # Verify experiment exists
    response = client.get("/api/v1/experiments/test_exp")
    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1

    # Delete experiment
    response = client.delete("/api/v1/experiments/test_exp")
    assert response.status_code == 200
    assert response.json() == {"message": "Experiment 'test_exp' deleted"}

    # Verify experiment is gone
    response = client.get("/api/v1/experiments/test_exp")
    assert response.status_code == 500  # Should fail as experiment is deleted


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
