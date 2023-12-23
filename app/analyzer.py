from .services import DataBaseManager
from datetime import datetime
import numpy as np
import scipy.interpolate


class BaseAnalyzer:
    def __init__(self):
        self.db = DataBaseManager()


class HHAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    async def analyze_salary(self, name: str):
        data = await self.db.get_data({
            "name": name,
            "salary_given": 1,
            "currency": "RUR"
        })

        if len(data) < 2:
            return {
                "len": len(data),  # количество проанализированных вакансий
                "msg": "not_enough_data"
            }
        # хранить зп буду в salary_from
        for vac in data:
            if vac.salary_to is not None:
                vac.salary_from = (vac.salary_from + vac.salary_to) / 2
        # анализ средних
        salaries = [s.salary_from for s in data]
        mean = np.mean(salaries)
        median = np.median(salaries)
        # линейная интерполяция
        # усредняем зарплаты в вакансиях с одинаковым временем
        groups = {}
        for vac in data:
            time = vac.published_at
            if time in groups:
                groups[time].append(vac.salary_from)
            else:
                groups[time] = [vac.salary_from]
        data_avg = []
        for time, salaries in groups.items():
            average_salary = sum(salaries) / len(salaries)
            data_avg.append({"published_at": time, "salary": average_salary})

        data_avg = sorted(data_avg, key=lambda v: v["published_at"])
        # строим данные интерполяции
        y = [s["salary"] for s in data_avg]
        x = [s["published_at"].timestamp() for s in data_avg]
        interpolator = scipy.interpolate.CubicSpline(x, y)
        interpolation_count = 500  # число точек для графика
        x = np.linspace(x[0], x[len(x) - 1], num=500).tolist()
        y = list(interpolator(x))

        x = [datetime.fromtimestamp(s) for s in x]
        return {
            "len": len(data),                   # количество проанализированных вакансий
            "mean": mean,                       # среднеарифметическое зарплаты
            "median": median,                   # медиана зарплаты
            "x": x,                             # метки времени интерполяции
            "y": y,                             # значения зарплат интерполяции
            "msg": "success"
        }

    async def analyze_experience(self, name: str):
        data = await self.db.get_data({
            "name": name
        })
        experience = [s.experience for s in data]
        experience = dict((x, experience.count(x)) for x in set(experience) if experience.count(x) >= 1)
        return {"experience": experience}

    async def analyze_employment(self, name: str):
        data = await self.db.get_data({
            "name": name
        })
        employment = [s.employment for s in data]
        employment = dict((x, employment.count(x)) for x in set(employment) if employment.count(x) >= 1)
        return {"employment": employment}
