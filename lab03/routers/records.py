"""Маршрути записів."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Response

from .. import repository
from ..schemas import RecordCreate, RecordRead, RecordReplace, Status

router = APIRouter(prefix="/records", tags=["Записи"])

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис з таким code вже існує"}}

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status: Annotated[
        Status | None, Query(description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(ge=0, allow_inf_nan=False, description="value >= min_value (хвилини)"),
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=120, description="Підрядок у title"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимум записів")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки пропустити")] = 0,
) -> list[dict]:
    """Повернути записи, відсортовані за id."""
    return repository.list_records(category_id, status, min_value, q, limit, offset)


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=201,
    summary="Пакетне створення записів",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    records: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Атомарно створити від 1 до 100 записів."""
    return repository.bulk_create_records([item.model_dump() for item in records])


@router.post(
    "",
    response_model=RecordRead,
    status_code=201,
    summary="Створити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(payload: RecordCreate) -> dict:
    """Створити один запис."""
    return repository.create_record(payload.model_dump())


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за id",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict:
    """Повернути один запис."""
    return repository.get_record(record_id)


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Замінити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict:
    """Повністю замінити змінювані поля запису."""
    return repository.replace_record(record_id, payload.model_dump())


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Видалити запис",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис."""
    repository.delete_record(record_id)
    return Response(status_code=204)
