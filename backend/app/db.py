"""
MongoDB connection layer.

Assumes a local MongoDB instance running on the default port.
Collections:
  - dq_runs     : one document per full check run (summary)
  - dq_results  : one document per individual check within a run
  - dq_alerts   : alerts raised when checks fail thresholds
"""
from pymongo import MongoClient, DESCENDING

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "data_quality_monitor"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client[DB_NAME]

runs_collection = db["dq_runs"]
results_collection = db["dq_results"]
alerts_collection = db["dq_alerts"]

def check_connection() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False


def ensure_indexes():
    """Creates indexes for fast querying. Called on app startup rather than
    at import time, so the app can still boot (and report the connection
    error clearly) even if MongoDB isn't reachable yet."""
    try:
        runs_collection.create_index([("timestamp", DESCENDING)])
        results_collection.create_index([("run_id", 1)])
        alerts_collection.create_index([("timestamp", DESCENDING)])
    except Exception as e:
        print(f"WARNING: could not create MongoDB indexes: {e}")
