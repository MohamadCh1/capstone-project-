from typing import List, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import uuid

VALID_STATUSES = {"rejected", "active", "stopped", "proposed"}


def normalize_details(details: Union[str, Dict]) -> str:
    if isinstance(details, dict):
        return json.dumps(details, sort_keys=True)
    try:
        parsed = json.loads(details)
        return json.dumps(parsed, sort_keys=True)
    except (TypeError, json.JSONDecodeError):
        return str(details)


class MySQLSuggestionsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists_similar(self, patient_email: str, details: Union[str, Dict]) -> bool:
        if isinstance(details, dict):
            text_value = details.get("text", "")
        else:
            try:
                parsed = json.loads(details)
                text_value = parsed.get("text", "")
            except Exception:
                text_value = str(details)

        result = await self.session.execute(
            text("""
                SELECT id FROM suggestions
                WHERE patient_email = :pid
                  AND JSON_UNQUOTE(JSON_EXTRACT(details, '$.text')) = :text
                  AND status IN ('active', 'proposed')
            """),
            {"pid": patient_email, "text": text_value}
        )
        return result.fetchone() is not None

    async def add_many(self, patient_email: str, suggestions: Union[List[Dict], Dict]):
        if isinstance(suggestions, dict):
            suggestions = [suggestions]

        for s in suggestions:
            s["details"] = normalize_details(s["details"])
            if not await self.exists_similar(patient_email, s["details"]):
                await self.session.execute(
                    text("""
                        INSERT INTO suggestions
                        (id, patient_email, source_type, category, details, priority, status)
                        VALUES (:id, :patient_email, :source_type, :category, :details, :priority, :status)
                    """),
                    s
                )
        await self.session.commit()

    async def update_status(self, suggestion_id: str, status: str) -> None:
        if status not in VALID_STATUSES:
            raise ValueError("Invalid status value")

        await self.session.execute(
            text("""
                UPDATE suggestions
                SET status = :status
                WHERE id = :id
            """),
            {"status": status, "id": suggestion_id}
        )
        await self.session.commit()

    async def get_all_active(self, patient_email: str) -> List[Dict]:
        result = await self.session.execute(
            text("SELECT * FROM suggestions WHERE patient_email = :pid AND status = 'active'"),
            {"pid": patient_email}
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    
    async def get_all_for_doctor(self, patient_email: str) -> List[Dict]:
        result = await self.session.execute(
            text("SELECT * FROM suggestions WHERE patient_email = :pid AND (status = 'active' or status = 'proposed')"),
            {"pid": patient_email}
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

