"""
CRM Data Cleaning & Modeling Pipeline
--------------------------------------
Takes the raw messy CRM export (raw/accounts.csv, reps.csv, opportunities.csv)
and produces a clean star-schema data model ready for Power BI:

    clean/dim_accounts.csv
    clean/dim_reps.csv
    clean/dim_date.csv
    clean/fact_opportunities.csv
    clean/data_quality_report.md

This mirrors the actual accountabilities in the job description:
  - CRM data hygiene / de-duplication / validation checks
  - Standardizing non-standard field values
  - Flagging missing required fields (DUNS number)
  - Identifying stale opportunities / pipeline hygiene issues
  - Structuring a scalable dataset that powers dashboards & KPIs
"""
import re
import difflib
from itertools import combinations
import pandas as pd
from datetime import datetime
import os

RAW = "raw"
OUT = "clean"
os.makedirs(OUT, exist_ok=True)

TODAY = datetime.strptime(os.getenv("CRM_AS_OF_DATE", "2026-09-01"), "%Y-%m-%d")
STALE_THRESHOLD_DAYS = int(os.getenv("CRM_STALE_THRESHOLD_DAYS", "30"))

accounts = pd.read_csv(f"{RAW}/accounts.csv", dtype=str)
reps = pd.read_csv(f"{RAW}/reps.csv", dtype=str)
opps = pd.read_csv(f"{RAW}/opportunities.csv", dtype=str)

n_accounts_before = len(accounts)

