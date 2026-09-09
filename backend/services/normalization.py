import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


BRANDS_PATH = Path(__file__).parents[1] / "data" / "egyptian_brands.json"
CATALOG_PATH = Path(__file__).parents[1] / "data" / "eg_drugs.csv"
RXNORM_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json?name="


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def parse_dosage_mg(value: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*mg\b", value.lower())
    return float(match.group(1)) if match else None


def _canonical_active(value: str) -> str:
    ingredients = []
    for ingredient in value.lower().split("+"):
        ingredient = re.sub(r"\([^)]*\)", "", ingredient)
        ingredient = re.sub(
            r"\b(fumarate|hydrochloride|sodium|calcium|potassium|maleate)\b",
            "",
            ingredient,
        )
        ingredient = normalize_key(ingredient)
        if ingredient:
            ingredients.append(ingredient)
    return "+".join(sorted(set(ingredients)))


def _catalog_trade_name(value: str) -> str:
    name = re.split(r"\s+\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b", value, maxsplit=1, flags=re.I)[0]
    return name.strip(" -").title()


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[dict[str, str], ...]:
    if not CATALOG_PATH.exists():
        return ()

    with CATALOG_PATH.open(encoding="utf-8-sig", newline="") as catalog_file:
        rows = csv.DictReader(catalog_file)
        return tuple(
            {
                "name": row.get("name", "").strip(),
                "active": row.get("active", "").strip(),
                "active_key": _canonical_active(row.get("active", "")),
                "strength_mg": parse_dosage_mg(row.get("name", "")),
                "trade_name": _catalog_trade_name(row.get("name", "")),
                "form": row.get("form", "").strip(),
                "barcode": row.get("barcode", "").strip(),
            }
            for row in rows
            if row.get("name", "").strip() and row.get("active", "").strip()
        )


def _load_brands() -> dict[str, dict[str, str | None]]:
    if not BRANDS_PATH.exists():
        return {}
    with BRANDS_PATH.open(encoding="utf-8") as brands_file:
        raw_brands = json.load(brands_file)
    return {normalize_key(name): details for name, details in raw_brands.items()}


def _rxnorm_lookup(name: str) -> str | None:
    try:
        with urlopen(RXNORM_URL + quote(name), timeout=5) as response:
            data = json.load(response)
    except (OSError, ValueError):
        return None

    identifiers = data.get("idGroup", {}).get("rxnormId", [])
    return identifiers[0] if identifiers else None


def _unresolved(input_name: str, reason: str) -> dict:
    return {"input_name": input_name, "reason": reason}


def find_alternatives(
    brand_name: str,
    dosage_mg: float | None = None,
    limit: int = 3,
) -> dict:
    brands = _load_brands()
    source_key = normalize_key(brand_name)
    source = brands.get(source_key)
    catalog = _load_catalog()

    exact_catalog_rows = [
        row for row in catalog
        if normalize_key(row["trade_name"]) == source_key
    ]
    family_catalog_rows = exact_catalog_rows or [
        row for row in catalog
        if normalize_key(row["trade_name"]).startswith(source_key + " ")
    ]
    source_catalog_rows = family_catalog_rows
    if dosage_mg is not None:
        source_catalog_rows = [
            row for row in source_catalog_rows
            if row["strength_mg"] == dosage_mg
        ]

        # A base brand such as Panadol may have both single-ingredient and
        # combination variants at the same strength. Prefer the uncombined
        # records when the caller provides only the base brand and dosage.
        single_ingredient_rows = [
            row for row in source_catalog_rows
            if "+" not in row["active_key"]
        ]
        if single_ingredient_rows:
            source_catalog_rows = single_ingredient_rows

    if not source and not family_catalog_rows:
        return {
            "input_name": brand_name,
            "generic_name": None,
            "alternatives": [],
            "warning": "This brand is not in the medicine catalog.",
        }

    source_active_keys = {
        row["active_key"] for row in source_catalog_rows
    }
    if len(source_active_keys) > 1:
        return {
            "input_name": brand_name,
            "generic_name": None,
            "alternatives": [],
            "warning": (
                "This brand name refers to multiple active ingredients. "
                "Provide the exact product name or dosage."
            ),
        }

    if not source_catalog_rows and dosage_mg is not None:
        return {
            "input_name": brand_name,
            "generic_name": next(iter(source_active_keys)),
            "alternatives": [],
            "warning": (
                "The catalog identifies this medicine, but does not record "
                "the requested strength for a safe alternative match."
            ),
        }

    generic_name = (
        source["generic_name"]
        if source
        else source_catalog_rows[0]["active_key"]
    )
    active_key = _canonical_active(generic_name)
    if source_catalog_rows:
        active_key = source_catalog_rows[0]["active_key"]
        generic_name = active_key

    if "+" in active_key and dosage_mg is None:
        return {
            "input_name": brand_name,
            "generic_name": generic_name,
            "alternatives": [],
            "warning": (
                "This is a combination medicine. Exact active-ingredient "
                "strengths are not recorded, so alternatives cannot be verified."
            ),
        }

    alternatives = []
    seen_names = set()
    for candidate in catalog:
        if candidate["active_key"] != active_key:
            continue
        if normalize_key(candidate["trade_name"]) == source_key:
            continue
        if dosage_mg is not None and candidate["strength_mg"] != dosage_mg:
            continue
        if candidate["trade_name"] in seen_names:
            continue

        alternatives.append({
            "trade_name": candidate["trade_name"],
            "generic_name": generic_name,
            "dosage_mg": candidate["strength_mg"],
            "form": candidate["form"] or None,
            "barcode": candidate["barcode"] or None,
            "same_active_ingredient": True,
            "same_dosage": dosage_mg is not None and candidate["strength_mg"] == dosage_mg,
            "source": "eg_drugs_catalog",
        })
        seen_names.add(candidate["trade_name"])
        if len(alternatives) == limit:
            break

    warning = None
    if dosage_mg is None:
        warning = "Dosage was not provided; verify the strength with a pharmacist."
    elif not alternatives:
        warning = "No dosage-matched alternative is in the medicine catalog."

    return {
        "input_name": brand_name,
        "generic_name": generic_name,
        "alternatives": alternatives,
        "warning": warning,
    }


def normalize_items(items: list[dict]) -> dict:
    brands = _load_brands()
    catalog = _load_catalog()
    medications = []
    unresolved = []

    for item in items:
        input_name = item.get("raw_text") or item.get("drug_name_guess") or ""
        drug_name = item.get("drug_name_guess") or input_name
        dosage_mg = parse_dosage_mg(item.get("dosage_guess") or input_name)
        lookup_name = normalize_key(drug_name)
        brand = brands.get(lookup_name)
        catalog_matches = [
            row for row in catalog
            if normalize_key(row["trade_name"]) == lookup_name
        ]

        if brand:
            medications.append({
                "input_name": input_name,
                "generic_name": brand["generic_name"],
                "dosage_mg": dosage_mg,
                "rxnorm_id": brand.get("rxnorm_id"),
                "match_method": "brand_table",
                "match_confidence": 1.0,
                "explanation_en": "",
                "explanation_ar": "",
            })
            continue

        if catalog_matches:
            catalog_match = catalog_matches[0]
            medications.append({
                "input_name": input_name,
                "generic_name": catalog_match["active_key"],
                "dosage_mg": dosage_mg or catalog_match["strength_mg"],
                "rxnorm_id": None,
                "match_method": "eg_drugs_catalog",
                "match_confidence": min(float(item.get("confidence", 0.8)), 0.95),
                "explanation_en": "",
                "explanation_ar": "",
            })
            continue

        rxnorm_id = _rxnorm_lookup(lookup_name) if lookup_name else None
        if rxnorm_id:
            medications.append({
                "input_name": input_name,
                "generic_name": lookup_name,
                "dosage_mg": dosage_mg,
                "rxnorm_id": rxnorm_id,
                "match_method": "rxnorm",
                "match_confidence": min(float(item.get("confidence", 0.8)), 0.9),
                "explanation_en": "",
                "explanation_ar": "",
            })
            continue

        unresolved.append(_unresolved(
            input_name,
            "No match in brand table or RxNorm; LLM review is required.",
        ))

    return {"medications": medications, "unresolved": unresolved}
