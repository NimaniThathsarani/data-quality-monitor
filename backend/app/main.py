from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import check_connection, ensure_indexes
from app.routers import checks, alerts, reports
from app.scheduler import start_scheduler, scheduler

app = FastAPI(title="Data Quality Monitoring System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(checks.router)
app.include_router(alerts.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup():
    if not check_connection():
        print("WARNING: could not connect to MongoDB at mongodb://localhost:27017 "
              "- make sure `mongod` is running.")
    else:
        print("Connected to MongoDB.")
        ensure_indexes()
    start_scheduler()
    print("Scheduler started - automated checks will run every 6 hours.")
    print("You can also trigger a check manually: POST /api/checks/run")


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler stopped.")


@app.get("/")
def root():
    return {
        "service": "Data Quality Monitoring System",
        "status": "running",
        "endpoints": {
            "run_check": "POST /api/checks/run",
            "list_runs": "GET /api/checks/runs",
            "run_detail": "GET /api/checks/runs/{run_id}",
            "trend": "GET /api/checks/trend",
            "alerts": "GET /api/alerts",
            "alerts_summary": "GET /api/alerts/summary",
            "resolve_alert": "PATCH /api/alerts/{alert_id}/resolve",
            "health_summary": "GET /api/reports/health-summary",
            "failing_checks": "GET /api/reports/failing-checks",
        },
    }
