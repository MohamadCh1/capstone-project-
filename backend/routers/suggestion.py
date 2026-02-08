from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from backend.repositories.suggestion_repo import MySQLSuggestionsRepo
from backend.database import get_mysql_session

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/suggestions/update_status")
async def update_suggestion_status(
    id: str = Form(...),
    email: str = Form(...),
    status: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    valid_statuses = ["active", "stopped", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    repo = MySQLSuggestionsRepo(mysql)
    await repo.update_status(id, status)  
    return RedirectResponse(url=f"/patient/{email}", status_code=HTTP_303_SEE_OTHER)

@router.post("/suggestions/update_status_to_reject")
async def update_suggestion_status(
    id: str = Form(...),
    email: str = Form(...),
    status: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    valid_statuses = ["active", "stopped", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    repo = MySQLSuggestionsRepo(mysql)
    await repo.update_status(id, status)  
    return RedirectResponse(url=f"/patient/info/{email}", status_code=HTTP_303_SEE_OTHER)