# ------------------------------------------------------------------
# 1. Standardize account names for matching (dedup key), without
#    destroying the original display name.
# ------------------------------------------------------------------
def normalize_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[.,]", "", name)
    name = re.sub(r"\s+", " ", name)
    for suffix in [" incorporated", " inc", " llc", " corp", " corporation", " ltd"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()

accounts["name_key"] = accounts["account_name"].apply(normalize_name)

# ------------------------------------------------------------------
# 2. Fuzzy-cluster accounts that are the same company entered
#    differently (exact key match + high-similarity near-matches).
# ------------------------------------------------------------------
canonical_map = {}          # (country, name_key) -> canonical key
match_scores = {}
review_keys = set()
seen_by_country = {}

for row in accounts[["account_id", "name_key", "country"]].itertuples(index=False):
    country = str(row.country).strip().lower()
    key = (country, row.name_key)
    if key in canonical_map:
        continue

    seen = seen_by_country.setdefault(country, [])
    candidates = [
        (candidate, difflib.SequenceMatcher(None, row.name_key, candidate).ratio())
        for candidate in seen
    ]
    candidate, score = max(candidates, key=lambda item: item[1], default=(None, 0.0))
    if score >= 0.92:
        canonical_map[key] = canonical_map[(country, candidate)]
        match_scores[key] = score
    else:
        canonical_map[key] = f"{country}::{row.name_key}"
        match_scores[key] = score
        seen.append(row.name_key)
        if score >= 0.85:
            review_keys.add(key)

accounts["country_key"] = accounts["country"].fillna("").str.strip().str.lower()
accounts["canonical_key"] = [
    canonical_map[(country, name_key)]
    for country, name_key in zip(accounts["country_key"], accounts["name_key"])
]
accounts["match_score"] = [
    match_scores[(country, name_key)]
    for country, name_key in zip(accounts["country_key"], accounts["name_key"])
]
accounts["review_required"] = [
    (country, name_key) in review_keys
    for country, name_key in zip(accounts["country_key"], accounts["name_key"])
]

# For each canonical group, pick the "best" surviving record:
# prefer the one with a DUNS number, then the earliest created_date.
accounts["has_duns"] = accounts["duns_number"].fillna("").str.strip() != ""
accounts["created_date"] = pd.to_datetime(accounts["created_date"])

accounts_sorted = accounts.sort_values(
    by=["canonical_key", "has_duns", "created_date"],
    ascending=[True, False, True]
)
survivors = accounts_sorted.drop_duplicates(subset="canonical_key", keep="first").copy()

n_duplicates_merged = n_accounts_before - len(survivors)

# map every original account_id -> surviving canonical account_id
id_map = accounts.merge(
    survivors[["canonical_key", "account_id"]].rename(columns={"account_id": "canonical_account_id"}),
    on="canonical_key", how="left"
)[["account_id", "account_name", "source_company_id", "canonical_key", "canonical_account_id", "match_score", "review_required"]]
id_map["merge_status"] = id_map["account_id"] == id_map["canonical_account_id"]
id_map.rename(columns={"merge_status": "is_survivor"}).to_csv(
    f"{OUT}/account_merge_map.csv", index=False
)
account_id_lookup = dict(zip(id_map.account_id, id_map.canonical_account_id))

account_records = id_map.set_index("account_id")
true_duplicate_pairs = {
    tuple(sorted(pair))
    for source_id, group in id_map.groupby("source_company_id")
    if len(group) > 1
    for pair in combinations(group["account_id"], 2)
}
predicted_duplicate_pairs = {
    tuple(sorted(pair))
    for canonical_id, group in id_map.groupby("canonical_account_id")
    if len(group) > 1
    for pair in combinations(group["account_id"], 2)
}
correct_duplicate_pairs = true_duplicate_pairs & predicted_duplicate_pairs
dedup_precision = round(
    len(correct_duplicate_pairs) / len(predicted_duplicate_pairs) * 100, 1
) if predicted_duplicate_pairs else 100.0
dedup_recall = round(
    len(correct_duplicate_pairs) / len(true_duplicate_pairs) * 100, 1
) if true_duplicate_pairs else 100.0

pct_missing_duns_before = round((~accounts["has_duns"]).mean() * 100, 1)
pct_missing_duns_after = round((~survivors["has_duns"]).mean() * 100, 1)

dim_accounts = survivors.rename(columns={"account_id": "account_id"})[
    ["account_id", "account_name", "industry", "country", "duns_number",
     "created_date", "owner_rep_id", "account_source"]
].copy()
dim_accounts["account_name"] = dim_accounts["account_name"].str.strip()
dim_accounts["duns_missing_flag"] = dim_accounts["duns_number"].fillna("").str.strip() == ""
dim_accounts["account_source"] = dim_accounts["account_source"].replace("", "Unknown").fillna("Unknown")
dim_accounts.to_csv(f"{OUT}/dim_accounts.csv", index=False)

# ------------------------------------------------------------------
# 3. Reps dimension (pass-through)
# ------------------------------------------------------------------
reps.to_csv(f"{OUT}/dim_reps.csv", index=False)

# ------------------------------------------------------------------
# 4. Standardize opportunity stage values (non-standard field values)
# ------------------------------------------------------------------
def standardize_stage(raw):
    s = str(raw).strip().lower().replace("-", " ")
    if "prospect" in s:
        return "Prospecting"
    if "qualif" in s:
        return "Qualification"
    if "proposal" in s:
        return "Proposal"
    if "negotiat" in s:
        return "Negotiation"
    if "won" in s:
        return "Closed Won"
    if "lost" in s:
        return "Closed Lost"
    return "Unclassified"

opps["stage"] = opps["stage_raw"].apply(standardize_stage)
n_non_standard_stage_values = opps["stage_raw"].nunique() - opps["stage"].nunique()

opps["account_id"] = opps["account_id"].map(account_id_lookup).fillna(opps["account_id"])
opps["created_date"] = pd.to_datetime(opps["created_date"])
opps["close_date"] = pd.to_datetime(opps["close_date"], errors="coerce")
opps["last_activity_date"] = pd.to_datetime(opps["last_activity_date"])
opps["amount"] = pd.to_numeric(opps["amount"], errors="coerce")

opps["is_closed"] = opps["stage"].isin(["Closed Won", "Closed Lost"])
opps["is_won"] = opps["stage"] == "Closed Won"
opps["days_since_activity"] = (TODAY - opps["last_activity_date"]).dt.days
opps["is_stale"] = (~opps["is_closed"]) & (opps["days_since_activity"] > STALE_THRESHOLD_DAYS)
opps["open_age_days"] = (pd.Timestamp(TODAY) - opps["created_date"]).dt.days
opps["sales_cycle_days"] = (
    opps["close_date"] - opps["created_date"]
).dt.days
# Retain the v1 field for compatibility; v2 analysis should use the explicit fields.
opps["deal_age_days"] = opps["sales_cycle_days"].fillna(opps["open_age_days"])
opps["amount_missing_flag"] = opps["amount"].isna()
amount_before_imputation = opps["amount"].copy()
opps["amount"] = opps["amount"].fillna(opps.groupby("product")["amount"].transform("median"))

# ------------------------------------------------------------------
# 5. Row-level validation issues for operational follow-up.
# ------------------------------------------------------------------
issue_rows = []

def add_issue(mask, issue_type, field_name, severity, description):
    for record_id in opps.loc[mask, "opp_id"].astype(str):
        issue_rows.append({
            "record_type": "opportunity",
            "record_id": record_id,
            "issue_type": issue_type,
            "field_name": field_name,
            "severity": severity,
            "issue_description": description,
        })

add_issue(~opps["account_id"].isin(set(survivors["account_id"])), "orphan_account_id", "account_id", "high", "Opportunity account does not exist in dim_accounts")
add_issue(~opps["rep_id"].isin(set(reps["rep_id"])), "orphan_rep_id", "rep_id", "high", "Opportunity rep does not exist in dim_reps")
add_issue(opps["opp_id"].duplicated(keep=False), "duplicate_opportunity_id", "opp_id", "high", "Opportunity ID is duplicated")
add_issue(opps["close_date"].notna() & (opps["close_date"] < opps["created_date"]), "close_before_create", "close_date", "high", "Close date precedes created date")
add_issue(opps["is_closed"] & opps["close_date"].isna(), "closed_without_close_date", "close_date", "medium", "Closed opportunity has no close date")
add_issue(~opps["is_closed"] & opps["close_date"].notna(), "open_with_close_date", "close_date", "medium", "Open opportunity has a close date")
add_issue(opps["amount_missing_flag"] | (opps["amount"] <= 0), "invalid_amount", "amount", "high", "Amount was missing or is non-positive")
add_issue(opps["stage"] == "Unclassified", "unclassified_stage", "stage", "high", "Stage could not be mapped to a canonical value")
pd.DataFrame(issue_rows, columns=[
    "record_type", "record_id", "issue_type", "field_name", "severity", "issue_description"
]).to_csv(f"{OUT}/data_quality_issues.csv", index=False)

n_stale = int(opps["is_stale"].sum())
n_open = int((~opps["is_closed"]).sum())
n_stale_value = round(opps.loc[opps["is_stale"], "amount"].sum(), 0)
n_stale_value_pct = round(
    n_stale_value / opps.loc[~opps["is_closed"], "amount"].sum() * 100, 1
)
total_open_pipeline_excluding_imputed = round(
    amount_before_imputation.loc[(~opps["is_closed"]) & amount_before_imputation.notna()].sum(), 0
)
average_open_age = round(opps.loc[~opps["is_closed"], "open_age_days"].mean(), 1)
average_sales_cycle = round(opps.loc[opps["is_closed"], "sales_cycle_days"].mean(), 1)

fact_opportunities = opps[[
    "opp_id", "account_id", "rep_id", "product", "lead_source", "stage",
    "amount", "created_date", "close_date", "last_activity_date",
    "days_since_activity", "open_age_days", "sales_cycle_days", "deal_age_days",
    "is_closed", "is_won",
    "is_stale", "amount_missing_flag",
]].copy()
fact_opportunities.to_csv(f"{OUT}/fact_opportunities.csv", index=False)

# ------------------------------------------------------------------
# 6. Date dimension (for Power BI time intelligence)
# ------------------------------------------------------------------
start = opps["created_date"].min()
end = TODAY
dim_date = pd.DataFrame({"date": pd.date_range(start, end, freq="D")})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%b %Y")
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str) + " " + dim_date["date"].dt.year.astype(str)
dim_date.to_csv(f"{OUT}/dim_date.csv", index=False)

