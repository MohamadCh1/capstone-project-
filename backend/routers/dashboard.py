from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services import RiskService, to_serializable, MedicalService
from backend.repositories.measurements_repo import MeasurementsRepo
from backend.repositories.patient_repo import MySQLPatientsRepo
from backend.database import get_pg_session, get_mysql_session, pg_session_factory, mysql_session_factory
from backend.repositories.suggestion_repo import MySQLSuggestionsRepo
from backend.repositories.doctor_repo import MySQLDoctorsRepo
from pydantic import EmailStr
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/patient/info/{email}", response_class=HTMLResponse)
async def get_info(request: Request, email: EmailStr, pg: AsyncSession = Depends(get_pg_session)):
    user = request.session.get("user")
    async with mysql_session_factory() as session:
        patient_repo = MySQLPatientsRepo(session)
        patient = await patient_repo.get(email)
    async with pg_session_factory() as pg_session:
        measurements_repo = MeasurementsRepo(pg_session)
        measurement_data = await measurements_repo.get_latest_measurements(patient["email"])
        last_7_day = await measurements_repo.get_measurements_last_7_days(patient["email"])
        measurement_data_last_7_days = await measurements_repo.get_measurements_avg_last_7_days(patient['email'])
    if measurement_data:
        async with mysql_session_factory() as session:
            patient_repo = MySQLPatientsRepo(session)
            risk_services = RiskService(patient_repo)
            prediction_data = {
                "RIDAGEYR": patient["dob"],
                "BMXBMI": measurement_data["BMI"]["value"],
                "LBXGH": measurement_data["HBA1C"]["value"],
                "LBXGH_missing": 0, 
                "SBP_mean": measurement_data["SBP"]["value"], 
                "LBDHDD": 51.0, 
                "HDL_missing": 1,
                "LBXSCR": 0.84, 
                "LBXGLU": measurement_data["Glucose"]["value"],
                "LBXGLU_missing": 0,
                "ACR": 0.07593,
                "ACR_missing": 1,
                "RIAGENDR": patient["gender"],
                "RIDRETH3": patient["ethnicity"]
            }
            prediction = await risk_services.predict_and_record(patient["email"], prediction_data)
            # SBP
            chart_data = {
                "labels": [m["ts"].date().isoformat() for m in last_7_day["SBP"]],
                "datasets": [{
                    "label": "SBP (mmHg)",
                    "data": [float(m["value"]) for m in last_7_day["SBP"]],
                    "borderColor": "blue",
                    "fill": True
                }]
            }
            sbp_data = json.dumps(chart_data, default=to_serializable)

            # BMI
            chart_data = {
                "labels": [m["ts"].date().isoformat() for m in last_7_day["BMI"]],
                "datasets": [{
                    "label": "BMI (kg/m2)",
                    "data": [float(m["value"]) for m in last_7_day["BMI"]],
                    "borderColor": "green",
                    "fill": True
                }]
            }
            bmi_data = json.dumps(chart_data, default=to_serializable)

                # Glucose
            chart_data = {
                "labels": [m["ts"].date().isoformat() for m in last_7_day["Glucose"]],
                "datasets": [{
                    "label": "Glucose (mg/dl)",
                    "data": [float(m["value"]) for m in last_7_day["Glucose"]],
                    "borderColor": "orange",
                    "fill": True
                }]
            }
            glucose_data = json.dumps(chart_data, default=to_serializable)

            chart_data = {
                "labels": [m["ts"].date().isoformat() for m in last_7_day["HBA1C"]],
                "datasets": [{
                    "label": "HBA1C (%)",
                    "data": [float(m["value"]) for m in last_7_day["HBA1C"]],
                    "borderColor": "red",
                    "fill": True
                }]
            }
            hba1c_data = json.dumps(chart_data, default=to_serializable)
            async with mysql_session_factory() as session:
                repo = MySQLSuggestionsRepo(session)
                medical_services = MedicalService(repo)
                suggestions = await medical_services.generate_suggestions(
                    patient_email=patient["email"],
                    hba1c=measurement_data_last_7_days.get('HBA1C', {}).get('avg_value', 0),
                    glucose=measurement_data_last_7_days.get('Glucose', {}).get('avg_value', 0),
                    bmi=measurement_data_last_7_days.get('BMI', {}).get('avg_value', 0),
                    sbp=measurement_data_last_7_days.get('SBP', {}).get('avg_value', 0)
                )
                suggestions = await repo.get_all_for_doctor(patient['email'])
                if not suggestions:
                    suggestions = [{'details': '{"text": "There are no suggestions at the moment. Please check back later."}'}]
                for s in suggestions:
                    if isinstance(s["details"], str):
                        try:
                            s["details"] = json.loads(s["details"])
                        except Exception:
                            pass
            return templates.TemplateResponse("patient_info.html", {"request": request, "user": user, 
                                                                    "patient_measurement_data": measurement_data,
                                                                    "prediction_data": prediction,
                                                                    "sbp_data": sbp_data,
                                                                    "bmi_data": bmi_data,
                                                                    "hba1c_data": hba1c_data,
                                                                    "glucose_data": glucose_data,
                                                                    "patient": patient,
                                                                    "suggestions": suggestions})
    else:
        return templates.TemplateResponse("patient_info.html", {"request": request, "user": user,
                                                                        "patient_measurement_data": None,"patient": patient})


