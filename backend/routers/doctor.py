from backend.repositories.suggestion_repo import MySQLSuggestionsRepo
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse
from backend.database import get_mysql_session
from backend.repositories.doctor_repo import MySQLDoctorsRepo
from backend.security import hash_password, verify_password
from decimal import Decimal
from backend.schemas import DoctorCreate
from pydantic import ValidationError
from starlette.status import HTTP_303_SEE_OTHER

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/doctor/register", response_class=HTMLResponse)
async def doctor_register_page(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("doctor_register.html", {"request": request})

@router.post("/doctor/register")
async def doctor_register(
    request: Request,
    email: str = Form(...),
    name: str = Form(...),
    specialty: str = Form(...),
    license_number: str = Form(...),
    monthly_rate: float = Form(...),
    password: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
):

    try:
        doctor = DoctorCreate(
            email=email,
            name=name,
            specialty=specialty,
            license_number=license_number,
            monthly_rate=monthly_rate,
            password=password
        )
    except ValidationError:
        return templates.TemplateResponse(
            "doctor_register.html",
            {"request": request, "error": "Please fill in all required fields correctly."},
            status_code=400
        )

    repo = MySQLDoctorsRepo(mysql)
    doctor_data = doctor.dict()
    doctor_data["password"] = hash_password(doctor_data["password"])

    try:
        await repo.insert(doctor_data)
    except ValueError as e:
        return templates.TemplateResponse(
            "doctor_register.html",
            {"request": request, "error": str(e)}
        )
    except Exception as e:
        if  "1062" in str(e) and "email" in str(e).lower():
            return templates.TemplateResponse(
                "doctor_register.html",
                {"request": request, "error": "This email is already registered."}
            )
        return templates.TemplateResponse(
            "doctor_register.html",
            {"request": request, "error": f"Registration failed: {str(e)}"}
        )

    request.session["message"] = f"Doctor {doctor.name} registered successfully!"
    return RedirectResponse(url="/doctor/login", status_code=302)

@router.get("/doctor/login")
async def show_login_form(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    flash = request.session.pop("flash", None)
    message = request.session.pop("message", None)
    return templates.TemplateResponse("doctor_login.html", {"request": request, "error":flash, "message": message})

@router.post("/doctor/login")
async def doctor_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    repo = MySQLDoctorsRepo(mysql)
    try:
        doctor = await repo.get(email)
        if not doctor:
            return templates.TemplateResponse(
                "doctor_login.html",
                {"request": request, "error": "Invalid email or password"}
            )

        if not verify_password(password, doctor["password"]):
            return templates.TemplateResponse(
                "doctor_login.html",
                {"request": request, "error": "Invalid email or password"}
            )

    except Exception as e:
        return templates.TemplateResponse(
            "doctor_login.html",
            {"request": request, "error": f"Login failed: {str(e)}"}
        )

    doctor_dict = {
        "email": doctor["email"],
        "name": doctor["name"],
        "specialty": doctor["specialty"],
        "is_verified": True if doctor["is_verified"]==1 else False,
        "is_available": True if doctor["is_available"]==1 else False,
        "monthly_rate": float(doctor["monthly_rate"]) if isinstance(doctor["monthly_rate"], Decimal) else doctor["monthly_rate"],
        "role": "Doctor"
    }
    request.session["user"] = doctor_dict
    return RedirectResponse(url="/dashboard", status_code=302)

@router.post("/update_availability")
async def update_doctor_availability(
    email: str = Form(...),
    status: bool = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
): 
    repo = MySQLDoctorsRepo(mysql)
    await repo.availability(email, status)  
    return RedirectResponse(url=f"/dashboard", status_code=HTTP_303_SEE_OTHER)