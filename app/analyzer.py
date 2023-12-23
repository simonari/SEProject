from .services import DataBaseManager
from datetime import datetime
import numpy as np
import scipy.interpolate
from .models import Vacancy
import matplotlib.pyplot as plt


class BaseAnalyzer:
    def __init__(self):
        self.db = DataBaseManager()


class HHAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def interpolation_data_preprocessing(data: list[Vacancy]):
        data = [v for v in data if v.salary_from is not None]

        if len(data) < 2:
            raise ValueError("Not enough data")

        salaries = [v.salary_mean() for v in data]
        mean = np.mean(salaries)
        median = np.median(salaries)

        groups = {}
        for v in data:
            time = v.published_at

            if time in groups:
                groups[time].append(v.salary_from)
                continue

            groups[time] = [v.salary_from]

        data_avg = []
        for time, salaries in groups.items():
            average_salary = sum(salaries) / len(salaries)
            data_avg.append({"published_at": time, "salary": average_salary})

        data_avg = sorted(data_avg, key=lambda v: v["published_at"])

        x = [s["published_at"].timestamp() for s in data_avg]
        y = [s["salary"] for s in data_avg]

        return x, y, len(data), mean, median

    async def analyze_salary(self, data: list[Vacancy]):
        try:
            x, y, vacancies_count, mean, median = self.interpolation_data_preprocessing(data)
        except ValueError:
            return {"msg": "Not enough data"}

        interpolator = scipy.interpolate.CubicSpline(x, y)
        interpolation_count = 500  # число точек для графика

        x = np.linspace(x[0], x[len(x) - 1], num=500).tolist()
        y = list(interpolator(x))
        x = [datetime.fromtimestamp(s) for s in x]

        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.axhline(mean, c="r", ls="--", label="Средняя зарплата")
        ax.axhline(median, c="g", ls="--", label="Медианная зарплата")
        ax.tick_params(axis='x', labelrotation=45)
        fig.legend()
        fig.savefig("salaries.png", bbox_inches="tight")

        return "salaries.png"

    @staticmethod
    async def analyze_experience(data: list[Vacancy]):
        experience = [s.experience for s in data]
        labels = list(set(experience))
        values = [experience.count(x) for x in labels]

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.0f%%')

        fig.savefig("experience.png", bbox_inches="tight")
        return "experience.png"

    @staticmethod
    async def analyze_employment(data: list[Vacancy]):
        employment = [s.employment for s in data]
        labels = list(set(employment))
        values = [employment.count(x) for x in labels]

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.0f%%')

        fig.savefig("employment.png", bbox_inches="tight")
        return "employment.png"

    async def analyze(self, query_dict: dict[str, str]):
        data = await self.db.get_data(query_dict)
        return {
            "salaries": await self.analyze_salary(data),
            "experience": await self.analyze_experience(data),
            "employment": await self.analyze_employment(data),
        }
