
import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import STUDENT_NAME, VARIANT_NUMBER

passwords = [
    "NetworkS3c!",
    "easy",
    "Firewa11@Pass",
    "anonymous",
    "Intrus10n#Detect",
    "sample",
    "Malwar3@Scan",
    "qwerty",
    "Vulnerability",
    "common",
]

criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "easy",
    "anonymous",
    "sample",
    "qwerty",
    "common",
    "password",
}


def analyze_passwords() -> None:
    print(f"Завдання 1  Студент: {STUDENT_NAME}  Варіант: {VARIANT_NUMBER} ")

    working_passwords = list(passwords)

    random.seed(42)
    random_indices = [random.randint(0, len(working_passwords) - 1) for _ in range(3)]
    for idx in random_indices:
        working_passwords.append(working_passwords[idx])

    min_len = criteria["min_length"]

    print(f"{'№':<3} | {'Пароль':<20} | {'Статус':<15}")

    for i, pwd in enumerate(working_passwords, 1):
        has_digit = any(c.isdigit() for c in pwd)
        has_upper = any(c.isupper() for c in pwd)
        has_lower = any(c.islower() for c in pwd)
        has_special = any(not c.isalnum() for c in pwd)

        all_criteria_met = (
            len(pwd) >= min_len and has_digit and has_upper and has_special
        )
        is_unique = working_passwords.count(pwd) == 1

        if pwd in forbidden_passwords or len(pwd) < min_len:
            status = "Заборонений"
        elif all_criteria_met and len(pwd) >= min_len + 4 and is_unique:
            status = "Дуже сильний"
        elif all_criteria_met:
            status = "Сильний"
        elif has_digit or has_upper or has_lower or has_special:
            if len(pwd) >= min_len and (has_digit or has_upper or has_special):
                status = "Середній"
            else:
                status = "Слабкий"
        else:
            status = "Заборонений"

        print(f"{i:<3} | {pwd:<20} | {status:<15}")


if __name__ == "__main__":
    analyze_passwords()
