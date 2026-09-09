from fastapi import APIRouter
from pydantic import BaseModel

from services.interaction import check_interactions

router = APIRouter()


class Medication(BaseModel):
    input_name: str = ""
    generic_name: str = ""
    dosage_mg: float | None = None
    rxnorm_id: str = ""
    match_method: str = ""
    match_confidence: float = 0.0
    explanation_en: str = ""
    explanation_ar: str = ""


class CheckRequest(BaseModel):
    medications: list[Medication] = []


@router.post("/check")
async def check(payload: CheckRequest) -> dict:
    medications = [m.model_dump() for m in payload.medications]
    return check_interactions(medications)
