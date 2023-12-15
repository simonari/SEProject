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
            "salary_given": 1,
            "salary_empty": 0
        })

        #не отрабатывает salary_given? бывают Nan в обоих полях
        data = [s for s in data if ((s.salary_from is not None)
                or (s.salary_to is not None))
                and s.currency == "RUR"#анализ только зп в рублях
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

        #для подсчета средних
        salaries = [s.salary_from for s in data]

        #линейная интерполяция
        data = sorted(data, key=lambda vac: vac.published_at)
        times = [s.published_at for s in data]
        x = [s.timestamp() for s in times]
        y = [s.salary_from for s in data]
        interpoler = scipy.interpolate.interp1d(x, y)
        times = np.arange(times[0], times[len(times)-1],
                           (times[len(times)-1] - times[0]) / len(times),
                            dtype=datetime).tolist()
        # для CubicSpline должно быть СТРОГОЕ возрастание x
        # пока будет интерполяцией по интерполяции, потом переделать
        x = [s.timestamp() for s in times]
        y = list(interpoler(x))
        interpoler2 = scipy.interpolate.CubicSpline(x, y)

        times = np.arange(times[0], times[len(times) - 1],
                          (times[len(times) - 1] - times[0]) / 1000,
                          dtype=datetime).tolist()
        x = [s.timestamp() for s in times]
        y = list(interpoler2(x))

        return {
            "amount": len(data),                # количество проанализированных вакансий
            "mean": stat.mean(salaries),        # среднеарифметическое зарплаты
            "median": stat.median(salaries),    # медиана зарплаты
            "x": times,                         # метки времени интерполяции
            "y": y,                             # значения зарплат интерполяции
        }

    async def analyze_experience(self):
        pass

    async def analyze_employment(self):
        pass
