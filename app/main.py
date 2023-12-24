from fastapi import FastAPI, Depends, HTTPException

from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas, models
from .logger import logger
from .models import User, TokenTable
from .services import DataBaseManager
from .database import init_tables, get_async_session
from .analyzer import HHAnalyzer
from .downloader import Downloader
from sqlalchemy.orm import Session
import sqlalchemy as orm
from .auth import create_access_token, create_refresh_token, verify_password, get_hashed_password

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .auth_bearer import JWTBearer
from functools import wraps

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = "HS256"
JWT_SECRET_KEY = "narscbjim@$@&^@&%^&RFghgjvbdsha"  # should be kept secret
JWT_REFRESH_SECRET_KEY = "13ugfdfgh@#$%^@&jkl45678902"

app = FastAPI()


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        payload = jwt.decode(kwargs['dependencies'], JWT_SECRET_KEY, ALGORITHM)
        user_id = payload['sub']
        data = kwargs['session'].query(models.TokenTable).filter_by(user_id=user_id, access_toke=kwargs['dependencies'],
                                                                    status=True).first()
        if data:
            return func(kwargs['dependencies'], kwargs['session'])

        else:
            return {'msg': "Token blocked"}

    return wrapper


@app.on_event("startup")
async def on_startup():
    await init_tables()


@app.get("/vacancies/download/")
async def download_vacancies(api: str, query: str):
    logger.info(f"Got GET request with query: {query}")
    logger.info(f"Queueing task to Celery")

    d = Downloader(api, query)
    await d.run()

    return 200


@app.get("/vacancies/get")
async def get_data(name: str | None = None,
                   salary_leq: str | None = None,
                   salary_gte: str | None = None,
                   salary_given: str | None = None,
                   salary_empty: str | None = None):
    query_dict = {k: v for k, v in locals().items() if v is not None}
    db = DataBaseManager()
    data = await db.get_data(query_dict)
    return data


@app.get("/vacancies/analyze")
async def analyze(name: str | None = None,
                  salary_leq: str | None = None,
                  salary_gte: str | None = None,
                  salary_given: str | None = None,
                  salary_empty: str | None = None):
    query_dict = {k: v for k, v in locals().items() if v is not None}
    hha = HHAnalyzer()
    return await hha.analyze(query_dict)


@app.get("/vacancies/analyze/salary")
async def get_salary_plot():
    return FileResponse("salaries.png")


@token_required
@app.get("/vacancies/analyze/experience")
async def get_experience_plot():
    return FileResponse("experience.png")


@token_required
@app.get("/vacancies/analyze/employment")
async def get_employment_plot():
    return FileResponse("employment.png")


@app.post("/auth/register")
async def register_user(user: schemas.UserCreate, session: AsyncSession = Depends(get_async_session)):
    query = orm.select(User).where(User.email == user.email)
    existing_user = (await session.execute(query)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    encrypted_password = get_hashed_password(user.password)

    new_user = models.User(username=user.username, email=user.email, password=encrypted_password)

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return {"message": "user created successfully"}


@app.post('/auth/login', response_model=schemas.TokenSchema)
async def login(request: schemas.RequestDetails, db: AsyncSession = Depends(get_async_session)):
    query = orm.select(User).where(User.email == request.email)
    user = (await db.execute(query)).scalar()

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email")

    hashed_pass = user.password
    if not verify_password(request.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    token_db = models.TokenTable(user_id=user.id, access_toke=access, refresh_toke=refresh, status=True)
    db.add(token_db)
    await db.commit()
    await db.refresh(token_db)
    return {
        "access_token": access,
        "refresh_token": refresh,
    }


@app.post('/auth/logout')
async def logout(dependencies=Depends(JWTBearer()), db: AsyncSession = Depends(get_async_session)):
    token = dependencies
    payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
    user_id = payload['sub']
    query = orm.select(TokenTable)
    token_record = (await db.execute(query)).all()
    info = []
    token_record = [item[0].__dict__ for item in token_record]
    for item in token_record:
        item.pop("_sa_instance_state")
    token_record = [TokenTable(**item) for item in token_record]
    for record in token_record:
        record = record
        print("record", record)
        if (datetime.utcnow() - record.created_date).days > 1:
            info.append(record.user_id)
    if info:
        query = orm.select(TokenTable).where(TokenTable.user_id.in_(info))
        existing_token = await db.delete(query)
        await db.commit()

    query = orm.select(models.TokenTable).filter(TokenTable.user_id == int(user_id),
                                                 TokenTable.access_toke == token)
    existing_token = (await db.execute(query)).scalar()

    if existing_token:
        existing_token.status = False
        db.add(existing_token)
        await db.commit()
        await db.refresh(existing_token)
    return {"message": "Logout Successfully"}
