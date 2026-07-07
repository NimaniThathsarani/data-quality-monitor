import pandas as pd
from fastapi import APIRouter, HTTPException

from app import quality_engine as qe
from app import alerts as alert_module
from app import rules_config as cfg
from app.db import runs_collection, results_collection

router = APIRouter(prefix="/api/checks", tags=["checks"])


@router.post("/run")
def run_checks_now():
    """Manually trigger a full data quality check run."""
    try:
        df = pd.read_csv(cfg.DATA_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset not found at {cfg.DATA_PATH}")

    run_result = qe.run_all_checks(df)

    runs_collection.insert_one({k: v for k, v in run_result.items() if k != "results"})
    results_collection.insert_many(run_result["results"])
    new_alerts = alert_module.generate_alerts(run_result)

    return {
        "run_id": run_result["run_id"],
        "health_score": run_result["health_score"],
        "checks_run": run_result["checks_run"],
        "checks_failed": run_result["checks_failed"],
        "alerts_generated": len(new_alerts),
        "results": run_result["results"],
    }


@router.get("/runs")
def list_runs(limit: int = 20):
    """Returns recent check run summaries, most recent first."""
    runs = list(runs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return {"runs": runs}


@router.get("/runs/{run_id}")
def get_run_detail(run_id: str):
    """Returns full detail (all individual check results) for one run."""
    run = runs_collection.find_one({"run_id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    results = list(results_collection.find({"run_id": run_id}, {"_id": 0}))
    run["results"] = results
    return run


@router.get("/trend")
def get_trend(metric: str = None, limit: int = 50):
    """Returns historical scores for trend charts, optionally filtered by metric."""
    query = {"metric": metric} if metric else {}
    results = list(
        results_collection.find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return {"results": list(reversed(results))}
