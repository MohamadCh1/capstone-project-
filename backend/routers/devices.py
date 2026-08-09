from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from backend.repositories.device_repo import MySQLDevicesRepo
from backend.repositories.measurements_repo import MeasurementsRepo
from backend.database import get_mysql_session, get_pg_session, pg_session_factory
from fastapi.responses import RedirectResponse
from backend.schemas import DeviceChange
from pydantic import ValidationError

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/device_change/{device_type}", response_class=HTMLResponse)
async def doctor_register_page(request: Request, device_type: str):
    user = request.session.get("user")
    if user:
        return templates.TemplateResponse("device_change.html", {"request": request, "device_type":device_type})
    return templates.TemplateResponse("paitent_register.html", {"request": request})

@router.post("/device_change/{device_type}")
async def change_bmi_device(
    request: Request,
    device_type:str,
    serial_number: str = Form(...),
    manufacturer: str = Form(...),
    model: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session),
    pg: AsyncSession = Depends(get_pg_session)
):
    try:
        device = DeviceChange(
                serial=serial_number,
                manufacturer=manufacturer,
                model=model,
            )
        user = request.session.get("user")
        devices = request.session.get("devices")
        old_serial = next((d["serial_number"] for d in devices if d["type"] == device_type), None)
        if not old_serial:
            return templates.TemplateResponse(
                "device_change.html",
                {"request": request, "error": f"No {device_type} device found for this user."}
            )
        repo = MySQLDevicesRepo(mysql)
        updated = await repo.update_device(user["email"],old_serial, device.serial, device.manufacturer,device.model,device_type)
        async with pg_session_factory() as pg_session:
            measurements_repo = MeasurementsRepo(pg_session)
            await measurements_repo.update_serial_number(old_serial, device.serial)
        return RedirectResponse("/dashboard", status_code=302)
    
    except ValidationError as e:
        # Pydantic validation errors
        return templates.TemplateResponse(
            "device_change.html",
            {"request": request, "device_type":device_type ,"error": "Invalid input! Serial must be 6-20 alphanumeric characters, Manufacturer and Model cannot be empty."}
        )  
    except ValueError as e:
        return templates.TemplateResponse(
            "device_change.html",
            {
                "request": request,
                "device_type":device_type,
                "error": str(e),
            }
        )


@router.get("/devices", response_class=HTMLResponse)
async def devices_dashboard(
    request: Request,
    mysql: AsyncSession = Depends(get_mysql_session),
):
    user = request.session.get("user")
    if not user:
        request.session["flash"] = "You need to login first"
        return RedirectResponse(url="/patient/login", status_code = 302)
    repo = MySQLDevicesRepo(mysql)

    devices = await repo.get_patient_devices(user["email"])
    request.session["devices"] = devices
    prediction_data = request.session.get("prediction")
    return templates.TemplateResponse(
        "devices_dashboard.html",
        {
            "request": request,
            "devices": devices,
            "user": user,
            "prediction_data": prediction_data
        }
    )
