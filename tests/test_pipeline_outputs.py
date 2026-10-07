from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "clean"


def load_fact():
    return pd.read_csv(CLEAN / "fact_opportunities.csv")


def test_fact_row_count_and_age_fields():
    fact = load_fact()

    assert len(fact) == 900
    assert {"open_age_days", "sales_cycle_days", "deal_age_days"}.issubset(fact.columns)
    assert fact.loc[fact["is_closed"], "sales_cycle_days"].notna().all()
    assert fact.loc[~fact["is_closed"], "sales_cycle_days"].isna().all()


def test_stale_opportunities_are_open_and_over_threshold():
    fact = load_fact()
    stale = fact[fact["is_stale"]]

    assert len(stale) == 201
    assert (~stale["is_closed"]).all()
    assert (stale["days_since_activity"] > 30).all()


def test_audit_outputs_exist_and_capture_missing_amounts():
    merge_map = pd.read_csv(CLEAN / "account_merge_map.csv")
    issues = pd.read_csv(CLEAN / "data_quality_issues.csv")

    assert len(merge_map) == 162
    assert (merge_map["is_survivor"] == True).sum() == 137
    assert (issues["issue_type"] == "invalid_amount").sum() == 33
