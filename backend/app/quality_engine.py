"""
Data Quality Check Engine - World Layoffs dataset.

Runs completeness, uniqueness, validity, consistency, and timeliness
checks against a DataFrame, using rules from rules_config.py.
Returns a list of structured result dicts ready to insert into MongoDB.
"""
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app import rules_config as cfg


def _new_run_id():
    return str(uuid.uuid4())


def _to_native(value):
    """Converts numpy scalar types to native Python types so results are
    JSON/BSON-serializable (MongoDB rejects numpy.bool_/numpy.float64 etc.)."""
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _sanitize_result(result: dict) -> dict:
    return {k: _to_native(v) for k, v in result.items()}


def check_completeness(df: pd.DataFrame) -> list:
    results = []
    total = len(df)
    for col, min_ratio in cfg.COMPLETENESS_RULES.items():
        if col not in df.columns:
            continue
        non_null = df[col].notna() & (df[col].astype(str).str.strip() != "")
        ratio = non_null.sum() / total if total else 0
        results.append({
            "metric": "completeness",
            "column": col,
            "score": round(ratio, 4),
            "threshold": min_ratio,
            "passed": ratio >= min_ratio,
            "details": f"{non_null.sum()}/{total} non-null values ({ratio:.1%})",
        })
    return results


def check_uniqueness(df: pd.DataFrame) -> list:
    results = []
    total = len(df)

    # exact full-row duplicates
    dup_count = df.duplicated().sum()
    dup_rate = dup_count / total if total else 0
    max_rate = cfg.UNIQUENESS_RULES["full_row"]["max_duplicate_rate"]
    results.append({
        "metric": "uniqueness",
        "column": "full_row",
        "score": round(1 - dup_rate, 4),
        "threshold": 1 - max_rate,
        "passed": dup_rate <= max_rate,
        "details": f"{dup_count} exact duplicate rows out of {total} ({dup_rate:.1%})",
    })

    # composite-key near-duplicates (e.g. same company+date+location reported twice)
    ck = cfg.UNIQUENESS_RULES.get("composite_key")
    if ck and all(c in df.columns for c in ck["columns"]):
        dup_mask = df.duplicated(subset=ck["columns"], keep=False)
        dup_rows = dup_mask.sum()
        dup_rate2 = dup_rows / total if total else 0
        max_rate2 = ck["max_duplicate_rate"]
        results.append({
            "metric": "uniqueness",
            "column": "+".join(ck["columns"]),
            "score": round(1 - dup_rate2, 4),
            "threshold": 1 - max_rate2,
            "passed": dup_rate2 <= max_rate2,
            "details": f"{dup_rows} rows share the same {', '.join(ck['columns'])} as another row ({dup_rate2:.1%})",
        })

    return results


def check_validity(df: pd.DataFrame) -> list:
    results = []
    total = len(df)
    for col, rule in cfg.VALIDITY_RULES.items():
        if col not in df.columns:
            continue
        valid_mask = pd.Series([True] * total, index=df.index)

        if rule["type"] == "numeric":
            numeric = pd.to_numeric(df[col], errors="coerce")
            not_null = df[col].notna()
            in_range = numeric.notna()
            if "min" in rule:
                in_range &= numeric >= rule["min"]
            if "max" in rule:
                in_range &= numeric <= rule["max"]
            # nulls are a completeness concern, not a validity failure -
            # only count rows that HAVE a value but violate the range
            valid_mask = ~not_null | in_range

        elif rule["type"] == "date":
            parsed = pd.to_datetime(df[col], errors="coerce")
            valid_mask = ~df[col].notna() | parsed.notna()

        valid_ratio = valid_mask.sum() / total if total else 0
        results.append({
            "metric": "validity",
            "column": col,
            "score": round(valid_ratio, 4),
            "threshold": 0.98,
            "passed": valid_ratio >= 0.98,
            "details": f"{valid_mask.sum()}/{total} valid values ({valid_ratio:.1%})",
        })
    return results


def check_consistency(df: pd.DataFrame) -> list:
    results = []
    total = len(df)

    if "country" in df.columns:
        countries_present = set(df["country"].dropna().unique())
        alias_hits = 0
        offending_pairs = []
        for a, b in cfg.COUNTRY_ALIASES:
            if a in countries_present and b in countries_present:
                alias_hits += df["country"].isin([a, b]).sum()
                offending_pairs.append(f"'{a}' vs '{b}'")

        ok_ratio = 1 - (alias_hits / total if total else 0)
        results.append({
            "metric": "consistency",
            "column": "country",
            "score": round(ok_ratio, 4),
            "threshold": 0.99,
            "passed": alias_hits == 0,
            "details": (
                f"Found conflicting country name variants: {', '.join(offending_pairs)} "
                f"({alias_hits} affected rows)"
                if offending_pairs else "No known country name inconsistencies found"
            ),
        })

    return results


def check_timeliness(df: pd.DataFrame) -> list:
    """Dataset-level freshness check: is the most recent record recent enough?
    (Not a per-row check, since this dataset is a historical archive back to 2020 -
    individual old rows are expected and not a quality problem.)"""
    results = []
    col = cfg.TIMELINESS_RULES["date_column"]
    if col not in df.columns:
        return results

    dates = pd.to_datetime(df[col], errors="coerce")
    if dates.notna().sum() == 0:
        return results

    most_recent = dates.max()
    age_days = (pd.Timestamp.now() - most_recent).days
    max_age = cfg.TIMELINESS_RULES["max_age_days"]
    passed = age_days <= max_age
    # score as a smooth ratio rather than binary, capped at [0,1]
    score = max(0.0, min(1.0, 1 - (age_days / max_age))) if max_age else (1.0 if passed else 0.0)

    results.append({
        "metric": "timeliness",
        "column": col,
        "score": round(score, 4),
        "threshold": 1.0,
        "passed": passed,
        "details": f"Most recent record is {age_days} day(s) old (limit: {max_age} days)",
    })
    return results


def compute_health_score(all_results: list) -> float:
    """Weighted overall health score across all metric dimensions."""
    by_metric = {}
    for r in all_results:
        by_metric.setdefault(r["metric"], []).append(r["score"])

    weighted_sum, weight_total = 0, 0
    for metric, weight in cfg.HEALTH_SCORE_WEIGHTS.items():
        scores = by_metric.get(metric)
        if scores:
            avg = sum(scores) / len(scores)
            weighted_sum += avg * weight
            weight_total += weight

    return round(weighted_sum / weight_total, 4) if weight_total else 0.0


def run_all_checks(df: pd.DataFrame) -> dict:
    """Runs the full suite of checks and returns a structured run result."""
    run_id = _new_run_id()
    timestamp = datetime.now(timezone.utc).isoformat()

    all_results = []
    all_results += check_completeness(df)
    all_results += check_uniqueness(df)
    all_results += check_validity(df)
    all_results += check_consistency(df)
    all_results += check_timeliness(df)

    all_results = [_sanitize_result(r) for r in all_results]
    for r in all_results:
        r["run_id"] = run_id
        r["timestamp"] = timestamp
        r["dataset"] = cfg.DATASET_NAME

    health_score = float(compute_health_score(all_results))
    failed = [r for r in all_results if not r["passed"]]

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "dataset": cfg.DATASET_NAME,
        "row_count": len(df),
        "health_score": health_score,
        "checks_run": len(all_results),
        "checks_failed": len(failed),
        "results": all_results,
    }
