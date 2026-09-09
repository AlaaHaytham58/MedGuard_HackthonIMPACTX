from itertools import combinations

from .models import CheckResponse, Drug, PairResult, Resolution
from .normalization import normalize_name
from .repository import Repository

# Source labels remain intact. Unrecognized labels have no inferred clinical rank.
# Reconcile this vocabulary against the delivered dataset before production import.
SEVERITY_RANK = {"Major": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}


def severity_rank(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip().title()
    return SEVERITY_RANK.get(normalized)


def unique_pairs(drug_ids: list[int]) -> list[tuple[int, int]]:
    return list(combinations(sorted(set(drug_ids)), 2))


class InteractionService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def check_pair(self, first: Drug, second: Drug) -> PairResult | None:
        """Canonical-drug entry point for future in-process pipeline integration."""
        if first.id == second.id:
            return None
        first, second = sorted((first, second), key=lambda drug: drug.id)
        interaction = self.repository.find_pair(first.id, second.id)
        return PairResult(
            drug_a=first, drug_b=second,
            status="interaction_found" if interaction else "no_record_found",
            interaction=interaction,
            severity_rank=severity_rank(interaction.severity) if interaction else None,
        )

    def check_names(self, names: list[str]) -> CheckResponse:
        if not 2 <= len(names) <= 50 or any(
            not isinstance(name, str) or len(name) > 300 or not normalize_name(name) for name in names
        ):
            raise ValueError("Provide 2-50 nonblank drug names, each at most 300 characters")
        resolutions = []
        resolved = {}
        cache = {}
        for name in names:
            key = normalize_name(name)
            if key not in cache:
                cache[key] = self.repository.resolve(name)
            drug = cache[key]
            resolutions.append(Resolution(
                input_name=name, normalized_name=key,
                status="resolved" if drug else "unresolved", drug=drug,
            ))
            if drug:
                resolved[drug.id] = drug

        pairs = unique_pairs(list(resolved))
        records = {}
        for item in self.repository.interactions_for(list(resolved)):
            key = (item.drug_a_id, item.drug_b_id)
            current = records.get(key)
            if current is None or (severity_rank(item.severity) or -1) > (severity_rank(current.severity) or -1):
                records[key] = item
        found, missing = [], []
        for first, second in pairs:
            interaction = records.get((first, second))
            result = PairResult(
                drug_a=resolved[first], drug_b=resolved[second],
                status="interaction_found" if interaction else "no_record_found",
                interaction=interaction,
                severity_rank=severity_rank(interaction.severity) if interaction else None,
            )
            (found if interaction else missing).append(result)
        found.sort(key=lambda item: (-(item.severity_rank or 0), item.drug_a.id, item.drug_b.id))
        status = "complete"
        if any(item.status == "unresolved" for item in resolutions):
            status = "unresolved_drugs"
        elif len(resolved) < 2:
            status = "insufficient_distinct_drugs"
        return CheckResponse(
            status=status, resolutions=resolutions, comparisons=len(pairs),
            interactions=found, no_record_pairs=missing,
        )
