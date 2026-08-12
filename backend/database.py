import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Called here (not only in app.py) because this module can be imported
# transitively - e.g. via a router importing get_mysql_session - before
# app.py's own top-level code has run. Safe to call more than once.
load_dotenv()

POSTGRES_URL = os.environ["POSTGRES_URL"]
pg_engine = create_async_engine(POSTGRES_URL, echo=True, future=True)
pg_session_factory = sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)

MYSQL_URL = os.environ["MYSQL_URL"]
mysql_engine = create_async_engine(MYSQL_URL, echo=True, future=True)
mysql_session_factory = sessionmaker(mysql_engine, expire_on_commit=False, class_=AsyncSession)

async def get_pg_session() -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_factory() as session:
        yield session

async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    async with mysql_session_factory() as session:
        yield session
