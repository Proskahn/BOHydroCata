from fastapi import FastAPI

from hydrocata.api.routers import experiments

app = FastAPI(
    title="HydroCata-A API",
    description="API for optimizing PEM electrolyzer experiments",
)

# Include the experiments router with a prefix
app.include_router(experiments.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Check API health."""
    return {"status": "healthy"}
