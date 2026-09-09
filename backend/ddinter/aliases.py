"""Seed INN/Egyptian-market drug names as aliases of DDInter's US canonical names.

DDInter stores US adopted names ("Acetaminophen"); `/normalize` resolves Egyptian
packaging to INN/British names ("paracetamol"). Without this bridge a pair silently
resolves to nothing and the user is told "no record found" for a drug the catalog
actually holds — the exact silent failure the integration guide warns about.

Only aliases whose target is already in the catalog are applied, so this stays
correct as the DDInter scrape grows rather than inserting dangling names.
"""

import sys

from .repository import Repository, connect, database_path

# alias (what /normalize emits) -> canonical name as DDInter stores it
SYNONYMS = {
    "paracetamol": "Acetaminophen",
    "acetylsalicylic acid": "Aspirin",
    "salbutamol": "Albuterol",
    "adrenaline": "Epinephrine",
    "noradrenaline": "Norepinephrine",
    "lignocaine": "Lidocaine",
    "frusemide": "Furosemide",
    "glibenclamide": "Glyburide",
    "rifampicin": "Rifampin",
    "ciclosporin": "Cyclosporine",
    "oestradiol": "Estradiol",
    "amoxycillin": "Amoxicillin",
    "pethidine": "Meperidine",
    "dothiepin": "Dosulepin",
    "indometacin": "Indomethacin",
    "thyroxine": "Levothyroxine",
    "vitamin k": "Phytonadione",
}


def seed_aliases(repository: Repository) -> dict:
    applied, skipped_missing_target, already_present = [], [], []

    for alias, canonical in SYNONYMS.items():
        target = repository.resolve(canonical)
        if target is None:
            skipped_missing_target.append(alias)
            continue
        if repository.resolve(alias) is not None:
            already_present.append(alias)
            continue
        repository.add_alias(alias, target.id)
        applied.append(f"{alias} -> {target.canonical_name}")

    return {
        "applied": applied,
        "already_present": already_present,
        "skipped_missing_target": skipped_missing_target,
    }


def main() -> int:
    connection = connect(database_path())
    try:
        report = seed_aliases(Repository(connection))
        connection.commit()
    finally:
        connection.close()

    for line in report["applied"]:
        print("added:", line)
    print(
        f"{len(report['applied'])} added, "
        f"{len(report['already_present'])} already present, "
        f"{len(report['skipped_missing_target'])} skipped (not in catalog yet)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
