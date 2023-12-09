from schedule import Scheduler
from datetime import datetime, time
import asyncio
import json
import os

from .task_manager import download
from .logger import logger

scheduler = Scheduler()


class DownloadSchedule(Scheduler):
    DEFAULT_CONFIG_PATH = "timetable.json"

    def __init__(self, /, config_path: str = DEFAULT_CONFIG_PATH):
        logger.info(f"Instantiating Scheduler")
        super().__init__()
        self._loop = asyncio.get_event_loop()
        self._pending: asyncio.Task | None = None
        self._config_path = config_path
        logger.info(f"Loading data from config")
        self._setup()

    def _setup(self):
        if not os.path.isfile(os.path.join(os.getcwd(), self._config_path)):
            with open(self._config_path, "w"):
                pass

        with open(self._config_path, "r") as f:
            schedule = []
            try:
                schedule = json.load(f)
            except json.decoder.JSONDecodeError:
                # TODO: log this
                pass

        for task in schedule:
            self.every().day.at(task["time"]) \
                .do(download, task["api"], task["query"]) \
                .tag("download")

        logger.info(f"{len(schedule)} scheduled tasks was loaded")

    def _update_config(self, data: list[dict]):
        with open(self._config_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Schedule config updated")

    @staticmethod
    def _create_task(api: str, query: str, _time: str):
        return {"api": api, "time": _time, "query": query}

    def _add_to_config(self, api: str, query: str, _time: str):
        with open(self._config_path, "r") as f:
            schedule = []
            try:
                schedule = json.load(f)
            except json.decoder.JSONDecodeError:
                # TODO: log this
                pass

        schedule.append(self._create_task(api, query, _time))
        self._update_config(schedule)
        logger.info(f"Added task ({query}) to API ({api}) at ({_time}) to schedule")

    # TODO
    def _remove_from_config(self, query, _time):
        with open(self._config_path, "r") as f:
            schedule = []
            try:
                schedule = json.load(f)
            except json.decoder.JSONDecodeError:
                # TODO: log this
                pass

            for task in schedule:
                if task["query"] == query and task["time"] == _time:
                    del task

        self._update_config(schedule)
        logger.info(f"Removed task ({query}) at ({_time}) from schedule")

    # TODO: Overload run_pending() method to log moment of execution of task

    async def _start_pending(self):
        while True:
            await asyncio.sleep(1)
            # print(f"{datetime.now()} i'm running")
            job = self.get_jobs()[-1]
            # print(job.at_time, job.job_func)
            self.run_pending()

    def start(self):
        # self._loop.run_in_executor(None, lambda: asyncio.run(self._start_pending()))
        logger.info(f"Scheduler connecting to asyncio loop")
        self._pending = self._loop.create_task(self._start_pending())
        logger.info(f"Scheduler connected")

    def stop(self):
        if self._pending is None:
            return
        logger.info(f"Scheduler detaching from asyncio loop")
        self._pending.cancel()
        logger.info(f"Scheduler detached")

    @staticmethod
    def with_restart(foo):
        logger.info(f"Scheduler restarting")

        def inner(self, *args, **kwargs):
            self.stop()
            foo(self, *args, *kwargs)
            self.start()

        return inner

    @with_restart
    def add_task(self, api: str, query: str, _time: str):
        self.every().day.at(_time) \
            .do(download, api, query) \
            .tag("download")

        self._add_to_config(api, query, _time)

    # TODO
    @with_restart
    def remove_task(self, api: str, query: str, _time: str):
        jobs = self.get_jobs()

        for job in jobs:
            if job.at_time == time(_time) and job.job_func.args[0] == query:
                self.cancel_job(job)
            break

        self._remove_from_config(query, _time)
