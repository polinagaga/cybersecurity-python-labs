"""Параметризовані SQL-запити до таблиць categories і records."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from typing import Any

from .database import get_connection


class NotFoundError(Exception):
    """Запис або категорію не знайдено."""


class ConflictError(Exception):
    """Дублікат унікального значення або категорія не порожня."""


RECORD_SELECT = """
SELECT r.id, r.code, r.title, r.category_id,
       c.name AS category_name, r.value, r.status
FROM records AS r
JOIN categories AS c ON c.id = r.category_id
"""

INSERT_RECORD = (
    "INSERT INTO records (code, title, category_id, value, status) "
    "VALUES (?, ?, ?, ?, ?)"
)


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Відкрити з'єднання на одну операцію й гарантовано закрити."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def _is_unique_violation(error: sqlite3.IntegrityError) -> bool:
    return "UNIQUE constraint failed" in str(error)


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict | None:
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


def _record_params(data: dict[str, Any]) -> tuple:
    return (
        data["code"],
        data["title"],
        data["category_id"],
        data["value"],
        data["status"],
    )


# ---------- Категорії ----------


def create_category(name: str) -> dict:
    """Створити категорію."""
    with _connect() as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
                category_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Категорія з такою назвою вже існує") from error
            raise
    return {"id": category_id, "name": name}


def list_categories() -> list[dict]:
    """Список категорій за зростанням id."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with _connect() as connection:
        try:
            with connection:
                if not _category_exists(connection, category_id):
                    raise NotFoundError("Категорію не знайдено")
                count = connection.execute(
                    "SELECT COUNT(*) FROM records WHERE category_id = ?",
                    (category_id,),
                ).fetchone()[0]
                if count > 0:
                    raise ConflictError("Категорія містить записи")
                connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Категорія містить записи") from error


# ---------- Записи ----------


def create_record(data: dict[str, Any]) -> dict:
    """Додати один запис."""
    with _connect() as connection:
        try:
            with connection:
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                cursor = connection.execute(INSERT_RECORD, _record_params(data))
                record = _fetch_record(connection, cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Запис з таким code вже існує") from error
            raise
    return record


def get_record(record_id: int) -> dict:
    """Отримати запис за id (з category_name через JOIN)."""
    with _connect() as connection:
        record = _fetch_record(connection, record_id)
    if record is None:
        raise NotFoundError("Запис не знайдено")
    return record


def list_records(
    category_id: int | None,
    status: str | None,
    min_value: float | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """Список записів із фільтрами (через AND) та пагінацією."""
    conditions: list[str] = []
    params: list[Any] = []

    # SQL-фрагменти - лише фіксовані рядки з коду, значення - у params.
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    query = RECORD_SELECT
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with _connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def replace_record(record_id: int, data: dict[str, Any]) -> dict:
    """Повністю замінити змінювані поля запису (id незмінний)."""
    with _connect() as connection:
        try:
            with connection:
                if _fetch_record(connection, record_id) is None:
                    raise NotFoundError("Запис не знайдено")
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (*_record_params(data), record_id),
                )
                record = _fetch_record(connection, record_id)
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Запис з таким code вже існує") from error
            raise
    return record


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with _connect() as connection, connection:
        if _fetch_record(connection, record_id) is None:
            raise NotFoundError("Запис не знайдено")
        connection.execute("DELETE FROM records WHERE id = ?", (record_id,))


def bulk_create_records(items: list[dict[str, Any]]) -> list[dict]:
    """Атомарно додати пакет записів в одній транзакції."""
    codes = [item["code"] for item in items]
    if len(codes) != len(set(codes)):
        raise ConflictError("Пакет містить повторювані code")

    with _connect() as connection:
        try:
            with connection:  # один commit у кінці або rollback при помилці
                connection.execute("BEGIN IMMEDIATE")
                for category_id in {item["category_id"] for item in items}:
                    if not _category_exists(connection, category_id):
                        raise NotFoundError("Категорію не знайдено")
                ids = []
                for item in items:
                    cursor = connection.execute(INSERT_RECORD, _record_params(item))
                    ids.append(cursor.lastrowid)
                created = [_fetch_record(connection, record_id) for record_id in ids]
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Запис з таким code вже існує") from error
            raise
    return created
