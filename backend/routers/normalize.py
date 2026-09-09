from fastapi import APIRouter

from services.normalization import find_alternatives, normalize_items


router = APIRouter()


@router.post("/normalize")
def normalize(payload: dict) -> dict:
    return normalize_items(payload.get("items", []))


@router.post("/alternatives")
def alternatives(payload: dict) -> dict:
    return find_alternatives(
        payload.get("brand_name", ""),
        payload.get("dosage_mg"),
    )
