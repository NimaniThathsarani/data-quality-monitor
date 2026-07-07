"""
Central data quality rules configuration - World Layoffs dataset.

Columns: company, location, total_laid_off, date, percentage_laid_off,
         industry, source, stage, funds_raised, country, date_added

This is the single source of truth for what "good data" means for this
dataset. Editing this file is how the standards get updated -- no code
changes needed elsewhere. This also doubles as documentation for the
Data Governance Framework deliverable.
"""

DATASET_NAME = "world_layoffs"
DATA_PATH = "data/layoffs.csv"

# Completeness: minimum % of non-null values required per column.
# Thresholds below reflect realistic expectations for this dataset -
# e.g. total_laid_off/percentage_laid_off are legitimately often
# unreported by companies, so we don't demand 100% here.
COMPLETENESS_RULES = {
    "company": 1.0,
    "location": 0.98,
    "total_laid_off": 0.55,
    "date": 1.0,
    "percentage_laid_off": 0.50,
    "industry": 0.98,
    "stage": 0.98,
    "funds_raised": 0.80,
    "country": 0.98,
}

# Uniqueness rules
UNIQUENESS_RULES = {
    "full_row": {"max_duplicate_rate": 0.01},
    # near-duplicates: same company reported for the same date/location
    # more than once (often re-scraped or split entries)
    "composite_key": {
        "columns": ["company", "date", "location"],
        "max_duplicate_rate": 0.02,
    },
}

# Validity: value-level rules per column
VALIDITY_RULES = {
    "total_laid_off": {"type": "numeric", "min": 0},
    "percentage_laid_off": {"type": "numeric", "min": 0, "max": 1},
    "funds_raised": {"type": "numeric", "min": 0},
    "date": {"type": "date"},
    "date_added": {"type": "date"},
}

# Known aliases that should be standardized to a single value.
# Presence of both forms in the data is itself a consistency issue.
COUNTRY_ALIASES = [
    ("UAE", "United Arab Emirates"),
]

# Consistency: cross-field / cross-record logical rules
CONSISTENCY_RULES = [
    {
        "name": "country_alias_consistency",
        "description": "The same country should not appear under two different names (e.g. 'UAE' vs 'United Arab Emirates')",
    },
]

# Timeliness: dataset-level freshness check.
# Rather than checking every row's age (this is a historical archive back
# to 2020, so per-row age isn't meaningful), we check whether the dataset
# as a whole has been refreshed recently, using the most recent date_added.
TIMELINESS_RULES = {
    "date_column": "date_added",
    "max_age_days": 14,
}

# Alerting thresholds
ALERT_THRESHOLDS = {
    "critical": 0.80,
    "warning": 0.95,
}

# Overall dataset health score weighting
HEALTH_SCORE_WEIGHTS = {
    "completeness": 0.25,
    "uniqueness": 0.20,
    "validity": 0.30,
    "consistency": 0.15,
    "timeliness": 0.10,
}
