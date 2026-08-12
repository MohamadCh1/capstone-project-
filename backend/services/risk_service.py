import joblib
import pandas as pd
import os
from typing import Dict
from datetime import datetime, timezone

from backend.utils import BASE_DIR

THRESHOLDS_PATH = os.path.join(BASE_DIR, "..", "models", "calibrated_Logistic_regression_model_risk_thresholds.joblib")
FEATURES_PATH = os.path.join(BASE_DIR, "..", "models", "calibrated_Logistic_regression_model_feature_columns.joblib")
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "calibrated_Logistic_regression_model.joblib")

# Loaded once at module import time (i.e. once per process), not once per
# RiskService construction. LOW_TH/HIGH_TH already worked this way; MODEL and
# FEATURE_COLS previously reloaded from disk in __init__ on every request.
LOW_TH = joblib.load(THRESHOLDS_PATH)['low']
HIGH_TH = joblib.load(THRESHOLDS_PATH)['high']
MODEL = joblib.load(MODEL_PATH)
FEATURE_COLS = joblib.load(FEATURES_PATH)

def calculate_age(dob_int: int) -> int:
    dob = datetime.fromtimestamp(dob_int, tz=timezone.utc).date()
    today = datetime.now(timezone.utc).date()

    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


class RiskService:
    def __init__(self, patients_repo, prediction_repo):
        self.model = MODEL
        self.feature_cols = FEATURE_COLS
        self.patients = patients_repo
        self.prediction_repo = prediction_repo

    def _assemble_df(self, payload: Dict) -> pd.DataFrame:
        payload = dict(payload)  # work on a copy - don't mutate the caller's dict
        payload["RIDAGEYR"] = calculate_age(payload["RIDAGEYR"])
        missing = [c for c in self.feature_cols if c not in payload]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        return pd.DataFrame([[payload[c] for c in self.feature_cols]], columns=self.feature_cols)

    def _categorize(self, p: float) -> str:
        if p < LOW_TH: return "Low"
        if p < HIGH_TH: return "Medium"
        return "High"

    def _explain(self, raw: Dict) -> str:
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
        return " ".join(report)

    async def predict_and_record(self, patient_email: str, payload: Dict) -> Dict:
        df = self._assemble_df(payload)
        proba = float(self.model.predict_proba(df)[:, 1][0])
        category = self._categorize(proba)
        explanation = self._explain(payload)

        await self.prediction_repo.insert_prediction(patient_email, proba, category, explanation)
        await self.patients.update_risk(patient_email, category)

        return {"probability": round(proba, 4), "category": category,
                "thresholds": {"low": LOW_TH, "high": HIGH_TH}, "explanation": explanation}
