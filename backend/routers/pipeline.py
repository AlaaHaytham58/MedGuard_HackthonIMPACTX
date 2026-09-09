from fastapi import APIRouter, File, HTTPException, UploadFile

from services.interaction import check_interactions
from services.normalization import normalize_items
from services.vision import extract_drugs


router = APIRouter()

MAX_IMAGES = 4
MAX_SIZE_BYTES = 8 * 1024 * 1024


def _report_drugs(medications: list[dict]) -> list[dict]:
    report_drugs = []
    seen_ingredients = set()
    for medication in medications:
        ingredient = medication.get("generic_name") or "unknown"
        ingredient_key = " ".join(ingredient.casefold().split())
        if ingredient_key in seen_ingredients:
            continue
        seen_ingredients.add(ingredient_key)
        report_drugs.append({
            "brand": medication.get("input_name") or ingredient or "Unknown medicine",
            "ingredient": ingredient or "Unknown ingredient",
            "source": medication.get("match_method") or "backend normalization",
        })
    return report_drugs


def _frontend_report(normalized: dict, interactions: dict) -> dict:
    medications = normalized.get("medications", [])
    raw_interactions = interactions.get("interactions", [])
    unresolved = normalized.get("unresolved", [])

    drugs = [
        {
            "brand": medication.get("input_name") or medication.get("generic_name") or "Unknown medicine",
            "ingredient": medication.get("generic_name") or "Unknown ingredient",
            "source": medication.get("match_method") or "backend normalization",
        }
        for medication in medications
    ]

    interaction_pairs = []
    management_set = set()

    for item in raw_interactions:
        # DDInter pair dict formatting
        pair_dict = item.model_dump() if hasattr(item, "model_dump") else item

        drug_a_name = (
            pair_dict.get("drug_a", {}).get("canonical_name")
            or pair_dict.get("drug_a_name")
            or "Medicine A"
        )
        drug_b_name = (
            pair_dict.get("drug_b", {}).get("canonical_name")
            or pair_dict.get("drug_b_name")
            or "Medicine B"
        )

        interaction_info = (
            pair_dict.get("interaction")
            if isinstance(pair_dict.get("interaction"), dict)
            else pair_dict
        )

        severity = interaction_info.get("severity", "Major")
        description = (
            interaction_info.get("interaction_text")
            or interaction_info.get("description")
            or f"A {severity} interaction was found between {drug_a_name} and {drug_b_name}."
        )
        mgmt = (
            interaction_info.get("management")
            or "Caution is recommended when coadministering these medications. Consult a doctor or pharmacist."
        )

        management_set.add(mgmt)

        interaction_pairs.append({
            "drug_a": drug_a_name,
            "drug_b": drug_b_name,
            "severity": severity,
            "description": description,
            "management": mgmt,
        })

    if interaction_pairs:
        combined_descriptions = "\n\n".join([pair["description"] for pair in interaction_pairs])

        return {
            "drugs": drugs,
            "verdict": "danger",
            "verdictHeadline": f"These medicines may interact ({len(interaction_pairs)} pair(s) found)",
            "interaction": combined_descriptions,
            "interactionPairs": interaction_pairs,
            "management": list(management_set),
            "alternatives": [],
            "checkedLabel": "Just now",
            "status": "interaction_found",
            "unresolved": unresolved,
        }

    if unresolved:
        headline = "We could not identify every medicine"
        interaction_text = "The result is incomplete because one or more medicines could not be matched to the verified catalog."
        status = "unresolved"
    else:
        headline = "No verified interaction record was found"
        interaction_text = "No interaction record was found for this combination. This does not prove that the medicines are safe together."
        status = "no_record_found"

    return {
        "drugs": drugs,
        "verdict": "unknown",
        "verdictHeadline": headline,
        "interaction": interaction_text,
        "interactionPairs": [],
        "management": ["Ask a doctor or pharmacist before taking these medicines together."],
        "alternatives": [],
        "checkedLabel": "Just now",
        "status": status,
        "unresolved": unresolved,
    }

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
        interactions = check_interactions(normalized["medications"])
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

    return _frontend_report(normalized, interactions)
