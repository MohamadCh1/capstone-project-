from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class MySQLDevicesRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert(self, patient_email: str, device_type: str, serial_number: str,
                     manufacturer: str | None = None, model: str | None = None, is_active: bool | None = True) -> None:
        await self.session.execute(
            text("""INSERT INTO devices (patient_email, device_type, serial_number, manufacturer, model, is_active)
                    VALUES (:patient_email, :device_type, :serial_number, :manufacturer, :model, :is_active)"""),
            {
                "patient_email": patient_email,
                "device_type": device_type,
                "serial_number": serial_number,
                "manufacturer": manufacturer,
                "model": model,
                "is_active": is_active,
            }
        )
        await self.session.commit()