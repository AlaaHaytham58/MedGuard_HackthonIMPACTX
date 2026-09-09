"""Drug-drug interaction checking backed by the local DDInter catalog.

Every verdict here comes from the catalog, never from the vision model — that
boundary is the product's core claim. When the catalog cannot be opened we say
so explicitly rather than returning an empty list, because an empty list reads
as "safe" and would be the most dangerous possible failure mode.
"""

import sqlite3

from ddinter.repository import Repository, connect, database_path
from ddinter.service import InteractionService

CATALOG_WARNING = (
    "The interaction catalog is unavailable, so no combination could be checked. "
    "An empty result here does NOT mean these medicines are safe together."
)

NO_RECORD_NOTICE = (
    "No record found does not establish that a drug combination is medically safe."
)


def _drug_names(medications: list[dict]) -> tuple[list[str], list[str]]:
    """Split normalized medications into checkable generic names and unresolved inputs."""
    names, unresolved = [], []
    for medication in medications:
        generic_name = (medication.get("generic_name") or "").strip()
        if generic_name:
            names.append(generic_name)
        else:
            unresolved.append(medication.get("input_name") or "")
    return names, unresolved


def _pair(result) -> dict:
    interaction = result.interaction
    return {
        "drug_a": result.drug_a.canonical_name,
        "drug_b": result.drug_b.canonical_name,
        "drug_a_id": result.drug_a.id,
        "drug_b_id": result.drug_b.id,
        "severity": interaction.severity if interaction else None,
        "severity_rank": result.severity_rank,
        "description": (interaction.description or interaction.interaction_text) if interaction else None,
        "mechanism": interaction.mechanism if interaction else None,
        "management": interaction.management if interaction else None,
        "pair_id": interaction.pair_id if interaction else None,
        "source": "ddinter",
    }


def check_interactions(medications: list[dict]) -> dict:
    names, unresolved_input = _drug_names(medications)

    if len(names) < 2:
        return {
            "status": "insufficient_distinct_drugs",
            "interactions": [],
            "no_record_pairs": [],
            "unresolved": unresolved_input,
            "comparisons": 0,
            "notice": "At least two identified medicines are needed to check a combination.",
            "warning": None,
        }

    try:
        connection = connect(database_path(), readonly=True)
    except sqlite3.Error:
        return {
            "status": "catalog_unavailable",
            "interactions": [],
            "no_record_pairs": [],
            "unresolved": unresolved_input,
            "comparisons": 0,
            "notice": NO_RECORD_NOTICE,
            "warning": CATALOG_WARNING,
        }

    try:
        response = InteractionService(Repository(connection)).check_names(names)
    finally:
        connection.close()

    unresolved = unresolved_input + [
        resolution.input_name
        for resolution in response.resolutions
        if resolution.status == "unresolved"
    ]

    return {
        "status": response.status,
        "interactions": [_pair(item) for item in response.interactions],
        "no_record_pairs": [_pair(item) for item in response.no_record_pairs],
        "unresolved": unresolved,
        "comparisons": response.comparisons,
        "notice": NO_RECORD_NOTICE,
        "warning": None,
    }
