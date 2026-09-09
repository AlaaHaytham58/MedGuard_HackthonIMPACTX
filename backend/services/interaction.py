from services.duplicates import find_duplicate_active_ingredients


def check_interactions(medications: list[dict]) -> dict:
    """/check's core logic, per Backend_Integration_Guide.md.

    DDInter-backed drug-drug interaction matching is separate follow-up work
    (needs the sqlite ingestion); duplicate active-ingredient detection needs
    no external data source, since generic_name is already on every
    medication coming out of /normalize, so it ships now.
    """
    return {
        "interactions": [],
        "duplicate_active_ingredients": find_duplicate_active_ingredients(medications),
    }
