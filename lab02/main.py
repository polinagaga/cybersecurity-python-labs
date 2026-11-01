import argparse
from pathlib import Path

from lab02.task1 import Admin, User, UserAccount
from lab02.task2 import analyze_user_activity


def run_demo():
    print("=== Демонстрація Завдання 1 (ООП Модель Безпеки) ===")

    print("\n1. Створення користувача та встановлення пароля:")
    user = User(username="j_smith", email="john.smith@example.com")
    user.set_password("SecurePassword123!")
    print(f"Створено: {user}")

    print("\n2. Тестування валідації email:")
    try:
        user.email = "bad_email_format"
    except ValueError as e:
        print(f"Очікувана помилка валідації: {e}")

    print("\n3. Спроби входу в систему:")
    account = UserAccount(user=user)
    success = account.login("j_smith", "SecurePassword123!", "192.168.1.50")
    print(f"Вхід з правильним паролем: {'УСПІШНИЙ' if success else 'НЕВДАЛИЙ'}")
    print(f"Статус аутентифікації: {account.is_authenticated()}")

    failed = account.login("j_smith", "WrongPassword", "192.168.1.50")
    print(f"Вхід з неправильним паролем: {'УСПІШНИЙ' if failed else 'НЕВДАЛИЙ'}")

    print("\n4. Перевірка класу Admin (Наслідування):")
    admin = Admin(
        username="alex_admin",
        email="alex@admin.corp.ua",
        permissions=["read", "write"],
    )
    admin.grant_permission("delete")
    print(admin)
    print(f"Має право 'delete': {admin.has_permission('delete')}")

    print("\n5. Вихід із системи та виведення AuditLog:")
    account.logout()
    account["audit_log"].show_all()


def main():
    parser = argparse.ArgumentParser(description="Лабораторна робота №2 (Варіант 7)")
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    subparsers.add_parser("demo", help="Запустити демонстрацію Завдання 1")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Запустити аналізатор активності (Завдання 2)"
    )
    analyze_parser.add_argument(
        "--activity-log",
        type=Path,
        default=Path("lab02/data/activity.csv"),
        help="Шлях до CSV файлу логів",
    )
    analyze_parser.add_argument(
        "--after-hours",
        action="store_true",
        help="Фільтрувати та показувати лише позаробочу активність",
    )
    analyze_parser.add_argument(
        "--out-report",
        type=Path,
        default=Path("lab02/data/off_hours_audit.json"),
        help="Шлях для збереження JSON-звіту",
    )
    analyze_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Шлях до лог-файлу утиліти",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        analyze_user_activity(
            csv_file=args.activity_log,
            out_report=args.out_report,
            after_hours_only=args.after_hours,
            log_file=args.log_file,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
