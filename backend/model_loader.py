import joblib
import numpy as np


MODEL_PATH = "../models/calibrated_Logistic_regression_model.joblib"
FEATURES_PATH = "../models/calibrated_Logistic_regression_model_feature_columns.joblib"
THRESHOLDS_PATH = "../models/calibrated_Logistic_regression_model_risk_thresholds.joblib"

_model = None
_feature_columns = None
_thresholds = None

def load_data():
    global _model, _feature_columns, _thresholds
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    if _feature_columns is None:
        _feature_columns = joblib.load(FEATURES_PATH)
    if _thresholds is None:
        _thresholds = joblib.load(THRESHOLDS_PATH)
    return _model, _feature_columns, _thresholds

def categorize_risk(p: float, thresholds: dict) -> str:
    if p < thresholds["low"]:
        return "Low"
    elif p < thresholds["high"]:
        return "Medium"
    else:
        return "High"

import pandas as pd

def assemble_feature_vector(payload: dict, feature_columns: list) -> pd.DataFrame:
    values = []
    missing = []
    for col in feature_columns:
        if col in payload:
            values.append(payload[col])
        else:
            values.append(None)
            missing.append(col)
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    
    return pd.DataFrame([values], columns=feature_columns)