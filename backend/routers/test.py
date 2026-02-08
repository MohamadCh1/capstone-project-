from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_pg_session, get_mysql_session

router = APIRouter()

@router.get("/test-db")
async def test_db_connections(
    pg: AsyncSession = Depends(get_pg_session),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    try:
        # PostgreSQL test
        pg_result = await pg.execute(text("SELECT 1"))
        pg_ok = pg_result.scalar() == 1

        # MySQL test
        mysql_result = await mysql.execute(text("SELECT 1"))
        mysql_ok = mysql_result.scalar() == 1

        return {
            "postgres_connected": pg_ok,
            "mysql_connected": mysql_ok
        }
    except Exception as e:
        return {"error": str(e)}