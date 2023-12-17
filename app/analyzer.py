from .services import DataBaseManager
import statistics as stat
from datetime import datetime
import numpy as np
import scipy.interpolate
import collections

class BaseAnalyzer:
    def __init__(self):
        self.db = DataBaseManager()


class HHAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    async def analyze_salary(self, name: str):
        data = await self.db.get_data({
            "name": name,
            #"salary_given": 1,
            #"salary_empty": 0
        })

        #не отрабатывает salary_given? бывают Nan в обоих полях
        data = [s for s in data if ((s.salary_from is not None)
                or (s.salary_to is not None))
                and s.currency == "RUR" #анализ только зп в рублях
                ]
        #хранить зп буду в salary_from
        for vac in data:
            if (vac.salary_from is None) and (vac.salary_to is not None):
                vac.salary_from = vac.salary_to
                continue
            if (vac.salary_from is not None) and (vac.salary_to is None):
                continue
            if (vac.salary_from is not None) and (vac.salary_to is not None):
                vac.salary_from = (vac.salary_from + vac.salary_to) / 2


        # подсчет средних
        salaries = [s.salary_from for s in data]
        if len(salaries) >= 1:
            mean = stat.mean(salaries)
            median = stat.median(salaries)
        else:
            mean = 0
            median = 0
            msg = "no data"
            return {
                "amount": len(data),
                "mean": mean,
                "median": median,
                "x": [],
                "y": [], 
                "msg": msg
            }

        if len(salaries) >= 2:
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

            data_avg = sorted(data_avg, key=lambda vac: vac["published_at"])
            times = [s["published_at"] for s in data_avg]
            x = [s.timestamp() for s in times]
            y = [s["salary"] for s in data_avg]

            interpoler = scipy.interpolate.CubicSpline(x, y)

            interpolation_count = 1000 # число точек для графика
            times = np.arange(times[0], times[len(times) - 1],
                              (times[len(times) - 1] - times[0]) / interpolation_count,
                              dtype=datetime).tolist()
            x = [s.timestamp() for s in times]
            y = list(interpoler(x))
            msg = "success"
        else:
            times = []
            y = []
            msg = "no interoplation"

        return {
            "len": len(data),                   # количество проанализированных вакансий
            "mean": mean,                       # среднеарифметическое зарплаты
            "median": median,                   # медиана зарплаты
            "x": times,                         # метки времени интерполяции
            "y": y,                             # значения зарплат интерполяции
            "msg": msg
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
