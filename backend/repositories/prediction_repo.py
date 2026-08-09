from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

class RiskPredictionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_prediction(
        self,
        patient_email: str,
        probability: float,
        risk_category: str,
        explanation: str,
    ) -> None:
        if not all([patient_email, probability, risk_category, explanation]):
            raise ValueError("All fields must be provided.")

        query = text("""
            INSERT INTO predictions (
                patient_email,
                probability,
                risk_category,
                explanation,
                ts
            )
            VALUES (
                :patient_email,
                :probability,
                :risk_category,
                :explanation,
                :ts
            )
        """)

        await self.session.execute(query, {
            "patient_email": patient_email,
            "probability": probability,
            "risk_category": risk_category,
            "explanation": explanation,
            "ts": datetime.utcnow()
        })

        await self.session.commit()
