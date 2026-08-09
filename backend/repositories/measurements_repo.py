from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class MeasurementsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_measurements(self, patient_email: str):
        query = text("""
            SELECT DISTINCT ON (type)
                type, value, unit, ts, raw_payload
            FROM measurements
            WHERE patient_email = :patient_email
              AND type IN ('BMI', 'HBA1C', 'SBP', 'Glucose')
            ORDER BY type, ts DESC;
        """)
        result = await self.session.execute(query, {"patient_email": patient_email})
        rows = result.fetchall()

        return {row.type: dict(row._mapping) for row in rows}
    
    async def get_measurements_last_7_days(self, patient_email: str):
        query = text("""
            SELECT
                type, value, unit, ts, raw_payload
            FROM measurements
            WHERE patient_email = :patient_email
            AND type IN ('BMI', 'HBA1C', 'SBP', 'Glucose')
            AND ts >= NOW() - INTERVAL '7 days'
            ORDER BY type, ts Asc;
        """)
        result = await self.session.execute(query, {"patient_email": patient_email})
        rows = result.fetchall()

        measurements = {}
        for row in rows:
            measurements.setdefault(row.type, []).append(dict(row._mapping))

        return measurements
    
    async def get_measurements_avg_last_7_days(self, patient_email: str):
        query = text("""
            SELECT
                type,
                AVG(value) AS avg_value,
                MIN(unit) AS unit
            FROM measurements
            WHERE patient_email = :patient_email
            AND type IN ('BMI', 'HBA1C', 'SBP', 'Glucose')
            AND ts >= NOW() - INTERVAL '7 days'
            GROUP BY type
        """)
        result = await self.session.execute(query, {"patient_email": patient_email})
        rows = result.fetchall()

        measurements = {}
        for row in rows:
            measurements[row.type] = {
                "avg_value": row.avg_value,
                "unit": row.unit
            }

        return measurements
    
    async def update_serial_number(
        self,
        old_serial: str,
        new_serial: str
    ) -> bool:
        update_query = text("""
            UPDATE measurements
            SET device_serial = :new_serial
            WHERE device_serial = :old_serial
        """)
        result = await self.session.execute(update_query, {
            "new_serial": new_serial,
            "old_serial": old_serial
        })
        await self.session.commit()
        return result.rowcount > 0