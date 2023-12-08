import time
import datetime
import re
import aiohttp
import aiohttp.web_exceptions

from .services import DataBaseManager
from .logger import logger

HEADERS = {"User-Agent": "Magistracy Diploma/0.1 (vsimonari@gmail.com)"}
HTML_TAG_PATTERN = re.compile("<.*?>")

response_type = dict[str, str | list[str]]


class BaseDownloader:
    def __init__(self, query: str):
        self.query: str = query

    async def run(self):
        pass


class DownloaderHH(BaseDownloader):
    BASE_URL_API = "https://api.hh.ru/"

    def __init__(self, query: str):
        super().__init__(query)
        self.total_pages: int = 0
        self.ids: list[int] = []

        self.params = {
            "per_page": "100",
            "text": f"{query}"
        }

    async def run(self) -> str:
        await self._get_total_pages()
        await self._get_ids()
        return await self._get_vacancies()

    async def _get_total_pages(self):
        logger.info(f"({id(self)}): Getting number of pages")
        async with aiohttp.ClientSession(self.BASE_URL_API, headers=HEADERS) as session:
            response = await session.get("/vacancies", params=self.params)

            if response.status == 400:
                raise aiohttp.web_exceptions.HTTPBadRequest()

            content = await response.json()

        self.total_pages = content.get("pages")
        logger.info(f"({id(self)}): There is {self.total_pages} pages")

    @staticmethod
    def _parse_page(content) -> list[int]:
        return [vacancy["id"] for vacancy in content["items"]]

    async def _get_ids(self):
        logger.info(f"({id(self)}): Getting ids of vacancies")
        async with aiohttp.ClientSession(self.BASE_URL_API, headers=HEADERS) as session:
            ids = []
            params = self.params.copy()
            for p in range(self.total_pages):
                params["page"] = str(p)

                response = await session.get("/vacancies", params=params)

                if response.status == 400:
                    raise aiohttp.web_exceptions.HTTPBadRequest()

                content = await response.json()

                ids += self._parse_page(content)

                time.sleep(0.5)

        self.ids = ids
        logger.info(f"({id(self)}): There is {len(self.ids)} ids")

    @staticmethod
    def _parse_vacancy(content) -> dict[str, str | list[str]]:
        salary = content.get("salary")
        salary_from = None
        salary_to = None
        currency = None

        if salary is not None:
            salary_from = salary.get("from")
            salary_to = salary.get("to")
            salary_from = float(salary_from) if salary_from is not None else None
            salary_to = float(salary_to) if salary_to is not None else None
            currency = salary.get("currency")

        return {
            "id": int(content.get("id")),
            "name": content.get("name"),
            "area": content.get("area").get("name"),
            "salary_from": salary_from,
            "salary_to": salary_to,
            "currency": currency,
            "experience": content.get("experience").get("name"),
            "schedule": content.get("schedule").get("name"),
            "employment": content.get("employment").get("name"),
            "description": re.sub(HTML_TAG_PATTERN, "", content.get("description")),
            "key_skills": [s.get("name") for s in content.get("key_skills")],
            "alternate_url": content.get("alternate_url"),
            "published_at": datetime.datetime.strptime(content.get("published_at").split("T")[0], "%Y-%m-%d"),
        }

    async def _get_vacancies(self):
        logger.info(f"({id(self)}): Getting vacancies data")
        found = []

        async with aiohttp.ClientSession(self.BASE_URL_API, headers=HEADERS) as session:

            for _id in self.ids:
                response = await session.get(f"/vacancies/{_id}")

                if response.status == 400:
                    raise aiohttp.web_exceptions.HTTPBadRequest()

                content = await response.json()
                found.append(self._parse_vacancy(content))

                time.sleep(0.5)

        logger.info(f"({id(self)}): There is {len(found)} vacancies")
        logger.info(f"({id(self)}): Instantiating DataBaseManager")
        db = DataBaseManager()
        logger.info(f"({id(self)}): Manager instantiated on {id(db)}")
        logger.info(f"({id(self)}): Trying to save them to database")
        await db.add_data(found)
        logger.info(f"({id(self)}): Data saved")


class Downloader:
    _api_map = {
        "hh": DownloaderHH,
    }

    def __init__(self, api: str, query: str):
        self.api = api.lower()
        self.query = query

    async def run(self):
        downloader = self._api_map.get(self.api)
        if downloader is None:
            raise RuntimeError(f"Such API [{self.api}] is not integrated yet!")

        downloader = downloader(self.query)
        await downloader.run()
