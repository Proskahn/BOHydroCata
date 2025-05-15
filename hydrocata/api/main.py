from fastapi import FastAPI, Request
from hydrocata.api.routers import experiments
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(experiments.router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/experiments", response_class=HTMLResponse)
async def experiments_page(request: Request):
    return templates.TemplateResponse("experiments.html", {"request": request})


@app.get("/recommend", response_class=HTMLResponse)
async def recommend_page(request: Request):
    return templates.TemplateResponse("recommend.html", {"request": request})


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
