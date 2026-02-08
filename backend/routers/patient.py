from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from fastapi.responses import RedirectResponse
from backend.schemas import PatientCreate, map_patient_to_db, ETHNICITY_MAP, GENDER_MAP
from backend.repositories.patient_repo import MySQLPatientsRepo
from backend.repositories.device_repo import MySQLDevicesRepo
from backend.services import hash_password, verify_password
from backend.database import get_mysql_session
from backend.repositories.doctor_repo import MySQLDoctorsRepo

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def patient_form(
    email: str = Form(...),
    name: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    ethnicity: str = Form(...),
    doctor_email: str = Form(...),
    password: str = Form(...),
    bmi_manufacturer: str = Form(...),
    bmi_model: str = Form(...),
    bmi_serial: str = Form(...),
    hba1c_manufacturer: str = Form(...),
    hba1c_model: str = Form(...),
    hba1c_serial: str = Form(...),
    glucose_manufacturer: str = Form(...),
    glucose_model: str = Form(...),
    glucose_serial: str = Form(...),
    bp_manufacturer: str = Form(...),
    bp_model: str = Form(...),
    bp_serial: str = Form(...),
    sleep_manufacturer: str = Form(...),
    sleep_model: str = Form(...),
    sleep_serial: str = Form(...),
) -> PatientCreate:
    return PatientCreate(
        email=email,
        name=name,
        dob=dob,
        gender=gender,
        ethnicity=ethnicity,
        doctor_email=doctor_email,
        password=password,
        bmi_manufacturer=bmi_manufacturer,
        bmi_model=bmi_model,
        bmi_serial=bmi_serial,
        hba1c_manufacturer=hba1c_manufacturer,
        hba1c_model=hba1c_model,
        hba1c_serial=hba1c_serial,
        glucose_manufacturer=glucose_manufacturer,
        glucose_model=glucose_model,
        glucose_serial=glucose_serial,
        bp_manufacturer=bp_manufacturer,
        bp_model=bp_model,
        bp_serial=bp_serial,
        sleep_manufacturer=sleep_manufacturer,
        sleep_model=sleep_model,
        sleep_serial=sleep_serial,
    )

@router.get("/patient/register")
async def show_register_form(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("patient_register.html", {"request": request})

@router.post("/patient/register")
async def patient_register(
    request: Request,
    patient: PatientCreate = Depends(patient_form),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    repo = MySQLPatientsRepo(mysql)
    device_repo = MySQLDevicesRepo(mysql)
    doctor_repo = MySQLDoctorsRepo(mysql)
    doctor = await doctor_repo.get(patient.doctor_email)
    
    try:
        if not doctor:
            raise ValueError("Doctor Not found")
        elif doctor['is_verified'] == False:
            raise ValueError("The Doctor You choose isn't Verified! Choose Another Doctor Please!")
        elif doctor['is_available'] == False:
            raise ValueError("The Doctor You choose isn't Available Right Now! Choose Another Doctor Please!")
        dob_date = datetime.strptime(patient.dob, "%Y-%m-%d")
        dob_utc_int = int(dob_date.replace(tzinfo=timezone.utc).timestamp())

        patient_data = {
            "email": patient.email,
            "name": patient.name,
            "dob": dob_utc_int,
            "gender": GENDER_MAP.get(patient.gender, None),
            "ethnicity": ETHNICITY_MAP.get(patient.ethnicity, None),
            "doctor_email": patient.doctor_email,
            "password": hash_password(patient.password),
        }
        await repo.insert(patient_data)  
        await device_repo.insert(patient.email, "BMI", patient.bmi_serial, patient.bmi_manufacturer, patient.bmi_model)
        await device_repo.insert(patient.email, "HBA1C", patient.hba1c_serial, patient.hba1c_manufacturer, patient.hba1c_model)
        await device_repo.insert(patient.email, "SBP", patient.bp_serial, patient.bp_manufacturer, patient.bp_model)
        await device_repo.insert(patient.email, "Glucose", patient.glucose_serial, patient.glucose_manufacturer, patient.glucose_model)
        await device_repo.insert(patient.email, "Activity&Sleep", patient.sleep_serial, patient.sleep_manufacturer, patient.sleep_model)
    
    except ValueError as e:
        return templates.TemplateResponse(
            "patient_register.html",
            {"request": request, "error": str(e)}
        )
    except Exception as e:
        if  "1062" in str(e) and "email" in str(e).lower():
            return templates.TemplateResponse(
                "patient_register.html",
                {"request": request, "error": "This email is already registered."}
            )
        return templates.TemplateResponse(
            "patient_register.html",
            {"request": request, "error": f"Registration failed: {str(e)}"}
        )

    request.session["message"] = f"Patient {patient.name} registered successfully!"
    return RedirectResponse(url="/patient/login", status_code=302)

@router.get("/patient/login")
async def show_login_form(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    flash = request.session.pop("flash", None)
    message = request.session.pop("message", None)
    return templates.TemplateResponse("patient_login.html", {"request": request, "error":flash, "message": message})

@router.post("/patient/login")
async def patient_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    mysql: AsyncSession = Depends(get_mysql_session)
):
    repo = MySQLPatientsRepo(mysql)

    try:
        patient = await repo.get(email)
        if not patient:
            return templates.TemplateResponse(
                "patient_login.html",
                {"request": request, "error": "Invalid email or password"}
            )

        if not verify_password(password, patient["password"]):
            return templates.TemplateResponse(
                "patient_login.html",
                {"request": request, "error": "Invalid email or password"}
            )

    except Exception as e:
        return templates.TemplateResponse(
            "patient_login.html",
            {"request": request, "error": f"Login failed: {str(e)}"}
        )
    
    request.session["user"] = {
        "name": patient["name"],
        "email": patient["email"],
        "role": "Patient",
        "gender": patient["gender"],        
        "ethnicity": patient["ethnicity"],  
        "dob": patient["dob"],              
        "doctor_email": patient["doctor_email"],
        "risk_category": patient["risk_category"]
    }
    return RedirectResponse(url="/dashboard", status_code=302)