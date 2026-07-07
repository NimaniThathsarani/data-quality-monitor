"""
Alerting logic.

Inspects check results from a run and raises alerts for anything that
fails, with severity based on how far below threshold the score fell.
Alerts are persisted to MongoDB so the frontend can show an alert feed
and history. Email sending is stubbed but ready to enable.
"""
import uuid
from datetime import datetime, timezone

from app import rules_config as cfg
from app.db import alerts_collection


def _severity(score: float, threshold: float) -> str:
    if score < cfg.ALERT_THRESHOLDS["critical"]:
        return "critical"
    if score < cfg.ALERT_THRESHOLDS["warning"]:
        return "warning"
    return "info"


def generate_alerts(run_result: dict) -> list:
    """Creates alert documents for every failed check in a run."""
    alerts = []
    for r in run_result["results"]:
        if r["passed"]:
            continue

        severity = _severity(r["score"], r["threshold"])
        alert = {
            "alert_id": str(uuid.uuid4()),
            "run_id": run_result["run_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": run_result["dataset"],
            "metric": r["metric"],
            "column": r["column"],
            "score": r["score"],
            "threshold": r["threshold"],
            "severity": severity,
            "message": f"{r['metric'].capitalize()} check failed on '{r['column']}': {r['details']}",
            "resolved": False,
        }
        alerts.append(alert)

    if alerts:
        alerts_collection.insert_many(alerts)

    return alerts


def send_email_alert(alert: dict, to_address: str = None):
    """
    Stub for email alerting. Wire up smtplib here with real credentials
    when deploying. Left disabled by default so the project runs without
    needing an SMTP account configured.
    """
    # Example implementation (disabled):
    #
    # import smtplib
    # from email.mime.text import MIMEText
    #
    # msg = MIMEText(alert["message"])
    # msg["Subject"] = f"[{alert['severity'].upper()}] Data Quality Alert"
    # msg["From"] = "alerts@yourproject.com"
    # msg["To"] = to_address
    #
    # with smtplib.SMTP("smtp.gmail.com", 587) as server:
    #     server.starttls()
    #     server.login("your_email@gmail.com", "app_password")
    #     server.send_message(msg)
    pass
