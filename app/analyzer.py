from .services import DataBaseManager


class BaseAnalyzer:
    def __init__(self):
        self.db = DataBaseManager()


class HHAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()

    async def analyze_salary(self):
        data = await self.db.get_data({
            # put query here
        })
        # analyze
        result = data
        # return it
        return result

    async def analyze_experience(self):
        pass

    async def analyze_employment(self):
        pass
