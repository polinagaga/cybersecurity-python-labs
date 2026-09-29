
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import STUDENT_NAME, VARIANT_NUMBER

users = {
    "incident_commander": {
        "role": "incident_response",
        "clearance": 4,
        "department": "CSIRT",
        "active": True,
    },
    "malware_analyst": {
        "role": "malware_researcher",
        "clearance": 3,
        "department": "Research",
        "active": True,
    },
    "monitoring_tech": {
        "role": "monitoring",
        "clearance": 2,
        "department": "NOC",
        "active": True,
    },
    "customer_rep": {
        "role": "customer_service",
        "clearance": 1,
        "department": "Customer",
        "active": True,
    },
    "backup_service": {
        "role": "service_account",
        "clearance": 2,
        "department": "System",
        "active": False,
    },
}

resources = [
    ("incident_playbook", 4),
    ("malware_lab", 3),
    ("monitoring_dashboards", 2),
    ("customer_portal", 1),
    ("emergency_procedures", 4),
    ("service_desk", 1),
    ("reverse_engineering", 3),
    ("alert_systems", 2),
    ("escalation_matrix", 3),
    ("knowledge_base", 1),
]

security_levels = ("Public Access", "Authorized", "Privileged", "Critical")
blocked_users = {"backup_service", "deactivated_svc", "policy_violation"}


def check_access() -> None:
    print(f"Завдання 2 Студент: {STUDENT_NAME} Варіант: {VARIANT_NUMBER} \n")

    print("Перелік ресурсів системи")
    for res_name, level in resources:
        level_str = security_levels[level - 1]
        print(f"Ресурс: {res_name:<25} | Рівень безпеки: {level_str}")

    print("\nРезультати перевірки доступуі")
    all_test_users = list(users.keys()) + ["unknown_user"]

    for user_id in all_test_users:
        for res_name, req_clearance in resources:
            if user_id not in users:
                status = "DENY (User not found)"
            elif user_id in blocked_users:
                status = "DENY (User is blocked)"
            elif not users[user_id]["active"]:
                status = "DENY (Account inactive)"
            elif users[user_id]["clearance"] >= req_clearance:
                status = "ALLOW"
            else:
                status = "DENY (Insufficient clearance)"

            print(f"user=[{user_id}] resource=[{res_name}] -> {status}")


if __name__ == "__main__":
    check_access()
