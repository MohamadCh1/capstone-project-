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

    from sqlalchemy.ext.asyncio import AsyncSession

    async def update_device(
        self,
        patient_email: str,
        old_serial_number: str,   # existing device (PK)
        new_serial_number: str,   # new device (PK)
        manufacturer: str,
        model: str,
        device_type: str,
    ) -> bool:

        if not all([
            patient_email,
            old_serial_number,
            new_serial_number,
            manufacturer,
            model,
            device_type
        ]):
            raise ValueError("All fields must be provided. None values are not allowed.")

        new_check = text("""
            SELECT serial_number
            FROM devices
            WHERE serial_number = :new_serial
        """)

        new_result = await self.session.execute(new_check, {
            "new_serial": new_serial_number
        })

        new_device = new_result.fetchone()

        if new_device:
            raise ValueError("The Serial number already exists in the system.")

        update_query = text("""
            UPDATE devices
            SET
                serial_number = :new_serial,
                manufacturer = :manufacturer,
                model = :model,
                device_type = :device_type,
                is_active = :is_active
            WHERE serial_number = :old_serial
              AND patient_email = :patient_email
        """)

        await self.session.execute(update_query, {
            "new_serial": new_serial_number,
            "manufacturer": manufacturer,
            "model": model,
            "device_type": device_type,
            "is_active": True,
            "old_serial": old_serial_number,
            "patient_email": patient_email
        })

        await self.session.commit()
        return True

    async def get_patient_devices(
        self,
        patient_email: str
    ) -> list[dict]:

        if not patient_email:
            raise ValueError("You Should Be Registered")

        query = text("""
            SELECT serial_number, device_type
            FROM devices
            WHERE patient_email = :patient_email
        """)

        result = await self.session.execute(query, {
            "patient_email": patient_email
        })

        rows = result.fetchall()

        devices = [
            {
                "serial_number": row.serial_number,
                "type": row.device_type
            }
            for row in rows
        ]

        return devices