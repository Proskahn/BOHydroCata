import pytest
import uuid
import logging
from fastapi.testclient import TestClient
from hydrocata.api.main import app
from hydrocata.storage.database_storage import DatabaseStorage
from hydrocata.optimization.bayesian import BayesianOptimizer
from fastapi import HTTPException

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = TestClient(app)


@pytest.fixture(scope="function")
async def storage():
    storage = DatabaseStorage(db_path="sqlite:///experiments.db")
    yield storage


@pytest.mark.asyncio
async def test_create_experiment(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    response = client.post(
        "/api/v1/experiments",
        json={"name": experiment_name, "comments": "Anode catalyst with IrO2 and RuO2"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": experiment_name,
        "comments": "Anode catalyst with IrO2 and RuO2",
    }

    experiments = await storage.list_experiments()
    assert any(exp["name"] == experiment_name for exp in experiments)

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_create_duplicate_experiment(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    response = client.post(
        "/api/v1/experiments",
        json={"name": experiment_name, "comments": "First attempt"},
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/experiments",
        json={"name": experiment_name, "comments": "Duplicate attempt"},
    )
    assert response.status_code == 500
    assert "already exists" in response.json().get("detail", "").lower()

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_add_variable(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "ratio_of_IrO2",
        "lower_bound": 0.0,
        "upper_bound": 1.0,
    }

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "ratio_of_RuO2",
        "lower_bound": 0.0,
        "upper_bound": 1.0,
    }

    details = await storage.get_experiment_details(experiment_name)
    assert len(details["variables"]) == 2
    assert {"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0} in details[
        "variables"
    ]
    assert {"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0} in details[
        "variables"
    ]

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_add_objective(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/objectives",
        json={"name": "hydrogen_production_rate"},
    )
    assert response.status_code == 200
    assert response.json() == {"name": "hydrogen_production_rate"}

    details = await storage.get_experiment_details(experiment_name)
    assert {"name": "hydrogen_production_rate"} in details["objectives"]

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_record_experiment_result(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    async def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        details = await storage.get_experiment_details(experiment_name)
        pbounds = {
            var["name"]: (
                var["lower_bound"] if var["lower_bound"] is not None else 0.0,
                var["upper_bound"] if var["upper_bound"] is not None else 1.0,
            )
            for var in details["variables"]
        }
        return BayesianOptimizer(pbounds=pbounds)

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
            "objective_value": 100.0,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
        "objective_value": 100.0,
    }

    details = await storage.get_experiment_details(experiment_name)
    assert {
        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
        "objective_value": 100.0,
    } in details["results"]

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_record_invalid_variable_result(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        return BayesianOptimizer(pbounds={"ratio_of_IrO2": (0.0, 1.0)})

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"undefined_var": 0.5},
            "objective_value": 100.0,
        },
    )
    assert response.status_code == 500
    assert "not defined" in response.json().get("detail", "").lower()

    response = client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 1.5},
            "objective_value": 100.0,
        },
    )
    assert response.status_code == 500
    assert "outside bounds" in response.json().get("detail", "").lower()

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_delete_experiment_result(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        return BayesianOptimizer(
            pbounds={"ratio_of_IrO2": (0.0, 1.0), "ratio_of_RuO2": (0.0, 1.0)}
        )

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
            "objective_value": 100.0,
        },
    )

    response = client.get(f"/api/v1/experiments/{experiment_name}")
    logger.debug(f"Get experiment response: {response.json()}")
    assert response.status_code == 200
    assert {
        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
        "objective_value": 100.0,
    } in response.json()["results"]

    response = client.request(
        "DELETE",
        f"/api/v1/experiments/{experiment_name}/results",
        json={"variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3}},
    )
    assert response.status_code == 200
    assert (
        response.json().get("message")
        == f"Result variables={{'ratio_of_IrO2': 0.5, 'ratio_of_RuO2': 0.3}} deleted for experiment '{experiment_name}'"
    )

    response = client.get(f"/api/v1/experiments/{experiment_name}")
    logger.debug(f"Get experiment after delete response: {response.json()}")
    assert response.status_code == 200
    assert {
        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
        "objective_value": 100.0,
    } not in response.json()["results"]

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_list_experiments(storage, monkeypatch):
    experiment_name1 = f"test_exp_{uuid.uuid4().hex}"
    experiment_name2 = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )

    client.post(
        "/api/v1/experiments",
        json={"name": experiment_name1, "comments": "Experiment 1"},
    )
    client.post(
        "/api/v1/experiments",
        json={"name": experiment_name2, "comments": "Experiment 2"},
    )

    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()["experiments"]
    assert {"name": experiment_name1, "comments": "Experiment 1"} in data
    assert {"name": experiment_name2, "comments": "Experiment 2"} in data

    await storage.delete_experiment(experiment_name1)
    await storage.delete_experiment(experiment_name2)
    logger.debug(f"Cleaned up {experiment_name1}, {experiment_name2}")


