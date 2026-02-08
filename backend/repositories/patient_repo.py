from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class MySQLPatientsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, patient_email: str) -> Dict:
        result = await self.session.execute(
            text("SELECT * FROM patients WHERE email = :email"),
            {"email": patient_email}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def update_risk(self, patient_email: str, category: str) -> None:
        await self.session.execute(
            text("UPDATE patients SET risk_category = :category WHERE email = :email"),
            {"category": category, "email": patient_email}
        )
        await self.session.commit()

    async def insert(self, patient: Dict) -> None:
        patient_core = {
            "email": patient["email"],
            "name": patient["name"],
            "dob": patient["dob"],
            "gender": patient["gender"],
            "ethnicity": patient["ethnicity"],
            "password": patient["password"],
            "doctor_email": patient["doctor_email"],
        }
        print("Inserting patient:", patient_core)
        result = await self.session.execute(
            text("SELECT email FROM patients WHERE email = :email"),
            {"email": patient_core["email"]}
        )
        existing = result.fetchone()
        if existing:
            raise ValueError("Patient already registered")

        await self.session.execute(
            text("""INSERT INTO patients (email, name, dob, gender, ethnicity, password, risk_category, is_admin, doctor_email)
                    VALUES (:email, :name, :dob, :gender, :ethnicity, :password, null, 0, :doctor_email)"""),
            patient_core
        )
        await self.session.commit()
        return patient_core["email"]
    
    async def get_all_by_doctor(self, doctor_email: str) -> List[Dict]:
        result = await self.session.execute(
            text("SELECT * FROM patients WHERE doctor_email = :doctor_email"),
            {"doctor_email": doctor_email}
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]