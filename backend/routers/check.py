from fastapi import APIRouter
from pydantic import BaseModel

from services.duplicates import find_duplicate_active_ingredients
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
    """Both hazards in one call: drug-drug interactions, and the same active
    ingredient arriving under two brand names (which no interaction database
    flags, since it isn't a pair of different drugs)."""
    medications = [m.model_dump() for m in payload.medications]

    if not medications:
        return {"interactions": [], "duplicate_active_ingredients": []}

    result = check_interactions(medications)
    return {
        **result,
        "duplicate_active_ingredients": find_duplicate_active_ingredients(medications),
    }