@pytest.mark.asyncio
async def test_recommend_next(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    async def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        details = await storage.get_experiment_details(experiment_name)
        pbounds = {
            var["name"]: (
                var["lower_bound"] if var["lower_bound"] is not None else 0.0,
                var["upper_bound"] if var["upper_bound"] is not None else 1.0,
            )
            for var in details["variables"]
        }
        return BayesianOptimizer(pbounds=pbounds)

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.3, "ratio_of_RuO2": 0.2},
            "objective_value": 80.0,
        },
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.7, "ratio_of_RuO2": 0.4},
            "objective_value": 120.0,
        },
    )

    response = client.get(f"/api/v1/experiments/{experiment_name}/recommend")
    assert response.status_code == 200
    variables = response.json()["variables"]
    assert "ratio_of_IrO2" in variables
    assert "ratio_of_RuO2" in variables
    assert 0.0 <= variables["ratio_of_IrO2"] <= 1.0
    assert 0.0 <= variables["ratio_of_RuO2"] <= 1.0

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_recommend_no_variables(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    async def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        details = await storage.get_experiment_details(experiment_name)
        pbounds = {
            var["name"]: (
                var["lower_bound"] if var["lower_bound"] is not None else 0.0,
                var["upper_bound"] if var["upper_bound"] is not None else 1.0,
            )
            for var in details["variables"]
        }
        if not pbounds:
            raise HTTPException(
                status_code=400, detail="No variables defined for experiment"
            )
        return BayesianOptimizer(pbounds=pbounds)

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})

    response = client.get(f"/api/v1/experiments/{experiment_name}/recommend")
    logger.debug(f"Recommend no variables response: {response.json()}")
    assert response.status_code == 400
    assert "no variables defined" in response.json().get("detail", "").lower()

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_get_experiment(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"
    comments = "Test experiment for get"

    def mock_get_storage():
        return storage

    def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        return BayesianOptimizer(
            pbounds={"ratio_of_IrO2": (0.0, 1.0), "ratio_of_RuO2": (0.0, 1.0)}
        )

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post(
        "/api/v1/experiments", json={"name": experiment_name, "comments": comments}
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/objectives",
        json={"name": "hydrogen_production_rate"},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
            "objective_value": 100.0,
        },
    )

    response = client.get(f"/api/v1/experiments/{experiment_name}")
    logger.debug(f"Get experiment response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == experiment_name
    assert data["comments"] == comments
    assert {"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0} in data[
        "variables"
    ]
    assert {"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0} in data[
        "variables"
    ]
    assert {"name": "hydrogen_production_rate"} in data["objectives"]
    assert {
        "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
        "objective_value": 100.0,
    } in data["results"]

    await storage.delete_experiment(experiment_name)
    logger.debug(f"Cleaned up {experiment_name}")


@pytest.mark.asyncio
async def test_delete_experiment(storage, monkeypatch):
    experiment_name = f"test_exp_{uuid.uuid4().hex}"

    def mock_get_storage():
        return storage

    def mock_get_optimizer(
        experiment_name: str, storage: DatabaseStorage = mock_get_storage()
    ):
        return BayesianOptimizer(
            pbounds={"ratio_of_IrO2": (0.0, 1.0), "ratio_of_RuO2": (0.0, 1.0)}
        )

    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_storage", mock_get_storage
    )
    monkeypatch.setattr(
        "hydrocata.api.routers.experiments.get_optimizer", mock_get_optimizer
    )

    client.post("/api/v1/experiments", json={"name": experiment_name})
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_IrO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/variables",
        json={"name": "ratio_of_RuO2", "lower_bound": 0.0, "upper_bound": 1.0},
    )
    client.post(
        f"/api/v1/experiments/{experiment_name}/results",
        json={
            "variables": {"ratio_of_IrO2": 0.5, "ratio_of_RuO2": 0.3},
            "objective_value": 100.0,
        },
    )

    response = client.get(f"/api/v1/experiments/{experiment_name}")
    logger.debug(f"Get experiment response: {response.json()}")
    assert response.status_code == 200
    assert len(response.json()["results"]) >= 1

    response = client.delete(f"/api/v1/experiments/{experiment_name}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Experiment '{experiment_name}' deleted"}

    response = client.get(f"/api/v1/experiments/{experiment_name}")
    logger.debug(f"Get experiment after delete response: {response.json()}")
    assert response.status_code == 500
    assert "not found" in response.json().get("detail", "").lower()

    try:
        await storage.delete_experiment(experiment_name)
        logger.debug(f"Attempted cleanup of {experiment_name}")
    except Exception as e:
        logger.debug(f"No cleanup needed for {experiment_name}: {str(e)}")


@pytest.mark.asyncio
async def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