@router.get("/dashboard")
async def dashboard(request: Request, pg: AsyncSession = Depends(get_pg_session)
):
    user = request.session.get("user")
    if not user:
        request.session["flash"] = "You need to login first"
        return RedirectResponse(url="/patient/login", status_code = 302)
    elif user["role"] == "Patient":
        async with pg_session_factory() as pg_session:
            measurements_repo = MeasurementsRepo(pg_session)
            measurement_data = await measurements_repo.get_latest_measurements(user["email"])
            measurement_data_last_7_days = await measurements_repo.get_measurements_avg_last_7_days(user['email'])
        if measurement_data:
            async with mysql_session_factory() as session:
                patient_repo = MySQLPatientsRepo(session)
                risk_services = RiskService(patient_repo)
                prediction_data = {
                    "RIDAGEYR": user["dob"],
                    "BMXBMI": measurement_data["BMI"]["value"],
                    "LBXGH": measurement_data["HBA1C"]["value"],
                    "LBXGH_missing": 0, 
                    "SBP_mean": measurement_data["SBP"]["value"], 
                    "LBDHDD": 51.0, 
                    "HDL_missing": 1,
                    "LBXSCR": 0.84, 
                    "LBXGLU": measurement_data["Glucose"]["value"],
                    "LBXGLU_missing": 0,
                    "ACR": 0.07593,
                    "ACR_missing": 1,
                    "RIAGENDR": user["gender"],
                    "RIDRETH3": user["ethnicity"]
                }
                prediction = await risk_services.predict_and_record(user["email"], prediction_data)
                async with mysql_session_factory() as session:
                    repo = MySQLSuggestionsRepo(session)
                    medical_services = MedicalService(repo)
                    suggestions = await medical_services.generate_suggestions(
                        patient_email=user["email"],
                        hba1c=measurement_data_last_7_days.get('HBA1C', {}).get('avg_value', 0),
                        glucose=measurement_data_last_7_days.get('Glucose', {}).get('avg_value', 0),
                        bmi=measurement_data_last_7_days.get('BMI', {}).get('avg_value', 0),
                        sbp=measurement_data_last_7_days.get('SBP', {}).get('avg_value', 0)
                    )
                    suggestions = await repo.get_all_active(user['email'])
                    if not suggestions:
                        suggestions = [{'details': '{"text": "There are no suggestions at the moment. Please check back later."}'}]
                    for s in suggestions:
                        if isinstance(s["details"], str):
                            try:
                                s["details"] = json.loads(s["details"])
                            except Exception:
                                pass
            return templates.TemplateResponse("patient_dashboard.html", {"request": request, "user": user, 
                                                                    "patient_measurement_data": measurement_data,
                                                                    "prediction_data": prediction,
                                                                    "suggestions": suggestions})
        else:
               return templates.TemplateResponse("patient_dashboard.html", {"request": request, "user": user,
                                                                            "patient_measurement_data": None})
    else:
        async with mysql_session_factory() as session:
            patient_repo = MySQLPatientsRepo(session)
            patients = await patient_repo.get_all_by_doctor(user['email'])
            user = await MySQLDoctorsRepo(session).get(user['email'])
            print(user["is_available"])
            return templates.TemplateResponse("doctor_dashboard.html", {"request": request, "user": user, 'patients':patients})
    
