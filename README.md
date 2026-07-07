# Data Quality Monitoring System

Automated data quality monitoring for the **World Layoffs** dataset — completeness,
uniqueness, validity, consistency, and timeliness checks, with automated alerting,
historical trend tracking, and a live dashboard.

## Stack
- **Backend**: FastAPI + Pandas (quality engine) + MongoDB + APScheduler
- **Frontend**: React (Vite) + Recharts

## Project structure
```
data-quality-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint
│   │   ├── db.py               # MongoDB connection
│   │   ├── quality_engine.py   # Pandas quality checks (5 dimensions)
│   │   ├── rules_config.py     # Quality standards/thresholds (edit this to retune rules)
│   │   ├── alerts.py           # Alert generation logic
│   │   ├── scheduler.py        # APScheduler automated runs
│   │   └── routers/            # checks / alerts / reports endpoints
│   ├── data/layoffs.csv        # The dataset being monitored
│   └── requirements.txt
└── frontend/
    └── src/                     # React dashboard
```

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Make sure MongoDB is running locally (default `mongodb://localhost:27017` —
edit `app/db.py` if yours is different).

Start the API:
```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Connected to MongoDB.
Scheduler started - automated checks will run every 6 hours.
```

Visit http://localhost:8000/docs for interactive API docs.

Trigger your first check run:
```bash
curl -X POST http://localhost:8000/api/checks/run
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — the dashboard talks to the backend at
`http://localhost:8000` (see `src/api.js` if you need to change that).

## How it works

1. **Quality engine** (`quality_engine.py`) runs 5 categories of checks defined
   in `rules_config.py`:
   - **Completeness** — % non-null per column
   - **Uniqueness** — exact duplicate rows + near-duplicate detection (same
     company/date/location reported more than once)
   - **Validity** — numeric ranges, valid dates
   - **Consistency** — cross-record logic (e.g. 'UAE' vs 'United Arab Emirates'
     used inconsistently)
   - **Timeliness** — how recently the dataset was refreshed
2. Each run is stored in MongoDB (`dq_runs`, `dq_results` collections) so you
   get historical trend data, not just a snapshot.
3. Any check that fails its threshold raises an **alert** (`dq_alerts`
   collection) with a severity (critical/warning/info based on how far below
   threshold it fell).
4. The scheduler re-runs all checks automatically every 6 hours
   (`CHECK_INTERVAL_HOURS` in `scheduler.py`) — you can also trigger a run
   manually from the dashboard's "Run checks now" button.
5. The dashboard shows the overall health score, a per-dimension breakdown
   with trend sparklines, the active alert feed, and a table of currently
   failing checks.

## Updating the rules
All quality standards live in `backend/app/rules_config.py` — thresholds,
which columns matter, and what counts as valid. Change the numbers there;
no other code needs to change. This file is also your documentation of what
"data quality" means for this dataset, useful to reference in the governance
framework write-up.

## Notes
- The dataset is a downloaded snapshot (`layoffs.csv`), not a live feed, so
  "timeliness" measures how recently the dataset file itself was refreshed
  rather than per-row recency (this is a historical archive back to 2020;
  individual old rows are expected, not an error).
- Email alerting is stubbed out in `alerts.py` (disabled by default) — wire
  up real SMTP credentials there if you want actual email notifications.
