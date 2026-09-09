import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

BRANDS_PATH = Path(__file__).parents[1] / "data" / "egyptian_brands.json"
CATALOG_PATH = Path(__file__).parents[1] / "data" / "eg_drugs.csv"
RXNORM_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json?name="

CatalogRow = dict[str, Any]

# Expanded regex to capture complex packaging text, slogans, and multi-word tablet counts
_OCR_NOISE_PATTERNS = (
    r"\b(relieves?|reduces?|treats?|lowers?|effective|absorbed|gentle\s+on|sugar\s+coated|film\s+coated|coated|recubiertas?)\b",
    r"\b(v[ií]a\s+de\s+administraci[oó]n|route\s+of\s+administration|oral|formulation|new|pain|relief)\b",
    r"^\s*\d+(?:\.\d+)?\s*(?:mg|mcg|μg|ug|g|ml)\s*$",
    r"^\s*\d+\s*(?:tablets?|tabs?|capsules?|caps?|tabletas?)(?:\s+\w+)*\s*$",
)


def _is_ocr_noise(value: object) -> bool:
    text = " ".join(str(value or "").split())
    if not text:
        return True
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in _OCR_NOISE_PATTERNS)


def normalize_key(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def parse_dosage_mg(value: object) -> float | None:
    if value is None:
        return None
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(mcg|μg|ug|mg|g)\b",
        str(value).lower(),
    )
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)
    if unit in {"mcg", "μg", "ug"}:
        return amount / 1000
    if unit == "g":
        return amount * 1000
    return amount


def _canonical_active(value: object) -> str:
    if value is None:
        return ""
    ingredients = []
    for ingredient in re.split(r"\s*(?:\+|/|,|&)\s*", str(value).lower()):
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


def _catalog_trade_name(value: object) -> str:
    if value is None:
        return ""
    name = re.split(
        r"\s+\d+(?:\.\d+)?\s*(?:mg|mcg|μg|ug|g|ml)\b",
        str(value),
        maxsplit=1,
        flags=re.I,
    )[0]
    return name.strip(" -").title()


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[CatalogRow, ...]:
    if not CATALOG_PATH.exists():
        return ()

    with CATALOG_PATH.open(encoding="utf-8-sig", newline="") as catalog_file:
        rows = csv.DictReader(catalog_file)
        return tuple(
            {
                "name": (row.get("name") or "").strip(),
                "active": (row.get("active") or "").strip(),
                "active_key": _canonical_active(row.get("active", "")),
                "strength_mg": parse_dosage_mg(row.get("name", "")),
                "trade_name": _catalog_trade_name(row.get("name", "")),
                "form": (row.get("form") or "").strip(),
                "barcode": (row.get("barcode") or "").strip(),
            }
            for row in rows
            if (row.get("name") or "").strip()
            and (row.get("active") or "").strip()
        )


@lru_cache(maxsize=1)
def _load_brands() -> dict[str, dict[str, Any]]:
    if not BRANDS_PATH.exists():
        return {}
    with BRANDS_PATH.open(encoding="utf-8") as brands_file:
        raw_brands = json.load(brands_file)
    if not isinstance(raw_brands, dict):
        return {}

    normalized = {}
    for name, details in raw_brands.items():
        if not isinstance(details, dict):
            continue
        generic_name = details.get("generic_name") or details.get("active")
        if not generic_name:
            continue
        normalized[normalize_key(name)] = {
            **details,
            "generic_name": _canonical_active(generic_name),
        }
    return normalized


@lru_cache(maxsize=512)
def _rxnorm_lookup(name: str) -> dict[str, str] | None:
    if not name:
        return None
    try:
        with urlopen(RXNORM_URL + quote(name), timeout=5) as response:
            data = json.load(response)
    except (OSError, ValueError):
        return None

    identifiers = data.get("idGroup", {}).get("rxnormId", [])
    if not identifiers:
        return None

    rxcui = identifiers[0]
    try:
        with urlopen(
            f"https://rxnav.nlm.nih.gov/REST/rxcui/{quote(rxcui)}/properties.json",
            timeout=5,
        ) as response:
            properties = json.load(response).get("properties", {})
    except (OSError, ValueError):
        return {"rxcui": rxcui, "name": name}

    return {
        "rxcui": rxcui,
        "name": _canonical_active(properties.get("name") or name),
    }


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
            "generic_name": next(iter(source_active_keys), source.get("generic_name") if source else None),
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
    if "+" in active_key and dosage_mg is None:
        warning = "Combination medicine without specified dosage; verify individual component strengths with a pharmacist."
    elif dosage_mg is None:
        warning = "Dosage was not provided; verify the strength with a pharmacist."
    elif not alternatives:
        warning = "No dosage-matched alternative is in the medicine catalog."

    return {
        "input_name": brand_name,
        "generic_name": generic_name,
        "alternatives": alternatives,
        "warning": warning,
    }


def normalize_items(items: list[dict] | None) -> dict:
    brands = _load_brands()
    catalog = _load_catalog()
    medications = []
    unresolved = []
    seen_generics = set()

    for item in items or []:
        if not isinstance(item, dict):
            unresolved.append(_unresolved("", "Invalid medicine item."))
            continue
        input_name = item.get("raw_text") or item.get("drug_name_guess") or ""
        drug_name = item.get("drug_name_guess") or input_name
        
        if _is_ocr_noise(input_name) or _is_ocr_noise(drug_name):
            continue
            
        dosage_mg = parse_dosage_mg(item.get("dosage_guess") or input_name)
        lookup_name = normalize_key(drug_name)
        brand = brands.get(lookup_name)
        catalog_matches = [
            row for row in catalog
            if normalize_key(row["trade_name"]) == lookup_name
            or normalize_key(row["trade_name"]).startswith(lookup_name + " ")
        ]

        matched_med = None

        if brand:
            matched_med = {
                "input_name": input_name,
                "generic_name": brand["generic_name"],
                "dosage_mg": dosage_mg,
                "rxnorm_id": brand.get("rxnorm_id"),
                "match_method": "brand_table",
                "match_confidence": 1.0,
                "explanation_en": "",
                "explanation_ar": "",
            }
        elif catalog_matches:
            catalog_match = catalog_matches[0]
            matched_med = {
                "input_name": input_name,
                "generic_name": catalog_match["active_key"],
                "dosage_mg": dosage_mg or catalog_match["strength_mg"],
                "rxnorm_id": None,
                "match_method": "eg_drugs_catalog",
                "match_confidence": min(float(item.get("confidence", 0.8)), 0.95),
                "explanation_en": "",
                "explanation_ar": "",
            }
        else:
            rxnorm_match = _rxnorm_lookup(lookup_name) if lookup_name else None
            if rxnorm_match:
                matched_med = {
                    "input_name": input_name,
                    "generic_name": rxnorm_match["name"],
                    "dosage_mg": dosage_mg,
                    "rxnorm_id": rxnorm_match["rxcui"],
                    "match_method": "rxnorm",
                    "match_confidence": min(float(item.get("confidence", 0.8)), 0.9),
                    "explanation_en": "",
                    "explanation_ar": "",
                }

        if matched_med:
            # Deduplicate by active generic ingredient
            gen_key = matched_med["generic_name"]
            if gen_key not in seen_generics:
                seen_generics.add(gen_key)
                medications.append(matched_med)
            continue

        unresolved.append(_unresolved(
            input_name,
            "No match in brand table or RxNorm; LLM review is required.",
        ))

    return {"medications": medications, "unresolved": unresolved}