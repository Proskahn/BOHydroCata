from fastapi import FastAPI
from hydrocata.core.config import settings
from hydrocata.api.routers import experiments

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="API for HydroCata-A platform to record PEM electrolyzer experiments and recommend catalyst combinations.",
)

# Include routers
app.include_router(experiments.router, prefix="/api/v1", tags=["experiments"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
