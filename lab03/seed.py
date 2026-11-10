"""Початкове заповнення бази з data/seed.json."""

import json
import sqlite3
import sys
from contextlib import closing

from pydantic import ValidationError

from .database import BASE_DIR, get_connection, initialize_database
from .schemas import CategoryCreate, RecordCreate

SEED_PATH = BASE_DIR / "data" / "seed.json"


def load_seed() -> tuple[list[dict], list[dict]]:
    """Прочитати й перевірити початкові дані."""
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    raw_categories = data["categories"]
    raw_records = data["records"]

    categories = []
    for item in raw_categories:
        category_id = item["id"]
        if not isinstance(category_id, int) or category_id <= 0:
            raise ValueError(f"Некоректний id категорії: {category_id!r}")
        validated = CategoryCreate.model_validate({"name": item["name"]})
        categories.append({"id": category_id, "name": validated.name})

    known_ids = {category["id"] for category in categories}
    records = []
    for item in raw_records:
        validated = RecordCreate.model_validate(item)
        if validated.category_id not in known_ids:
            raise ValueError(f"Невідома категорія: {validated.category_id}")
        records.append(validated.model_dump())
    return categories, records


def seed_database() -> bool:
    """Заповнити порожню базу; повернути True, якщо дані додано."""
    categories, records = load_seed()
    # одна транзакція: або все, або нічого
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        categories_count = connection.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]
        records_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if categories_count or records_count:
            return False
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            [(c["id"], c["name"]) for c in categories],
        )
        connection.executemany(
            "INSERT INTO records (code, title, category_id, value, status) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (r["code"], r["title"], r["category_id"], r["value"], r["status"])
                for r in records
            ],
        )
    return True


def main() -> int:
    """Точка входу: ініціалізувати базу й заповнити її."""
    try:
        initialize_database()
        if seed_database():
            print("Базу заповнено: 3 категорії, 8 записів.")
        else:
            print("База вже містить дані - нічого не змінено.")
    except (OSError, KeyError, ValueError, ValidationError, json.JSONDecodeError) as e:
        print(f"Початкові дані некоректні, зміни скасовано: {e}")
        return 1
    except sqlite3.Error as e:
        print(f"Помилка бази даних, зміни скасовано: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