# ------------------------------------------------------------------
# 7. Data quality scorecard
# ------------------------------------------------------------------
win_rate = round(opps.loc[opps.is_closed, "is_won"].mean() * 100, 1)
total_open_pipeline = round(opps.loc[~opps.is_closed, "amount"].sum(), 0)

report = f"""# CRM Data Quality & Cleaning Report

## De-duplication
- Accounts before cleaning: **{n_accounts_before}**
- Duplicate account records merged: **{n_duplicates_merged}**
- Accounts after cleaning: **{len(dim_accounts)}**
- Duplicate pair precision against generator ground truth: **{dedup_precision}%**
- Duplicate pair recall against generator ground truth: **{dedup_recall}%**

## Missing required fields (DUNS number)
- Missing before cleanup: **{pct_missing_duns_before}%** of accounts
- Missing after cleanup (still unresolved, flagged for outreach): **{pct_missing_duns_after}%** of accounts
  → `duns_missing_flag = True` in `dim_accounts.csv` for seller follow-up.

## Non-standard field values
- Raw stage values found: **{opps['stage_raw'].nunique()}** distinct strings
  (e.g. "closed-won", "Won", "CLOSED WON" all mapped to one canonical stage)
- Standardized down to **{opps['stage'].nunique()}** canonical stages

## Pipeline hygiene
- Open opportunities: **{n_open}**
- Stale opportunities (open, no activity in {STALE_THRESHOLD_DAYS}+ days): **{n_stale}**
  ({round(n_stale / n_open * 100, 1)}% of open pipeline — flagged for rep follow-up)
- Total open pipeline value: **${total_open_pipeline:,.0f}**
- Open pipeline value excluding imputed amounts: **${total_open_pipeline_excluding_imputed:,.0f}**
- Stale pipeline value: **${n_stale_value:,.0f}** ({n_stale_value_pct}% of open pipeline value)
- Overall win rate (closed deals): **{win_rate}%**

## Missing amounts
- Opportunities with missing deal amount, imputed with product-level median: **{int(opps['amount_missing_flag'].sum())}**
"""
with open(f"{OUT}/data_quality_report.md", "w", encoding="utf-8") as f:
    f.write(report)

