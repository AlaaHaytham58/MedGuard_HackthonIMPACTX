import re

# Common salt/ester/hydrate suffixes that show up appended to an active
# ingredient name (e.g. "metformin hydrochloride", "bisoprolol fumarate").
# Two brands of the same drug won't always be normalized to the same salt
# form upstream, so strip these before grouping or real duplicates get missed.
_SALT_SUFFIXES = {
    "hydrochloride", "hcl", "sodium", "potassium", "calcium",
    "sulfate", "sulphate", "fumarate", "maleate", "tartrate", "bitartrate",
    "citrate", "besylate", "mesylate", "succinate", "phosphate", "acetate",
    "dihydrate", "monohydrate", "trihydrate", "anhydrous",
}

# Combination drugs list more than one active ingredient in generic_name
# (e.g. "amoxicillin/clavulanate", "amoxicillin + clavulanate").
_INGREDIENT_SEPARATORS = re.compile(r"[/+;,&]| and | with ", re.IGNORECASE)

_PARENTHETICAL = re.compile(r"\([^)]*\)")


def _normalize_ingredient(raw: str) -> str:
    text = _PARENTHETICAL.sub(" ", raw).lower().strip()
    words = [w for w in re.split(r"\s+", text) if w]
    while words and words[-1] in _SALT_SUFFIXES:
        words.pop()
    return " ".join(words)


def _split_ingredients(generic_name: str) -> list[str]:
    if not generic_name:
        return []
    parts = _INGREDIENT_SEPARATORS.split(generic_name)
    seen: dict[str, None] = {}
    for part in parts:
        normalized = _normalize_ingredient(part)
        if normalized:
            seen.setdefault(normalized, None)
    return list(seen)


def _dedupe_products(meds: list[dict]) -> list[dict]:
    """Collapses entries that are the same physical product (e.g. the same
    box photographed twice) so they don't flag as a "duplicate" against
    themselves. Entries without an input_name are never collapsed together,
    since there's no signal they're the same product.
    """
    seen_names: set[str] = set()
    unique_meds = []
    for med in meds:
        name = (med.get("input_name") or "").strip().lower()
        if name and name in seen_names:
            continue
        if name:
            seen_names.add(name)
        unique_meds.append(med)
    return unique_meds


def _display_name(med: dict) -> str:
    input_name = med.get("input_name")
    if input_name:
        return input_name
    generic_name = med.get("generic_name") or "this medication"
    dosage_mg = med.get("dosage_mg")
    return f"{generic_name} ({dosage_mg}mg)" if dosage_mg else generic_name


def _join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def find_duplicate_active_ingredients(medications: list[dict]) -> list[dict]:
    """Groups normalized medications by active ingredient and flags any
    ingredient taken under 2+ different brand/input names.

    This catches the "Panadol + Adol + Fevadol" overdose scenario — same
    active ingredient, different brand names — which a drug-drug interaction
    database like DDInter has no reason to flag, since it isn't a pair of
    different drugs. Input matches the `/normalize` -> `/check` contract:
    each medication needs a non-empty `generic_name`; entries without one
    (already reported under `unresolved` by /normalize) are skipped.
    """
    ingredient_to_meds: dict[str, list[dict]] = {}

    for med in medications:
        generic_name = med.get("generic_name") or ""
        for ingredient in _split_ingredients(generic_name):
            ingredient_to_meds.setdefault(ingredient, []).append(med)

    duplicates = []
    for ingredient, meds in ingredient_to_meds.items():
        unique_meds = _dedupe_products(meds)
        if len(unique_meds) < 2:
            continue
        display_names = [_display_name(m) for m in unique_meds]
        duplicates.append({
            "active_ingredient": ingredient,
            "severity": "high",
            "medications": [
                {
                    "input_name": m.get("input_name", ""),
                    "generic_name": m.get("generic_name", ""),
                    "dosage_mg": m.get("dosage_mg"),
                }
                for m in unique_meds
            ],
            "message": (
                f"{_join_names(display_names)} all contain {ingredient}. "
                "Taking them together isn't a drug interaction — it's the same "
                "active ingredient from different products, which risks an "
                "accidental overdose. Check with a pharmacist before combining them."
            ),
        })

    duplicates.sort(key=lambda d: d["active_ingredient"])
    return duplicates
