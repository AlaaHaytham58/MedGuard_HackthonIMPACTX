def check_interactions(medications: list[dict]) -> dict:
    """Return the interaction-engine contract until B connects DDInter."""
    return {
        "interactions": [],
        "status": "not_configured",
        "warning": (
            "DDInter is not connected yet. Do not interpret an empty list "
            "as confirmation that the medications are safe together."
        ),
    }