# ------------------------------------------------------------------
# 8. Quality metrics as a small table (for a dynamic Power BI scorecard
#    page instead of static text boxes)
# ------------------------------------------------------------------
metrics = pd.DataFrame([
    {"metric": "Accounts Before Cleaning", "value": n_accounts_before},
    {"metric": "Duplicate Accounts Merged", "value": n_duplicates_merged},
    {"metric": "Dedup Precision Pct", "value": dedup_precision},
    {"metric": "Dedup Recall Pct", "value": dedup_recall},
    {"metric": "Accounts After Cleaning", "value": len(dim_accounts)},
    {"metric": "Pct Missing DUNS Before", "value": pct_missing_duns_before},
    {"metric": "Pct Missing DUNS After", "value": pct_missing_duns_after},
    {"metric": "Raw Stage Values Found", "value": int(opps["stage_raw"].nunique())},
    {"metric": "Canonical Stages After Cleaning", "value": int(opps["stage"].nunique())},
    {"metric": "Open Opportunities", "value": n_open},
    {"metric": "Stale Opportunities", "value": n_stale},
    {"metric": "Stale Pct Of Open Pipeline", "value": round(n_stale / n_open * 100, 1)},
    {"metric": "Open Pipeline Value", "value": total_open_pipeline},
    {"metric": "Open Pipeline Value Excluding Imputed", "value": total_open_pipeline_excluding_imputed},
    {"metric": "Stale Pipeline Value", "value": n_stale_value},
    {"metric": "Stale Value Pct Of Open Pipeline", "value": n_stale_value_pct},
    {"metric": "Average Open Age Days", "value": average_open_age},
    {"metric": "Average Sales Cycle Days", "value": average_sales_cycle},
    {"metric": "Win Rate Pct", "value": win_rate},
    {"metric": "Amounts Imputed", "value": int(opps["amount_missing_flag"].sum())},
])
metrics.to_csv(f"{OUT}/quality_metrics.csv", index=False)

print(report)
