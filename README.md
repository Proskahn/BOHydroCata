# HydroCata-A API

The HydroCata API is a FastAPI-based platform designed to optimize electrolyzer experiments. It enables researchers to create and manage experiments, specify design variables and objectives, record experimental results (catalyst ratio \( x_1 \) and hydrogen production rate), and use Bayesian optimization to recommend the next optimal catalyst combination for maximizing hydrogen production efficiency. The API uses a SQLite database to store experiment-specific data, ensuring isolation of unrelated variants, and provides a RESTful interface for seamless integration into experimental workflows.

## Objective

The HydroCata-A API aims to accelerate catalyst selection for PEM electrolyzers by providing a data-driven platform for researchers. Key features include:
- **Experiment Management**: Create named experiments with metadata (e.g., "Anode catalyst with \( IrO_2 \) and \( RuO_2 \)", including comments on temperature, pressure, etc.) to isolate unrelated variants.
- **Design Variables**: Specify variables (e.g., "ratio of \( IrO_2 \)") with bounds (e.g., \( [0, 1] \)) or default to \( \mathbb{R}^+ \).
- **Optimization Objectives**: Define objectives (e.g., hydrogen production rate) for single-objective optimization (multi-objective support planned for future).
- **Data Recording**: Record experimental results (\( x_1 \), objective value) in experiment-specific datasets.
- **Bayesian Optimization**: Recommend the next \( x_1 \) value to test, leveraging the `bayesian-optimization` library to maximize efficiency.
- **Data Retrieval and Deletion**: List all experiments, retrieve experiment data, delete specific results, or delete entire experiments.

This API is ideal for chemists and engineers working on green hydrogen production, offering a streamlined approach to catalyst optimization.

## Necessary Packages

The HydroCata-A API depends on the following Python packages, managed via [Poetry](https://python-poetry.org/):

- **Runtime Dependencies**:
  - `python`: `^3.10, <3.12` (Python 3.10 or 3.11)
  - `fastapi`: `>=0.115.12,<0.116.0` (FastAPI framework)
  - `uvicorn`: `>=0.34.2,<0.35.0` (ASGI server)
  - `numpy`: `>=2.2.5,<3.0.0` (Numerical computations)
  - `httpx`: `>=0.28.1,<0.29.0` (HTTP client for testing)
  - `pydantic`: `>=2.11.0,<3.0.0` (Data validation)
  - `pydantic-settings`: `>=2.9.1,<3.0.0` (Settings management)
  - `bayesian-optimization`: `^1.5.1` (Bayesian optimization)
  - `scipy`: `^1.14.1` (Scientific computations)
  - `sqlalchemy`: `^2.0.36` (ORM for SQLite)
  - `aiosqlite`: `^0.20.0` (Async SQLite driver)

- **Development Dependencies**:
  - `pytest`: `>=8.3.5,<9.0.0` (Testing framework)
  - `pytest-asyncio`: `^0.24.0` (Async support for pytest)

Install dependencies with Poetry (after installing Poetry via `pip install poetry`):

```bash
poetry install
```

## How to Use It

### Prerequisites

- **Python**: Version 3.10 or 3.11.
- **Poetry**: Install with `pip install poetry`.
- **Operating System**: Compatible with macOS, Linux, or Windows (developed on macOS `x86_64`).

### Setup

1. **Clone the Repository** (if applicable):
   ```bash
   git clone <https://github.com/Proskahn/BOHydroCata>
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

3. **Clear Existing Database Files** (optional, to start fresh):
   ```bash
   poetry run python clean_databases.py
   ```

### Running the API

1. **Start the API**:
   ```bash
   poetry run uvicorn hydrocata.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
   ```
   - `--host 0.0.0.0`: Allows external access.
   - `--port 8000`: Default port (change if needed, e.g., `--port 8080`).
   - `--reload`: Auto-reloads for development.
   - `--log-level debug`: Detailed logs for troubleshooting.

   Expected output:
   ```
   INFO:     Will watch for changes in these directories: ['/Users/zkang/BOHydroCata']
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process [12345] using StatReload
   INFO:     Started server process [12347]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

2. **Access the API**:
   - **Interactive Docs**: Open `http://localhost:8000/docs` in a browser for Swagger UI.
   - **Command Line**: Use `curl` or tools like Postman.

### Running Tests

Run the test suite to verify functionality:

```bash
poetry run pytest tests/test_api.py -v --log-cli-level=DEBUG
```

The tests cover:
- Creating experiments.
- Adding variables and objectives.
- Recording and deleting results.
- Listing all experiments.
- Recommending \( x_1 \) values.
- Retrieving and deleting experiments.
- Health checks.

Ensure the production database (`experiments.db`) is not modified by tests. Tests use unique temporary databases to prevent interference and protect real experiment data.

### Troubleshooting

- **API Fails to Start**:
  - Check logs:
    ```bash
    poetry run uvicorn hydrocata.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
    ```
  - Ensure port 8000 is free:
    ```bash
    lsof -i :8000
    ```
    Use a different port if needed (e.g., `--port 8080`).
  - Verify dependencies:
    ```bash
    poetry show fastapi uvicorn numpy httpx pydantic pydantic-settings bayesian-optimization scipy sqlalchemy aiosqlite pytest pytest-asyncio
    ```

- **404 Not Found Errors in Tests**:
  - Ensure `tests/test_api.py` uses `/api/v1` prefix for all endpoint URLs (e.g., `/api/v1/experiments`).
  - Verify `hydrocata/api/main.py` includes `app.include_router(experiments.router, prefix="/api/v1")`.

- **Database Errors**:
  - Ensure `hydrocata/storage/database_storage.py` imports `select` and `delete` from `sqlalchemy.sql`.
  - Clear stale database files:
    ```bash
    poetry run python clean_databases.py
    ```
  - Verify `aiosqlite`:
    ```bash
    poetry run python -c "import aiosqlite; print(aiosqlite.__version__)"
    ```

- **Test Failures (e.g., interference or database modification)**:
  - Run with debug logs:
    ```bash
    poetry run pytest tests/test_api.py -v --log-cli-level=DEBUG
    ```
  - Verify `tests/test_api.py` uses unique temporary databases via the `dependencies` fixture with `tmp_path`.
  - Ensure all tests mock `get_storage` to use the test database, preventing modification of `experiments.db`.
  - Check for consistent experiment names across test steps to avoid logical errors.
  - Clear stale database files before running tests:
    ```bash
    poetry run python clean_databases.py
    ```

- **Cleaning All Databases**:
  - To delete all database files (`experiments.db`, `test_experiments_*.db`):
    ```bash
    poetry run python clean_databases.py
    ```
  - Alternatively, use the command-line instruction:
    ```bash
    find /Users/zkang/BOHydroCata -type f -name "*.db" -exec rm -v {} \;
    ```
  - **Caution**: Backup `experiments.db` before cleaning if it contains production data:
    ```bash
    cp experiments.db experiments.db.bak
    ```