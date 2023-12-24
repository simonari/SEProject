from datetime import datetime

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


class User(Base):
    __tablename__ = 'users'
    id = sql.Column(sql.Integer, primary_key=True)
    username = sql.Column(sql.String(50), nullable=False)
    email = sql.Column(sql.String(100), unique=True, nullable=False)
    password = sql.Column(sql.String(100), nullable=False)


class TokenTable(Base):
    __tablename__ = "token"
    user_id = sql.Column(sql.Integer)
    access_toke = sql.Column(sql.String(450), primary_key=True)
    refresh_toke = sql.Column(sql.String(450), nullable=False)
    status = sql.Column(sql.Boolean)
    created_date = sql.Column(sql.DateTime, default=datetime.now)
