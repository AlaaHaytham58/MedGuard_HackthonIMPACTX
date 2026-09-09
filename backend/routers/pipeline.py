from fastapi import APIRouter, File, HTTPException, UploadFile

from services.duplicates import find_duplicate_active_ingredients
from services.interaction import check_interactions
from services.normalization import find_alternatives, normalize_items
from services.vision import extract_drugs


router = APIRouter()

MAX_IMAGES = 4
MAX_SIZE_BYTES = 8 * 1024 * 1024


def _alternatives_for(medications: list[dict], items: list[dict]) -> list[dict]:
    """Same-ingredient substitutes for each identified medicine.

    Looked up by the brand the vision step read rather than by `input_name`: the
    catalog is keyed on trade names, while `input_name` is the whole OCR line
    ("BRUFEN 400 mg Ibuprofen"), which matches nothing.
    """
    brand_by_raw_text = {
        item.get("raw_text") or "": item.get("drug_name_guess") or ""
        for item in items
        if isinstance(item, dict)
    }

    results = []
    for medication in medications:
        input_name = medication.get("input_name") or ""
        brand = brand_by_raw_text.get(input_name) or input_name
        if not brand:
            continue
        results.append(find_alternatives(brand, medication.get("dosage_mg")))
    return results


@router.post("/pipeline")
async def pipeline(images: list[UploadFile] = File(...)) -> dict:
    if not images or len(images) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "BAD_IMAGE_COUNT",
                "message": f"Send 1-{MAX_IMAGES} images",
                "details": {},
            },
        )

    image_bytes_list = []
    for image in images:
        content = await image.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "EMPTY_IMAGE",
                    "message": f"{image.filename} is empty",
                    "details": {},
                },
            )
        if len(content) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "IMAGE_TOO_LARGE",
                    "message": f"{image.filename} exceeds 8MB",
                    "details": {},
                },
            )
        image_bytes_list.append(content)

    try:
        extracted = extract_drugs(image_bytes_list)
        normalized = normalize_items(extracted.get("items", []))
        medications = normalized["medications"]
        interactions = check_interactions(medications)
        duplicates = find_duplicate_active_ingredients(medications)
        alternatives = _alternatives_for(medications, extracted.get("items", []))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": True,
                "code": "PIPELINE_UNAVAILABLE",
                "message": str(exc),
                "details": {},
            },
        ) from exc

    return {
        "extracted": extracted,
        "normalized": normalized,
        "interactions": interactions,
        "duplicates": duplicates,
        "alternatives": alternatives,
    }
