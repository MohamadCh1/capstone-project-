from pydantic import BaseModel, Field, EmailStr, constr, StringConstraints
from typing import Dict, Any, List, Optional, Annotated

SerialNumber = Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9\-]{6,20}$')]

class DoctorCreate(BaseModel):
    email: EmailStr
    name: str
    specialty: str
    license_number: str
    monthly_rate: float = Field(..., gt=0)
    password: str


class PatientCreate(BaseModel):
    email: EmailStr
    name: str
    gender: str
    ethnicity: str
    doctor_email: EmailStr
    password: str
    dob: str

    bmi_manufacturer: str
    bmi_model: str
    bmi_serial: SerialNumber

    hba1c_manufacturer: str
    hba1c_model: str
    hba1c_serial: SerialNumber

    glucose_manufacturer: str
    glucose_model: str
    glucose_serial: SerialNumber

    bp_manufacturer: str
    bp_model: str
    bp_serial: SerialNumber

    sleep_manufacturer: str
    sleep_model: str
    sleep_serial: SerialNumber

GENDER_MAP = {
    "Male": 1,
    "Female": 2
}

ETHNICITY_MAP = {
    "Mexican American": 1,
    "Other Hispanic": 2,
    "Non-Hispanic White": 3,
    "Non-Hispanic Black": 4,
    "Other Race": 5
}

def map_patient_to_db(patient: PatientCreate) -> dict:
    return {
        "email": patient.email,
        "name": patient.name,
        "dob": patient.dob,
        "gender": GENDER_MAP.get(patient.gender, None),       # NHANES coding
        "ethnicity": ETHNICITY_MAP.get(patient.ethnicity, None),
        "doctor_email": patient.doctor_email,
        "password": patient.password
    }

class LoginForm(BaseModel):
    email: EmailStr
    password: str

class PredictRequest(BaseModel):
    RIDAGEYR: float
    BMXBMI: float
    LBXGH: float
    LBXGH_missing: int
    SBP_mean: float
    LBDHDD: float
    HDL_missing: int
    LBXSCR: float
    LBXGLU: float
    LBXGLU_missing: int
    ACR: float
    ACR_missing: int
    RIAGENDR: int
    RIDRETH3: int

class PredictResponse(BaseModel):
    probability: float = Field(..., description="Diabetes risk probability (0-1)")
    category: str = Field(..., description="Risk category: Low, Medium, High")
    thresholds: Dict[str, float]
    message: str

class Decision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    note: Optional[str] = None

