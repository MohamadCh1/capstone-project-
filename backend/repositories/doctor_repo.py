from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class MySQLDoctorsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, doctor_email: str) -> Dict:
        result = await self.session.execute(
            text("SELECT * FROM doctors WHERE email = :email"),
            {"email": doctor_email}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def insert(self, doctor: Dict) -> str:
        await self.session.execute(
            text("""
                INSERT INTO doctors (email, name, specialty, license_number, monthly_rate, is_available, is_verified, password)
                VALUES (:email, :name, :specialty, :license_number, :monthly_rate, 0, 0, :password)
            """),
            doctor
        )
        await self.session.commit()

    async def availability(self, email: str, status: bool) -> None:
        await self.session.execute(
            text("""
                UPDATE doctors
                SET is_available = :status
                WHERE email = :email
            """),
            {"status": status, "email": email}
        )
        await self.session.commit()
