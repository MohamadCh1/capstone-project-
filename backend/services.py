import uuid
import joblib
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os
from passlib.context import CryptContext
from datetime import datetime, timezone
from decimal import Decimal
import json

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
THRESHOLDS_PATH = os.path.join(BASE_DIR, "..", "models", "calibrated_Logistic_regression_model_risk_thresholds.joblib")
FEATURES_PATH = os.path.join(BASE_DIR,"..","models","calibrated_Logistic_regression_model_feature_columns.joblib")
MODEL_PATH = os.path.join(BASE_DIR,"..","models","calibrated_Logistic_regression_model.joblib")
LOW_TH = joblib.load(THRESHOLDS_PATH)['low']
HIGH_TH = joblib.load(THRESHOLDS_PATH)['high']

def calculate_age(dob_int: int) -> int:
    dob = datetime.fromtimestamp(dob_int, tz=timezone.utc).date()
    today = datetime.now(timezone.utc).date()

    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def to_serializable(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)  

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

class RiskService:
    def __init__(self, patients_repo, prediction_repo):
        self.model = joblib.load(MODEL_PATH)
        self.feature_cols = joblib.load(FEATURES_PATH)
        self.patients = patients_repo
        self.prediction_repo = prediction_repo

    def _assemble_df(self, payload: Dict) -> pd.DataFrame:
        payload["RIDAGEYR"] = calculate_age(payload["RIDAGEYR"])
        print(payload["RIDAGEYR"])
        missing = [c for c in self.feature_cols if c not in payload]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        return pd.DataFrame([[payload[c] for c in self.feature_cols]], columns=self.feature_cols)
    
    def _categorize(self, p: float) -> str:
        if p < LOW_TH: return "Low"
        if p < HIGH_TH: return "Medium"
        return "High"

    def _explain(self, raw: Dict) -> List[str]:
        report = []
        if "LBXGLU" in raw:
            val = raw["LBXGLU"]
            if val < 100:
                report.append(
                    f"Your blood sugar level is {val:.2f} mg/dL, which is healthy. "
                    "This shows your body is managing sugar well."
                )
            elif val < 126:
                report.append(
                    f"Your blood sugar level is {val:.2f} mg/dL. "
                    "This falls in the prediabetes range, meaning your body is beginning to struggle with sugar control. "
                    "It’s a sign to pay attention to diet and lifestyle now to prevent future problems."
                )
            else:
                report.append(
                    f"Your blood sugar level is {val:.2f} mg/dL, which is in the diabetes range. "
                    "This means your body is having difficulty managing sugar. "
                    "High sugar over time can affect your heart, kidneys, and eyes, so medical follow‑up is important."
                )

        # BMI
        if "BMXBMI" in raw:
            val = raw["BMXBMI"]
            if val < 18.5:
                report.append(
                    f"Your BMI is {val:.1f}, which is underweight. "
                    "This may mean your body isn’t getting enough nutrition."
                )
            elif val < 25:
                report.append(
                    f"Your BMI is {val:.1f}, which is in the healthy range. "
                    "This suggests your weight is well balanced for your height."
                )
            elif val < 30:
                report.append(
                    f"Your BMI is {val:.1f}, which is in the overweight range. "
                    "Carrying extra weight can put strain on your heart and joints."
                )
            else:
                report.append(
                    f"Your BMI is {val:.1f}, which is in the obesity range. "
                    "This increases risk for diabetes and heart disease."
                )

        # Blood Pressure
        if "SBP_mean" in raw:
            val = raw["SBP_mean"]
            if val < 120:
                report.append(
                    f"Your average systolic blood pressure is {val:.0f} mmHg, which is healthy."
                )
            elif val < 140:
                report.append(
                    f"Your average systolic blood pressure is {val:.0f} mmHg, which is elevated. "
                    "This means your heart is working harder than normal."
                )
            else:
                report.append(
                    f"Your average systolic blood pressure is {val:.0f} mmHg, which is high. "
                    "This puts extra strain on your heart and kidneys."
                )

        # Kidney Health (ACR)
        if "ACR" in raw:
            val = raw["ACR"]
            if val < 30:
                report.append(
                    f"Your urine albumin‑to‑creatinine ratio (ACR) is {val:.1f} mg/g, which is healthy for kidney function."
                )
            elif val <= 300:
                report.append(
                    f"Your ACR is {val:.1f} mg/g, which suggests early kidney stress. "
                    "This means your kidneys may be under pressure."
                )
            else:
                report.append(
                    f"Your ACR is {val:.1f} mg/g, which is very high. "
                    "This indicates significant kidney disease risk."
                )

        if not report:
            return "We could not generate a detailed health report based on your data."

        # Add supportive closing
        report.append(
            "The good news is that many of these numbers can be improved with healthy habits and medical guidance. "
            "Small changes, like adjusting diet, increasing activity, or following your doctor’s advice, often make a big difference."
        )
        print(report)
        return " ".join(report)
    
    async def predict_and_record(self, patient_email: str, payload: Dict) -> Dict:
        df = self._assemble_df(payload)
        proba = float(self.model.predict_proba(df)[:, 1][0])
        category = self._categorize(proba)
        explanation = self._explain(payload)
        await self.patients.update_risk(patient_email, category)
        await self.prediction_repo.insert_prediction(patient_email, proba, category, explanation)
        return {"probability": round(proba, 4), "category": category,
                "thresholds": {"low": LOW_TH, "high": HIGH_TH}, "explanation": explanation}

class MedicalService:
    def __init__(self, suggestions_repo):
        self.suggestions = suggestions_repo

    async def generate_suggestions(
        self,
        patient_email: str,
        hba1c: float,
        glucose: float,
        bmi: float,
        sbp: int
    ) -> List[Dict]:

        def make_suggestion(details: str, priority: str) -> Dict:
            return {
                "id": str(uuid.uuid4()),
                "patient_email": patient_email,
                "source_type": "ai",
                "category": "medication",
                "details": {"text": details},  # dict form
                "priority": priority,
                "status": "proposed"
            }

        suggestions: List[Dict] = []

        # HbA1c rules
        if hba1c >= 10:
            suggestions.append(make_suggestion(
                "Start basal insulin at 10 units/day and continue metformin 1000 mg twice daily.",
                "high"
            ))
        elif hba1c >= 9:
            suggestions.append(make_suggestion(
                "Initiate triple therapy: metformin 1000 mg twice daily, empagliflozin 10 mg daily, and liraglutide titrated to 1.8 mg.",
                "high"
            ))
        elif hba1c >= 7.5:
            suggestions.append(make_suggestion(
                "Begin dual therapy: metformin 1000 mg twice daily and empagliflozin 10 mg daily.",
                "medium"
            ))
        elif hba1c >= 6.5:
            suggestions.append(make_suggestion(
                "Start metformin 500 mg twice daily and titrate to 1000 mg twice daily as tolerated.",
                "low"
            ))

        # Glucose rule
        if glucose >= 126 and hba1c < 6.5:
            suggestions.append(make_suggestion(
                "Start metformin 500 mg twice daily for impaired fasting glucose.",
                "low"
            ))

        # BMI rule
        if bmi >= 30:
            suggestions.append(make_suggestion(
                "Add semaglutide 0.25 mg weekly, titrate to 1 mg weekly for weight reduction.",
                "medium"
            ))

        # SBP rule
        if sbp >= 140:
            suggestions.append(make_suggestion(
                "Add lisinopril 10 mg daily or losartan 50 mg daily for hypertension control.",
                "high"
            ))

        if suggestions:
            await self.suggestions.add_many(patient_email, suggestions)
        return suggestions
