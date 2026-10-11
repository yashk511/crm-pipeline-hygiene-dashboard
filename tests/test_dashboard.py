"""Dashboard metric tests: the app's numbers must equal the pipeline's own outputs."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard import metrics as m  # noqa: E402
from dashboard.data import load_all  # noqa: E402

MARTS = ROOT / "clean" / "sql_marts"


@pytest.fixture(scope="module")
def data():
    return load_all()


def test_kpis_match_quality_metrics(data):
    k, q = m.kpis(data["fact"]), data["quality"]
    assert k["open_value"] == q["Open Pipeline Value"]
    assert k["open_value_excl_imputed"] == q["Open Pipeline Value Excluding Imputed"]
    assert k["stale_count"] == q["Stale Opportunities"]
    assert k["stale_value"] == q["Stale Pipeline Value"]
    assert round(100 * k["win_rate"], 1) == q["Win Rate Pct"]
    assert round(k["avg_open_age"], 1) == q["Average Open Age Days"]
    assert k["beyond_cycle"] == q["Open Opportunities Beyond Longest Closed Cycle"]
    assert k["missing_lead_source"] == q["Missing Lead Source Opportunities"]


def test_stage_progression_matches_sql_mart(data):
    prog = m.stage_progression(data["history"], data["fact"]["opp_id"])
    mart = pd.read_csv(MARTS / "06_stage_progression.csv")
    merged = prog.merge(mart, on=["from_stage", "to_stage"])
    assert len(merged) == len(mart) == len(prog)
    assert (merged["progressed"] == merged["opportunities_progressed"]).all()
    assert (merged["progressed_pct"].round(1) == merged["progressed_to_date_pct"]).all()


def test_aging_buckets_match_sql_mart(data):
    ag = m.aging_buckets(data["fact"])
    mart = pd.read_csv(MARTS / "04_aging_buckets.csv")
    assert ag["open_opportunities"].tolist() == mart["open_opportunity_count"].tolist()
    assert ag["open_value"].tolist() == mart["open_pipeline_value"].tolist()


def test_win_rate_tables_match_sql_mart(data):
    mart = pd.read_csv(MARTS / "07_win_rate_by_segment.csv")
    for dim, col in (("lead_source", "lead_source"), ("product", "product")):
        mine = m.win_rate_table(data["fact"], col).set_index(col)
        ref = mart[mart["dimension"] == dim].set_index("segment")
        assert (mine["closed_deals"] == ref["closed_deals"]).all()
        assert (mine["win_rate"].mul(100).round(1) == ref["win_rate_pct"]).all()
        assert (mine["ci_low"].mul(100).round(1) == ref["ci95_low_pct"]).all()
        assert (mine["ci_high"].mul(100).round(1) == ref["ci95_high_pct"]).all()


def test_rep_table_matches_sql_mart(data):
    mine = m.rep_table(data["fact"]).set_index("rep_name")
    ref = pd.read_csv(MARTS / "02_rep_performance.csv").set_index("rep_name")
    assert (mine["open_pipeline"] == ref["open_pipeline_value"]).all()
    assert (mine["closed_deals"] == ref["closed_count"]).all()


def test_duns_by_industry_matches_quality_metrics(data):
    duns = m.duns_by_industry(data["accounts"])
    assert duns["accounts"].sum() == data["quality"]["Accounts After Cleaning"]
    overall = 100 * duns["missing"].sum() / duns["accounts"].sum()
    assert round(overall, 1) == data["quality"]["Pct Missing DUNS After"]


def test_merged_duplicates_count_matches_quality_metrics(data):
    dups = m.merged_duplicates(data["merge_map"], data["accounts"])
    assert len(dups) == data["quality"]["Duplicate Accounts Merged"]
    assert dups["merged_into"].notna().all()


def test_normalize_name_is_in_sync_with_clean_data():
    import re
    src = (ROOT / "clean_data.py").read_text(encoding="utf-8")
    assert 'for suffix in [" incorporated", " inc", " llc", " corp", " corporation", " ltd"]' in src
    assert m.normalize_name("  Suarez LLC Inc. ") == "suarez"
    assert m.normalize_name("NOVAK  PLC") == "novak plc"


def test_merge_types_are_reported_honestly(data):
    dups = m.merged_duplicates(data["merge_map"], data["accounts"])
    assert set(dups["match_type"]) <= {"Exact (normalized)", "Fuzzy"}
    assert "match_score" not in data["merge_map"].columns
    assert "nearest_other_similarity" in data["merge_map"].columns


def test_filters_reduce_totals_consistently(data):
    f = data["fact"]
    parts = [m.kpis(f[f["region"] == r])["open_value"] for r in f["region"].unique()]
    assert sum(parts) == m.kpis(f)["open_value"]


def test_app_runs_without_exceptions():
    at_mod = pytest.importorskip("streamlit.testing.v1")
    app = at_mod.AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    assert not app.exception
    assert len(app.tabs) == 6
    # change a filter and rerun: still no exception, and fewer opportunities
    app.sidebar.multiselect[0].set_value(["EMEA"]).run()
    assert not app.exception
