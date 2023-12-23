import datetime
import sqlalchemy as sql
import sqlalchemy.orm as orm


class Base(orm.DeclarativeBase):
    pass


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(255))
    area = sql.Column(sql.String(255))
    salary_from = sql.Column(sql.Float())
    salary_to = sql.Column(sql.Float())
    currency = sql.Column(sql.String(3))
    experience = sql.Column(sql.String(255))
    schedule = sql.Column(sql.String(255))
    employment = sql.Column(sql.String(255))
    description = sql.Column(sql.Text())
    key_skills = sql.Column(sql.ARRAY(sql.String(24)))
    alternate_url = sql.Column(sql.String(255))
    published_at = sql.Column(sql.DateTime)

    def salary_mean(self):
        if self.salary_from is None:
            return None
        if self.salary_to is None:
            return self.salary_from
        return (self.salary_from + self.salary_to) / 2
