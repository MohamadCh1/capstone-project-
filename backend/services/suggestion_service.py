import uuid
from typing import Dict, List


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
