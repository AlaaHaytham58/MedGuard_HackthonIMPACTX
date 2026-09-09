from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .normalization import normalize_name

DrugName = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=300)]


class Drug(BaseModel):
    id: int
    canonical_name: str
    ddinter_id: str | None = None
    drugbank_id: str | None = None


class DrugAlias(BaseModel):
    id: int
    alias: str
    drug_id: int


class InteractionReference(BaseModel):
    pair_id: int
    reference_number: int
    reference_text: str
    source_url: str


class DrugInteraction(BaseModel):
    id: int
    drug_a_id: int
    drug_b_id: int
    severity: str
    interaction_type: str | None = None
    description: str | None = None
    mechanism: str | None = None
    management: str | None = None
    source_reference: str | None = None
    pair_id: int | None = None
    definition_id: str | None = None
    pair_key: str | None = None
    detail_url: str | None = None
    interaction_text: str | None = None
    detail_available: bool = False
    references: list[InteractionReference] = Field(default_factory=list)


class AlternativeDrug(BaseModel):
    id: int
    original_drug_id: int
    alternative_drug_id: int | None = None
    information: str | None = None
    context: str | None = None
    pair_id: int | None = None
    side: Literal["A", "B"] | None = None
    atc_code: str | None = None


class MultipleCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drugs: list[DrugName] = Field(min_length=2, max_length=50)

    @field_validator("drugs")
    @classmethod
    def nonblank_names(cls, values: list[str]) -> list[str]:
        if any(not normalize_name(value) for value in values):
            raise ValueError("Drug names must contain non-whitespace characters")
        return values


class Resolution(BaseModel):
    input_name: str
    normalized_name: str
    status: Literal["resolved", "unresolved"]
    drug: Drug | None = None


class PairResult(BaseModel):
    drug_a: Drug
    drug_b: Drug
    status: Literal["interaction_found", "no_record_found"]
    interaction: DrugInteraction | None = None
    severity_rank: int | None = None


class CheckResponse(BaseModel):
    status: Literal["complete", "unresolved_drugs", "insufficient_distinct_drugs"]
    resolutions: list[Resolution]
    comparisons: int
    interactions: list[PairResult]
    no_record_pairs: list[PairResult]
    notice: str = "No record found does not establish that a drug combination is medically safe."


class AlternativesResponse(BaseModel):
    drug: Drug
    alternatives: list[AlternativeDrug]
    notice: str = "Catalog alternatives are source information, not personalized substitution recommendations."
