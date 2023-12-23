from fastapi import FastAPI
from fastapi.responses import FileResponse

from .logger import logger
from .services import DataBaseManager
from .database import init_tables
from .analyzer import HHAnalyzer
from .downloader import Downloader

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await init_tables()


@app.get("/vacancies/download/")
async def download_vacancies(api: str, query: str):
    logger.info(f"Got GET request with query: {query}")
    logger.info(f"Queueing task to Celery")

    d = Downloader(api, query)
    await d.run()

    return 200


@app.get("/vacancies/get")
async def get_data(name: str | None = None,
                   salary_leq: str | None = None,
                   salary_gte: str | None = None,
                   salary_given: str | None = None,
                   salary_empty: str | None = None):
    query_dict = {k: v for k, v in locals().items() if v is not None}
    db = DataBaseManager()
    data = await db.get_data(query_dict)
    return data


@app.get("/vacancies/analyze")
async def analyze(name: str | None = None,
                  salary_leq: str | None = None,
                  salary_gte: str | None = None,
                  salary_given: str | None = None,
                  salary_empty: str | None = None):
    query_dict = {k: v for k, v in locals().items() if v is not None}
    hha = HHAnalyzer()
    return await hha.analyze(query_dict)


@app.get("/vacancies/analyze/images")
async def get_processed_image(path: str):
    available_paths = [
        "salaries.png",
        "experience.png",
        "employment.png"
    ]
    return FileResponse(path)
