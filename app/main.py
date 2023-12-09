from fastapi import FastAPI

from .logger import logger
from .scheduler import DownloadSchedule
from . import task_manager as tm
from .services import DataBaseManager
from .database import init_tables

app = FastAPI()

scheduler = DownloadSchedule()
scheduler.start()


@app.on_event("startup")
async def on_startup():
    await init_tables()


@app.get("/vacancies/{query}")
async def get_vacancy(api: str, query: str):
    logger.info(f"Got GET request with query: {query}")
    logger.info(f"Queueing task to Celery")
    tm.get_download.delay(api, query)
    return 200


@app.get("/scheduler/add/{api}/{time}/{query}")
async def add_task(api: str, time: str, query: str):
    scheduler.add_task(api, query, time)


@app.get("/vacancies/")
async def get_data(salary_leq: str | None = None,
                   salary_gte: str | None = None,
                   salary_given: str | None = None,
                   salary_empty: str | None = None):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    db = DataBaseManager()
    data = await db.get_data(query_dict)

    return data
