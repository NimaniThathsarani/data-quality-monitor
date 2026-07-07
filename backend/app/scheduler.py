"""
Scheduled automated quality checks using APScheduler.
Runs the full check suite every N hours without manual triggering.
"""
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from app import quality_engine as qe
from app import alerts as alert_module
from app import rules_config as cfg
from app.db import runs_collection, results_collection

CHECK_INTERVAL_HOURS = 6  # adjust as needed


def run_scheduled_check():
    df = pd.read_csv(cfg.DATA_PATH)
    run_result = qe.run_all_checks(df)

    # Store run summary and individual results
    runs_collection.insert_one({k: v for k, v in run_result.items() if k != "results"})
    results_collection.insert_many(run_result["results"])

    # Generate alerts for any failures
    alert_module.generate_alerts(run_result)

    print(f"[scheduler] Run {run_result['run_id']} complete. "
          f"Health score: {run_result['health_score']}, "
          f"Failed checks: {run_result['checks_failed']}")


scheduler = BackgroundScheduler()
scheduler.add_job(run_scheduled_check, "interval", hours=CHECK_INTERVAL_HOURS, id="dq_check_job")


def start_scheduler():
    scheduler.start()
