from fastapi import FastAPI, Request, Depends
from hydrocata.api.routers import experiments
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from hydrocata.storage.database_storage import DatabaseStorage

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(experiments.router, prefix="/api/v1")


def get_storage():
    """Provide a new DatabaseStorage instance."""
    return DatabaseStorage(db_path="sqlite:///experiments.db")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/experiments", response_class=HTMLResponse)
async def experiments_page(
    request: Request, storage: DatabaseStorage = Depends(get_storage)
):
    experiment_name = request.query_params.get("experiment_name", None)
    variables = []
    if experiment_name:
        try:
            details = await storage.get_experiment_details(experiment_name)
            variables = details["variables"]
        except Exception:
            variables = []
    return templates.TemplateResponse(
        "experiments.html",
        {
            "request": request,
            "variables": variables,
            "experiment_name": experiment_name,
        },
    )


@app.get("/recommend", response_class=HTMLResponse)
async def recommend_page(request: Request):
    return templates.TemplateResponse("recommend.html", {"request": request})


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
