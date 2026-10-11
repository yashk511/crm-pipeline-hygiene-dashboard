"""Load the cleaned CRM tables. Pure pandas (no Streamlit) so tests can import it."""
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "clean"
AS_OF = os.environ.get("CRM_AS_OF_DATE", "2026-09-01")  # same default as clean_data.py
GITHUB_URL = "https://github.com/yashk511/crm-pipeline-hygiene-dashboard"


def load_all() -> dict:
    fact = pd.read_csv(
        CLEAN / "fact_opportunities.csv",
        parse_dates=["created_date", "close_date", "last_activity_date"],
    )
    reps = pd.read_csv(CLEAN / "dim_reps.csv")
    accounts = pd.read_csv(CLEAN / "dim_accounts.csv")
    fact = fact.merge(reps, on="rep_id", how="left").merge(
        accounts[["account_id", "account_name", "industry", "country"]],
        on="account_id",
        how="left",
    )
    return {
        "fact": fact,
        "accounts": accounts,
        "history": pd.read_csv(CLEAN / "opportunity_stage_history.csv"),
        "quality": pd.read_csv(CLEAN / "quality_metrics.csv").set_index("metric")["value"],
        "validation": pd.read_csv(CLEAN / "validation_summary.csv"),
        "issues": pd.read_csv(CLEAN / "data_quality_issues.csv"),
        "merge_map": pd.read_csv(CLEAN / "account_merge_map.csv"),
        "metric_dictionary": (ROOT / "metric_dictionary.md").read_text(encoding="utf-8"),
    }
