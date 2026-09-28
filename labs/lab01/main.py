"""Головний модуль запуску Лабораторної роботи №1."""

from labs.lab01.task1 import analyze_passwords
from labs.lab01.task2 import check_access
from labs.lab01.task3 import run_task3


def main() -> None:
    """Запускає всі три завдання послідовно."""
    print("=" * 60)
    print("  ЛАБОРАТОРНА РОБОТА №1 | ОСНОВИ PYTHON, GIT ТА PEP-8")
    print("=" * 60 + "\n")

    analyze_passwords()
    print("\n" + "=" * 60 + "\n")

    check_access()
    print("\n" + "=" * 60 + "\n")

    run_task3()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
