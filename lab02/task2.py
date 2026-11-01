import csv
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def setup_logger(log_file_path: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("UserActivityAudit")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def is_off_hours(dt: datetime) -> bool:
    if dt.weekday() >= 5:
        return True
    return dt.hour >= 22 or dt.hour < 6


def analyze_user_activity(
    csv_file: Path,
    out_report: Path,
    after_hours_only: bool = False,
    log_file: Path | None = None,
    mass_threshold: int = 50,
) -> dict:
    logger = setup_logger(log_file)
    logger.info(f"Reading user activity log {csv_file}...")

    if not csv_file.exists():
        logger.error(f"File {csv_file} does not exist!")
        raise FileNotFoundError(f"Вхідний файл {csv_file} не знайдено.")

    records = []
    with open(csv_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row or not any(row.values()):
                continue

            clean_row = {
                k.strip(): v.strip() for k, v in row.items() if k and v
            }

            ts_val = clean_row.get("Timestamp") or clean_row.get("timestamp")
            user_val = (
                clean_row.get("UserID")
                or clean_row.get("user_id")
                or clean_row.get("User")
            )
            action_val = clean_row.get("Action") or clean_row.get("action")
            res_val = clean_row.get("Resource") or clean_row.get("resource")
            ip_val = clean_row.get("IP") or clean_row.get("ip")

            if ts_val and user_val:
                try:
                    dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                except ValueError:
                    continue

                records.append({
                    "timestamp": dt,
                    "user_id": user_val,
                    "action": action_val or "UNKNOWN",
                    "resource": res_val or "UNKNOWN",
                    "ip": ip_val or "0.0.0.0",
                })

    logger.info(f"Total records processed: {len(records)}.")

    off_hours_alerts = []
    user_requests = defaultdict(list)

    for rec in records:
        dt = rec["timestamp"]
        user = rec["user_id"]
        user_requests[user].append(rec)

        if is_off_hours(dt):
            off_hours_alerts.append({
                "user_id": user,
                "timestamp": dt.isoformat(),
                "resource": rec["resource"],
                "ip": rec["ip"],
                "action": rec["action"],
            })

    print("\n=== Off-Hours Activity Alerts (22:00 - 06:00 / Weekends) ===")
    for alert in off_hours_alerts:
        dt_obj = datetime.fromisoformat(alert["timestamp"])
        if dt_obj.weekday() >= 5:
            day_str = dt_obj.strftime("%A")
            print(
                f"[ALERT] User '{alert['user_id']}' accessed"
                f" '{alert['resource']}' on {day_str}"
                f" {dt_obj.strftime('%H:%M:%S')} from IP {alert['ip']}"
            )
        else:
            print(
                f"[ALERT] User '{alert['user_id']}' performed activity at"
                f" {dt_obj.strftime('%H:%M:%S')} (Resource:"
                f" {alert['resource']})"
            )

    mass_download_alerts = []
    for user, reqs in user_requests.items():
        reqs_sorted = sorted(reqs, key=lambda x: x["timestamp"])
        n = len(reqs_sorted)
        for i in range(n):
            window_count = 0
            for j in range(i, n):
                diff = (
                    reqs_sorted[j]["timestamp"] - reqs_sorted[i]["timestamp"]
                ).total_seconds()
                if diff <= 60:
                    window_count += 1
                else:
                    break
            if window_count > mass_threshold:
                alert = {
                    "user_id": user,
                    "count": window_count,
                    "window_sec": 60,
                    "start_time": reqs_sorted[i]["timestamp"].isoformat(),
                }
                if alert not in mass_download_alerts:
                    mass_download_alerts.append(alert)

    print("\n=== Mass Download Anomalies (>50 requests/min) ===")
    for alert in mass_download_alerts:
        print(
            f"[ALERT] User '{alert['user_id']}' executed {alert['count']}"
            " requests within 60 seconds."
        )

    report_data = {
        "summary": {
            "total_records": len(records),
            "off_hours_alerts_count": len(off_hours_alerts),
            "mass_download_alerts_count": len(mass_download_alerts),
        },
        "off_hours_alerts": off_hours_alerts,
        "mass_download_alerts": mass_download_alerts,
    }

    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    logger.info(f"Anomalous activity report written to {out_report}")
    return report_data
