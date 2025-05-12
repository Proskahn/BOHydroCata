
# HydroCata-A API

The **HydroCata-A API** is a FastAPI-based platform designed to optimize Proton Exchange Membrane (PEM) electrolyzer experiments. It enables researchers to manage experiments, specify design variables and objectives, record results, and use Bayesian optimization to recommend the next optimal catalyst combination to maximize hydrogen production.

---

## 🚀 Objective

Accelerate catalyst selection for PEM electrolyzers using a data-driven platform.

### 🔑 Key Features

- **Experiment Management**: Create isolated, named experiments with metadata.
- **Design Variables**: Define bounds for variables like catalyst ratios.
- **Optimization Objectives**: Support for hydrogen production rate (multi-objective coming soon).
- **Data Recording**: Track inputs and outputs per experiment.
- **Bayesian Optimization**: Recommends next optimal input (x₁).
- **Data Retrieval & Deletion**: Manage experiment data with RESTful endpoints.

---

## 📦 Necessary Packages

Managed via **Poetry**.

### Runtime Dependencies

- `python`: ^3.10, <3.12
- `fastapi`: >=0.115.12,<0.116.0
- `uvicorn`: >=0.34.2,<0.35.0
- `numpy`: >=2.2.5,<3.0.0
- `httpx`: >=0.28.1,<0.29.0
- `pydantic`: >=2.11.0,<3.0.0
- `pydantic-settings`: >=2.9.1,<3.0.0
- `bayesian-optimization`: ^1.5.1
- `scipy`: ^1.14.1
- `sqlalchemy`: ^2.0.36
- `aiosqlite`: ^0.20.0

### Development Dependencies

- `pytest`: >=8.3.5,<9.0.0
- `pytest-asyncio`: ^0.24.0

---

## 🛠️ How to Use It

### Prerequisites

- Python 3.10 or 3.11
- Poetry: `pip install poetry`
- Compatible OS: macOS, Linux, Windows

### Setup

```bash
git clone <repository-url>
cd BOHydroCata  # Skip if you're already in /Users/zkang/BOHydroCata
poetry install
```

### Verify Installation

```bash
poetry show fastapi uvicorn numpy httpx pydantic pydantic-settings bayesian-optimization scipy sqlalchemy aiosqlite pytest pytest-asyncio
```

### Optional: Clear Existing Database Files

```bash
rm -f experiments.db test_experiments*.db
```

---

## ▶️ Running the API

```bash
poetry run uvicorn hydrocata.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

**Access:**

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- CLI or Postman for direct API calls

---

## 📡 API Endpoints

### Create Experiment

```bash
curl -X POST "http://localhost:8000/api/v1/experiments" \
-H "Content-Type: application/json" \
-d '{"name": "anode_catalyst", "comments": "Anode catalyst with IrO2 and RuO2, T=25C, P=1atm"}'
```

### Add Design Variable

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/anode_catalyst/variables" \
-H "Content-Type: application/json" \
-d '{"name": "ratio of IrO2", "lower_bound": 0.0, "upper_bound": 1.0}'
```

### Add Objective

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/anode_catalyst/objectives" \
-H "Content-Type: application/json" \
-d '{"name": "hydrogen production rate"}'
```

### Record Result

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/anode_catalyst/results" \
-H "Content-Type: application/json" \
-d '{"x1": 0.5, "objective_value": 100.0}'
```

### Get Recommendation

```bash
curl "http://localhost:8000/api/v1/experiments/anode_catalyst/recommend"
```

### Get All Experiment Data

```bash
curl "http://localhost:8000/api/v1/experiments/anode_catalyst"
```

### Delete Experiment

```bash
curl -X DELETE "http://localhost:8000/api/v1/experiments/anode_catalyst"
```

### Health Check

```bash
curl "http://localhost:8000/health"
```

---

## ✅ Running Tests

```bash
poetry run pytest tests/test_api.py -v --log-cli-level=DEBUG
```

### Tests Cover:

- Experiment creation
- Adding variables/objectives
- Recording results
- Recommendation generation
- Data retrieval & deletion
- Health checks

> Tests use temporary databases. Real data in `experiments.db` is safe.

---

## 🧩 Troubleshooting

### API Won't Start?

```bash
poetry run uvicorn hydrocata.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

- Check port: `lsof -i :8000`
- Try a different port: `--port 8080`

### 404 Errors?

- Ensure `/api/v1` prefix is used in routes
- Confirm `main.py` includes:  
  `app.include_router(experiments.router, prefix="/api/v1")`

### Database Errors?

- Confirm `select`, `delete` imported in `database_storage.py`
- Clear old DB files: `rm -f experiments.db test_experiments*.db`

### Test Interference?

- Use `tmp_path` in tests
- Ensure tests mock `get_storage`
- Use unique experiment names
- Run with debug logs for clarity

---

## 📬 Feedback

This API is designed for researchers in **green hydrogen production**. Feedback and contributions are welcome!
