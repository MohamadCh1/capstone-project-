from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator


POSTGRES_URL = "postgresql+asyncpg://postgres:pass123@localhost:5432/diabetes_ts"
pg_engine = create_async_engine(POSTGRES_URL, echo=True, future=True)
pg_session_factory = sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)

MYSQL_URL = "mysql+aiomysql://root:pass123@localhost:3306/diabetes"
mysql_engine = create_async_engine(MYSQL_URL, echo=True, future=True)
mysql_session_factory = sessionmaker(mysql_engine, expire_on_commit=False, class_=AsyncSession)

async def get_pg_session() -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_factory() as session:
        yield session

async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    async with mysql_session_factory() as session:
        yield session
