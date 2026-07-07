from fastapi import APIRouter, HTTPException

from app.db import runs_collection, results_collection, alerts_collection
from app import rules_config as cfg

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/health-summary")
def health_summary():
    """
    Top-level dashboard summary: latest health score, per-metric breakdown,
    active alert counts. This powers the main dashboard cards.
    """
    latest_run = runs_collection.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
    if not latest_run:
        raise HTTPException(status_code=404, detail="No check runs found yet. POST /api/checks/run first.")

    latest_results = list(results_collection.find({"run_id": latest_run["run_id"]}, {"_id": 0}))

    by_metric = {}
    for r in latest_results:
        by_metric.setdefault(r["metric"], []).append(r["score"])
    metric_averages = {m: round(sum(s) / len(s), 4) for m, s in by_metric.items()}

    active_alerts = alerts_collection.count_documents({"resolved": False})

    return {
        "dataset": latest_run["dataset"],
        "last_run": latest_run["timestamp"],
        "health_score": latest_run["health_score"],
        "row_count": latest_run["row_count"],
        "checks_run": latest_run["checks_run"],
        "checks_failed": latest_run["checks_failed"],
        "active_alerts": active_alerts,
        "metric_breakdown": metric_averages,
        "weights": cfg.HEALTH_SCORE_WEIGHTS,
    }


@router.get("/failing-checks")
def failing_checks():
    """Returns just the currently-failing checks from the latest run."""
    latest_run = runs_collection.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
    if not latest_run:
        raise HTTPException(status_code=404, detail="No check runs found yet.")

    failing = list(results_collection.find(
        {"run_id": latest_run["run_id"], "passed": False}, {"_id": 0}
    ))
    return {"run_id": latest_run["run_id"], "failing_checks": failing}
