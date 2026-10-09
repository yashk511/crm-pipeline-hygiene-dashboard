"""Logic tests for the CRM pipeline. Run from the repo root: pytest"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CLEAN = ROOT / "clean"
MARTS = CLEAN / "sql_marts"
AS_OF = pd.Timestamp("2026-09-01")

CHRONOLOGICAL = {"Prospecting": 1, "Qualification": 2, "Proposal": 3,
                 "Negotiation": 4, "Closed Won": 5, "Closed Lost": 6}


def fact():
    return pd.read_csv(CLEAN / "fact_opportunities.csv", parse_dates=["last_activity_date", "created_date"])


def test_no_ground_truth_leakage_or_blended_age_field():
    cols = set(fact().columns)
    assert "expected_win_probability" not in cols  # generator ground truth must stay out of the model
    assert "deal_age_days" not in cols             # blended open-age / sales-cycle field was retired
    assert {"open_age_days", "sales_cycle_days", "stage_order"} <= cols


def test_stage_order_is_chronological_in_fact_and_history():
    f = fact()
    assert (f["stage"].map(CHRONOLOGICAL) == f["stage_order"]).all()
    h = pd.read_csv(CLEAN / "opportunity_stage_history.csv")
    assert (h["stage"].map(CHRONOLOGICAL) == h["stage_order"]).all()


def test_stale_flag_matches_definition():
    f = fact()
    expected_days = (AS_OF - f["last_activity_date"]).dt.days
    assert (f["days_since_activity"] == expected_days).all()
    stale = f[f["is_stale"]]
    assert (~stale["is_closed"]).all()
    assert (stale["days_since_activity"] > 30).all()
    # every open deal over the threshold is flagged, none is missed
    should_be_stale = (~f["is_closed"]) & (f["days_since_activity"] > 30)
    assert (should_be_stale == f["is_stale"]).all()


def test_age_fields_are_mutually_exclusive_by_status():
    f = fact()
    assert f.loc[f["is_closed"], "sales_cycle_days"].notna().all()
    assert f.loc[~f["is_closed"], "sales_cycle_days"].isna().all()
    # open age exists ONLY for open deals, so AVERAGE(open_age_days) can never include closed ones
    assert f.loc[~f["is_closed"], "open_age_days"].notna().all()
    assert f.loc[f["is_closed"], "open_age_days"].isna().all()
    assert (f["open_age_days"].dropna() >= 0).all()


def test_beyond_max_cycle_flag_definition():
    f = fact()
    longest = f.loc[f["is_closed"], "sales_cycle_days"].max()
    expected = (~f["is_closed"]) & (f["open_age_days"] > longest)
    assert (expected == f["beyond_max_cycle_flag"]).all()


def test_dedup_quality_against_ground_truth():
    m = pd.read_csv(CLEAN / "quality_metrics.csv").set_index("metric")["value"]
    assert m["Dedup Precision Pct"] >= 99
    assert m["Dedup Recall Pct"] >= 99
    merge_map = pd.read_csv(CLEAN / "account_merge_map.csv")
    assert merge_map["is_survivor"].sum() == m["Accounts After Cleaning"]
    assert len(merge_map) == m["Accounts Before Cleaning"]


def test_validation_summary_is_consistent_with_issue_log():
    summary = pd.read_csv(CLEAN / "validation_summary.csv")
    issues = pd.read_csv(CLEAN / "data_quality_issues.csv")
    assert len(summary) == 10
    for row in summary.itertuples():
        assert (issues["issue_type"] == row.issue_type).sum() == row.issue_count
        assert row.status == ("PASS" if row.issue_count == 0 else "REVIEW")
    assert summary.set_index("issue_type").loc["missing_lead_source", "issue_count"] == fact()["lead_source_missing_flag"].sum()


def test_imputation_is_reported_separately():
    m = pd.read_csv(CLEAN / "quality_metrics.csv").set_index("metric")["value"]
    assert m["Open Pipeline Value Excluding Imputed"] < m["Open Pipeline Value"]
    f = fact()
    assert f["amount_missing_flag"].sum() == m["Amounts Imputed"]
    assert f["amount"].notna().all()


def test_all_marts_exported_and_progression_rates_are_valid():
    assert len(list(MARTS.glob("*.csv"))) == 8
    assert not (MARTS / "01_pipeline_funnel.csv").exists()  # the >100% "funnel" was retired
    p = pd.read_csv(MARTS / "06_stage_progression.csv")
    assert (p["progressed_to_date_pct"] <= 100).all()
    assert (p["opportunities_progressed"] <= p["opportunities_at_start"]).all()
    assert p["from_order"].is_monotonic_increasing


def test_win_rate_intervals_are_ordered():
    s = pd.read_csv(MARTS / "07_win_rate_by_segment.csv")
    assert (s["ci95_low_pct"] <= s["win_rate_pct"]).all()
    assert (s["win_rate_pct"] <= s["ci95_high_pct"]).all()


def test_business_analysis_is_in_sync_with_marts():
    from build_analysis import build_report, OUT
    assert OUT.read_text(encoding="utf-8") == build_report()
