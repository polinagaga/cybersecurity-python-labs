import csv
import datetime
import functools
import hashlib
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import VARIANT_NUMBER


class ValidationError(Exception):
  pass
HASH_ALGORITHM = "sha384"
MIN_PASSWORD_LENGTH = 15
SALT = str(VARIANT_NUMBER).zfill(5)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_FILE = os.path.join(DATA_DIR, "users.csv")
LOG_FILE = os.path.join(DATA_DIR, "log.json")

users_to_register = (
    ("admin_sec", "SuperSecretPass2026!Key1"),
    ("analyst_1", "ComplexPassword#99999"),
    ("operator_x", "ShortPass123!"),  # Викличе ValidationError (довжина < 15)
    ("user_test", "AnotherVeryLongPassword777"),
    ("audit_lead", "SecureAuditAccess2026"),
    ("guest_user", "GuestAccountPass_12345"),
    ("dev_engineer", "DeveloperAccessCode_888"),
    ("manager_sec", "ManagementLevelPass_000"),
    ("sys_monitor", "SystemMonitoringPass_555"),
    ("soc_analyst", "SOCAnalystSecurePass_111"),
)


def log_event(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        username = kwargs.get("username") or (args[0] if args else "unknown")
        result = "failure"
        try:
            res = func(*args, **kwargs)
            result = "success" if res else "failure"
            return res
        finally:
            os.makedirs(DATA_DIR, exist_ok=True)
            log_entry = {
                "event": "login",
                "user": username,
                "result": result,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "args": list(args),
                "kwargs": kwargs,
            }

            logs = []
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except (OSError, json.JSONDecodeError):
                    logs = []

            logs.append(log_entry)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

    return wrapper


def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми!")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль коротший за мінімальну довжину ({MIN_PASSWORD_LENGTH} символів.)"
        )

    salted_password = (password + salt).encode("utf-8")
    return hashlib.sha384(salted_password).hexdigest()


def create_user(username: str, password: str) -> tuple:
    hash_val = generate_hash(password, SALT)
    return (username, hash_val)


def create_users(users_list: tuple) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    valid_users = []

    for user, pwd in users_list:
        try:
            user_data = create_user(user, pwd)
            valid_users.append(user_data)
        except (ValueError, ValidationError) as e:
            print(f"Помилка реєстрації користувача {user}: {e}")

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password_hash"])
        writer.writerows(valid_users)


def read_users_db() -> list:
    users_db = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Пропускаємо заголовок
        for row in reader:
            if row:
                users_db.append(row)
    return users_db


@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Логін або пароль порожні!")

    users_db = read_users_db()
    for db_user, db_hash in users_db:
        if db_user == username:
            try:
                input_hash = generate_hash(password, SALT)
                return input_hash == db_hash
            except (ValueError, ValidationError):
                return False
    return False


def run_task3() -> None:
    print("Реєстрація користувачів та збереження в CSV")
    try:
        create_users(users_to_register)

        print("\nВміст бази даних користувачів (users.csv)")
        db = read_users_db()
        print(f"{'Username':<20} | {'Password Hash (sha384)':<40}")
        for u, h in db:
            print(f"{u:<20} | {h[:37]}...")

        print("\nСпроби входу (Автентифікація)і")
        # Успішний вхід
        res1 = login(username="admin_sec", password="SuperSecretPass2026!Key1")
        print(f"Вхід admin_sec: {'Успіх' if res1 else 'Невдача'}")

        # Неуспішний вхід (неправильний пароль)
        res2 = login(username="admin_sec", password="WrongPassword123456")
        print(f"Вхід admin_sec (невірний пароль): {'Успіх' if res2 else 'Невдача'}")

    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка роботи з файлами: {e}")
    except (ValueError, ValidationError) as e:
        print(f"Помилка валідації: {e}")


if __name__ == "__main__":
    run_task3()
