# HydroCata-A API

**HydroCata-A** is a FastAPI-based web API designed to accelerate the optimization process of **Proton Exchange Membrane (PEM) electrolyzer** experiments. It leverages **Bayesian optimization** to guide researchers toward optimal catalyst combinations that maximize hydrogen production efficiency.

## 🎯 Objective

The HydroCata-A API aims to streamline experimental workflows by:

- 📊 Recording experimental data, including:
  - `x1` — the catalyst ratio (with constraint: `0 ≤ x1 ≤ 1`)
  - `hydrogen_rate` — the hydrogen production rate (must be a positive float)
- 🤖 Recommending the next optimal `x1` value using **Bayesian optimization**
- 💾 Persisting experiments in a **SQLite** database
- 🔗 Exposing a user-friendly **RESTful API** for integration into automated data pipelines

This tool is ideal for researchers and engineers looking to apply **data-driven optimization** in green hydrogen production using PEM electrolyzers.

---

## 🧰 Dependencies

The project uses [Poetry](https://python-poetry.org/) for dependency and environment management.

### ✅ Runtime

| Package              | Version         | Description                                       |
|----------------------|-----------------|---------------------------------------------------|
| `python`             | ^3.10, <3.12    | Required Python version                           |
| `fastapi`            | >=0.115.12,<0.116.0 | Web framework                                    |
| `uvicorn`            | >=0.34.2,<0.35.0   | ASGI server                                      |
| `numpy`              | >=2.2.5,<3.0.0    | Numerical operations                             |
| `httpx`              | >=0.28.1,<0.29.0  | HTTP client for async calls                      |
| `pydantic`           | >=2.11.0,<3.0.0   | Data validation and serialization                |
| `pydantic-settings`  | >=2.9.1,<3.0.0    | Settings management                              |
| `bayesian-optimization` | ^1.5.1        | Core Bayesian optimizer                          |
| `scipy`              | ^1.14.1           | Mathematical and scientific computations         |
| `sqlalchemy`         | ^2.0.36           | ORM for DB management                            |
| `aiosqlite`          | ^0.20.0           | Async SQLite driver                              |

### 🧪 Development

| Package            | Version         | Purpose                    |
|--------------------|-----------------|----------------------------|
| `pytest`           | >=8.3.5,<9.0.0  | Testing framework          |
| `pytest-asyncio`   | ^0.24.0         | Async support for pytest   |

---

## 🚀 Getting Started

### 1. 📦 Install Poetry (if not already installed)

```bash
pip install poetry
```

### 2. 📁 Clone the Repository

```bash
git clone <repository-url>
cd BOHydroCata
```

> 💡 If you’re already in `/Users/zkang/BOHydroCata`, skip this step.

### 3. 🔧 Install Dependencies

```bash
poetry install
```

This will create a virtual environment and install all required packages.

### 4. ✅ Verify Installation

```bash
poetry show fastapi uvicorn numpy httpx pydantic pydantic-settings \
    bayesian-optimization scipy sqlalchemy aiosqlite pytest pytest-asyncio
```

### 5. 🧹 Clear Existing Database (Optional)

To start fresh:

```bash
rm -f experiments.db test_experiments.db
```

---

## ▶️ Running the API

Start the FastAPI application with:

```bash
poetry run uvicorn hydrocata.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Parameters:

- `--host 0.0.0.0`: Makes the server externally accessible
- `--port 8000`: Change if port is in use
- `--reload`: Auto-reloads code on save (for development)
- `--log-level debug`: Enables detailed logging

### Expected Output

```text
INFO:     Will watch for changes in these directories: ['/Users/zkang/BOHydroCata']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12347]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🧪 API Usage

### 📚 Interactive API Docs

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to explore the endpoints using Swagger UI.

### 📬 Manual Requests

Use `curl`, Postman, or any HTTP client to interact with the following endpoints:

| Endpoint                | Method | Description                                       |
|-------------------------|--------|---------------------------------------------------|
| `/api/v1/record`        | POST   | Record an experiment (`x1`, `hydrogen_rate`)      |
| `/api/v1/recommend`     | GET    | Get recommended next `x1`                         |
| `/api/v1/experiments`   | GET    | List all recorded experiments                     |
| `/health`               | GET    | Health check                                      |

---

## 🧪 Running Tests

To run all tests:

```bash
poetry run pytest
```

---

## 📄 License

This project is provided for research and educational purposes. License to be defined.

---

## 🙋‍♀️ Questions?

Open an issue or reach out to the maintainers if you encounter problems or need enhancements!




