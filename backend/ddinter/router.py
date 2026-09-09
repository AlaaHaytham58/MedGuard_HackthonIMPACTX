import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from .models import AlternativesResponse, CheckResponse, Drug, DrugInteraction, MultipleCheckRequest
from .normalization import normalize_name
from .repository import Repository, connect, database_path
from .service import InteractionService

router = APIRouter(tags=["drug interactions"])


def api_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={
        "error": True, "code": code, "message": message, "details": {},
    })


def get_repository() -> Iterator[Repository]:
    connection = None
    try:
        connection = connect(database_path(), readonly=True)
        yield Repository(connection)
    except sqlite3.Error as exc:
        raise api_error(503, "CATALOG_UNAVAILABLE", "The drug interaction catalog is unavailable") from exc
    finally:
        if connection is not None:
            connection.close()


Catalog = Annotated[Repository, Depends(get_repository)]
NameQuery = Annotated[str, Query(min_length=1, max_length=300)]
PositiveId = Annotated[int, Path(gt=0)]


def validate_names(*names: str) -> None:
    if any(not normalize_name(name) for name in names):
        raise api_error(422, "INVALID_DRUG_NAME", "Drug names must contain non-whitespace characters")


@router.get("/drugs/search", response_model=list[Drug])
def search(q: NameQuery, repository: Catalog, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    validate_names(q)
    return repository.search(q, limit)


@router.get("/interactions/check", response_model=CheckResponse)
def check_pair(drug_a: NameQuery, drug_b: NameQuery, repository: Catalog):
    validate_names(drug_a, drug_b)
    return InteractionService(repository).check_names([drug_a, drug_b])


@router.post("/interactions/check-multiple", response_model=CheckResponse)
def check_multiple(request: MultipleCheckRequest, repository: Catalog):
    return InteractionService(repository).check_names(request.drugs)


@router.get("/interactions/{interaction_id}", response_model=DrugInteraction)
def interaction_details(interaction_id: PositiveId, repository: Catalog):
    interaction = repository.get_interaction(interaction_id)
    if interaction is None:
        raise api_error(404, "INTERACTION_NOT_FOUND", "Interaction record not found")
    return interaction


@router.get("/drugs/{drug_id}/alternatives", response_model=AlternativesResponse)
def drug_alternatives(
    drug_id: PositiveId,
    repository: Catalog,
    pair_id: Annotated[int, Query(gt=0)],
):
    drug = repository.get_drug(drug_id)
    if drug is None:
        raise api_error(404, "DRUG_NOT_FOUND", "Drug record not found")
    return AlternativesResponse(drug=drug, alternatives=repository.alternatives(drug_id, pair_id))
