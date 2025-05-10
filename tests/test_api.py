import pytest
from fastapi.testclient import TestClient
from hydrocata.api.main import app
from hydrocata.storage.database_storage import DatabaseStorage, Base
from hydrocata.optimization.bayesian import BayesianOptimizer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create a TestClient instance for the FastAPI app
client = TestClient(app)


@pytest.fixture(scope="function")
async def dependencies():
    """Provide DatabaseStorage and BayesianOptimizer for a test, with database cleanup."""
    storage = DatabaseStorage(db_path="sqlite:///test_experiments.db")
    optimizer = BayesianOptimizer()

    # Clear database before test
    engine = create_engine("sqlite:///test_experiments.db", echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield storage, optimizer

    # Clean up after test
    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_record_experiment_success(dependencies):
    """Test recording a valid experiment."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    response = client.post("/api/v1/record", json={"x1": 0.5, "hydrogen_rate": 100.0})
    assert response.status_code == 200
    assert response.json() == {"x1": 0.5, "hydrogen_rate": 100.0}

    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert {"x1": 0.5, "hydrogen_rate": 100.0} in response.json()

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_record_experiment_invalid_x1(dependencies):
    """Test recording with invalid x1 (outside [0,1])."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    response = client.post("/api/v1/record", json={"x1": 1.5, "hydrogen_rate": 100.0})
    assert response.status_code == 422
    assert "x1" in response.json()["detail"][0]["loc"]

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_record_experiment_invalid_hydrogen_rate(dependencies):
    """Test recording with invalid hydrogen rate (non-positive)."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    response = client.post("/api/v1/record", json={"x1": 0.5, "hydrogen_rate": 0.0})
    assert response.status_code == 422
    assert "hydrogen_rate" in response.json()["detail"][0]["loc"]

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_recommend_no_data(dependencies):
    """Test recommend endpoint with no data (should return valid x1)."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    response = client.get("/api/v1/recommend")
    assert response.status_code == 200
    x1 = response.json()["x1"]
    assert 0.0 <= x1 <= 1.0

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_recommend_after_record(dependencies):
    """Test recommend endpoint after recording experiments."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    client.post("/api/v1/record", json={"x1": 0.3, "hydrogen_rate": 80.0})
    client.post("/api/v1/record", json={"x1": 0.7, "hydrogen_rate": 120.0})

    response = client.get("/api/v1/recommend")
    assert response.status_code == 200
    x1 = response.json()["x1"]
    assert 0.0 <= x1 <= 1.0

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_list_experiments_with_data(dependencies):
    """Test listing experiments after recording."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    client.post("/api/v1/record", json={"x1": 0.4, "hydrogen_rate": 90.0})
    client.post("/api/v1/record", json={"x1": 0.6, "hydrogen_rate": 110.0})

    response = client.get("/api/v1/experiments")
    assert response.status_code == 200

    response = client.get("/api/v1/all_experiments")
    assert response.status_code == 200

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_delete_all_experiments(dependencies):
    """Test deleting all experiments."""
    storage, optimizer = dependencies

    def mock_get_storage():
        return storage

    def mock_get_optimizer():
        return optimizer

    from hydrocata.api.routers import experiments

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(experiments, "get_storage", mock_get_storage)
    monkeypatch.setattr(experiments, "get_optimizer", mock_get_optimizer)

    # Add some experiments
    client.post("/api/v1/record", json={"x1": 0.4, "hydrogen_rate": 90.0})

    # Delete all experiments
    response = client.delete("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json() == {"message": "All experiments deleted"}

    # Verify experiments are gone
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json() == []

    monkeypatch.undo()


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
