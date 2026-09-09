import sqlite3

from ddinter.repository import Repository, connect, database_path
from ddinter.service import InteractionService
from services.duplicates import find_duplicate_active_ingredients


def check_interactions(medications: list[dict]) -> dict:
    """Check normalized generic names against the local DDInter catalog."""
    duplicates = find_duplicate_active_ingredients(medications)
    
    # Extract active ingredients and split combination drugs (e.g. "caffeine+paracetamol")
    individual_names = set()
    for medication in medications:
        generic = medication.get("generic_name", "")
        if generic:
            for ingredient in generic.split("+"):
                cleaned = ingredient.strip()
                if cleaned:
                    individual_names.add(cleaned)

    names = list(individual_names)

    result = {
        "interactions": [],
        "duplicate_active_ingredients": duplicates,
    }
    if len(names) < 2:
        return result

    try:
        connection = connect(database_path(), readonly=True)
    except sqlite3.Error:
        result["status"] = "catalog_unavailable"
        result["warning"] = (
            "The DDInter catalog is not available. An empty interaction list "
            "does not establish that the medications are safe together."
        )
        return result

    try:
        response = InteractionService(Repository(connection)).check_names(names)
        result["interactions"] = [
            pair.model_dump(mode="json") for pair in response.interactions
        ]
        result["status"] = response.status
        result["no_record_pairs"] = [
            pair.model_dump(mode="json") for pair in response.no_record_pairs
        ]
        result["resolutions"] = [
            resolution.model_dump(mode="json") for resolution in response.resolutions
        ]
        result["notice"] = response.notice
        return result
    finally:
        connection.close()