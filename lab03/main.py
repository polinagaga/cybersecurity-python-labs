"""FastAPI-застосунок: облік часу реагування на інциденти."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Якщо у вашому shared/student.py змінні названі інакше - змініть імена тут.
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

from .config import APP_DESCRIPTION, APP_TITLE
from .database import initialize_database
from .repository import ConflictError, NotFoundError
from .routers import categories, records
from .schemas import StudentRead

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску (дані не чіпаємо)."""
    initialize_database()
    yield


app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, lifespan=lifespan)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, error: NotFoundError) -> JSONResponse:
    """404 для неіснуючого запису чи категорії."""
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ConflictError)
async def conflict_handler(_: Request, error: ConflictError) -> JSONResponse:
    """409 для дублікатів і непорожньої категорії."""
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(_: Request, error: sqlite3.Error) -> JSONResponse:
    """500 без технічних деталей для клієнта; деталі - у лог."""
    logger.exception("Помилка бази даних: %s", error)
    return JSONResponse(
        status_code=500, content={"detail": "Внутрішня помилка сервера"}
    )


@app.get("/ping", tags=["Службові"], summary="Перевірка доступності")
def ping() -> dict[str, str]:
    """Повернути статус сервісу."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["Службові"],
    summary="Дані студента",
)
def student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
