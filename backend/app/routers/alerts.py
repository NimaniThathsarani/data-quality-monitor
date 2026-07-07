from fastapi import APIRouter, HTTPException

from app.db import alerts_collection

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(resolved: bool = None, limit: int = 50):
    """Returns alerts, optionally filtered by resolved status."""
    query = {} if resolved is None else {"resolved": resolved}
    alerts = list(
        alerts_collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    )
    return {"alerts": alerts}


@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    """Marks an alert as resolved."""
    result = alerts_collection.update_one(
        {"alert_id": alert_id}, {"$set": {"resolved": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert_id": alert_id, "resolved": True}


@router.get("/summary")
def alerts_summary():
    """Counts of active alerts by severity, for dashboard cards."""
    pipeline = [
        {"$match": {"resolved": False}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    counts = {doc["_id"]: doc["count"] for doc in alerts_collection.aggregate(pipeline)}
    return {
        "critical": counts.get("critical", 0),
        "warning": counts.get("warning", 0),
        "info": counts.get("info", 0),
    }
