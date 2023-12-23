import sqlalchemy as orm

from . import database
from . import models
from .models import Vacancy

from . import custom_typings as ct
from .logger import logger


class DataBaseManager:
    def __init__(self):
        self.engine = database.engine
        self.session = database.SessionLocal

    async def get_session(self):
        try:
            yield self.session
        finally:
            await self.session.close()

    async def add_tables(self):
        async with self.engine.begin() as conn:
            return await conn.run_sync(models.Base.metadata.create_all)

    async def add_data(self, data: ct.response):
        # TODO: do it with async context manager
        logger.info(f"({id(self)}): Establishing session with database")
        session = self.session()
        # getting ids that we want to add
        missing = set([i["id"] for i in data])

        # getting ids that presented in database
        query = orm.select(Vacancy.id)
        existing = set(item[0] for item in await session.execute(query))

        # leaving only unique for database ids
        missing -= existing

        # creating a list of items that we want to add
        to_add = [Vacancy(**item) for item in data if item["id"] in missing]
        logger.info(f"({id(self)}): {len(to_add)} / {len(data)} will be added")

        # adding items and saving state of database
        logger.info(f"({id(self)}): Trying to add to database")
        session.add_all(to_add)
        logger.info(f"({id(self)}): Committing changes")
        await session.commit()
        # closing session
        await session.close()
        logger.info(f"({id(self)}): Session closed")

    async def get_data(self, query_dict: dict[str, str]) -> list[Vacancy] | dict[str, str]:
        query = orm.select(Vacancy)

        if "name" in query_dict:
            query = query.where(Vacancy.name.contains(query_dict["name"]))
        if "salary_leq" in query_dict:
            query = query.where(
                    orm.or_(
                        Vacancy.salary_to <= float(query_dict["salary_leq"]),
                        Vacancy.salary_from <= float(query_dict["salary_leq"])
                    )
            )
        if "salary_gte" in query_dict:
            query = query.where(
                orm.or_(
                    Vacancy.salary_to >= float(query_dict["salary_gte"]),
                    Vacancy.salary_from >= float(query_dict["salary_gte"])
                ),
            )
        if "salary_given" in query_dict:
            query = query.where(Vacancy.salary_from != None)
        if "salary_empty" in query_dict:
            query = query.where(Vacancy.salary_from == None)
        if "currency" in query_dict:
            query = query.where(Vacancy.currency == query_dict["currency"])

        logger.info(f"({id(self)}): Establishing session with database")

        async with self.session() as session:
            if query == orm.select(Vacancy):
                return {"No query was provided": "400"}

            result = await session.execute(query)

        result = [item[0].__dict__ for item in result.all()]
        for item in result:
            item.pop("_sa_instance_state")
        print(query_dict)
        print(query)
        print(result)

        logger.info(f"({id(self)}): Session closed")
        return [Vacancy(**item) for item in result]
