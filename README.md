# CRM Pipeline & Data Hygiene Dashboard

A sales-ops style project: takes a deliberately messy CRM export (the kind an analyst actually inherits from Dynamics/Salesforce) and turns it into a clean, modeled dataset powering a Power BI dashboard — covering data de-duplication, field standardization, missing-field flagging, and pipeline hygiene monitoring.

> Data is synthetic and seeded (`generate_data.py`). Lead-source, product and team effects are planted simulation parameters, not real-world evidence.

## What was cleaned and audited
| Problem | Approach | Result |
|---|---|---|
| **Duplicate accounts** | Name normalization + fuzzy match, blocked by country | 162 -> 140; 100% precision/recall vs ground truth |
| **Non-standard stages** | Rule-based mapping | 21 raw spellings -> 6 canonical stages |
| **Missing amounts** | Flagged, median-imputed, reported separately | 34 flagged; $10.96M pipeline excluding imputed vs $11.28M total |
| **Missing DUNS** | Flagged, never invented | 39 accounts isolated for seller follow-up |
| **Stale pipeline** | No activity in 30+ days | 183 deals, $3.76M (33% of open pipeline) |
| **Validation** | 9 row-level rules, PASS/REVIEW summary | 7 PASS, 2 REVIEW |

## Technical Highlights
* **Event-Based Funnel (SQL Window Functions):** Replaced static current-stage reporting with true historical stage progression using CTEs and `LAG()` window functions in DuckDB to calculate accurate stage-to-stage conversion drop-off.
* **Data Quality Modeling (DAX):** Isolated dirty records and missing data fields using DAX integer logic rather than letting implicit blanks break matrix visuals.
* **Fuzzy Matching:** Achieved 100% duplicate pair precision using country-blocked sequence matching.

## What's in here
```text
raw/                     ← messy source export (as "received" from CRM)
  accounts.csv           duplicate company records, missing DUNS numbers
  account_ground_truth.csv generator-only duplicate labels, not an analysis input
  reps.csv
  opportunities.csv      inconsistent stage naming, some missing amounts

clean/                   ← output of clean_data.py — Power BI-ready
  dim_accounts.csv       deduped, DUNS-missing flag added
  dim_reps.csv
  dim_date.csv           calendar table for time intelligence
  fact_opportunities.csv standardized stages, stale-deal flag, deal age
  quality_metrics.csv    dashboard-ready data quality scorecard metrics
  account_merge_map.csv  account survivor and merge audit trail
  data_quality_issues.csv row-level validation issues for follow-up
  validation_summary.csv pass/review status for every validation rule
  opportunity_stage_history.csv standardized stage transition events
  sql_marts/             DuckDB output tables for dashboarding
  data_quality_report.md before/after metrics

generate_data.py         builds the raw/ files (synthetic, seeded/reproducible)
clean_data.py            the actual cleaning + modeling pipeline
sql/                     DuckDB business-question queries
metric_dictionary.md     KPI definitions, grain, and caveats
requirements.txt         reproducible Python dependencies
run_sql.py               executes SQL and exports analysis marts
analysis/                findings, recommendations, and limitations
```

## Build the Power BI dashboard (Windows, Power BI Desktop)

**1. Import**
Get Data → Text/CSV → import all five files from `clean/`.

- `dim_accounts.csv`
- `dim_reps.csv`
- `dim_date.csv`
- `fact_opportunities.csv`
- `quality_metrics.csv`

**2. Relationships** (Model view)
- `fact_opportunities[account_id]` → `dim_accounts[account_id]` (many-to-one)
- `fact_opportunities[rep_id]` → `dim_reps[rep_id]` (many-to-one)
- `fact_opportunities[created_date]` → `dim_date[date]` (many-to-one)

**3. DAX measures** (New Measure, paste these in)
```DAX
Open Pipeline Value =
CALCULATE(SUM(fact_opportunities[amount]), fact_opportunities[is_closed] = FALSE)

Win Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_won] = TRUE),
    CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_closed] = TRUE)
)

Stale Opportunities =
CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_stale] = TRUE)

Stale % of Open Pipeline =
DIVIDE(
    [Stale Opportunities],
    CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_closed] = FALSE)
)

Avg Deal Age (Days) =
AVERAGE(fact_opportunities[deal_age_days])

DUNS Completeness % =
DIVIDE(
    CALCULATE(COUNTROWS(dim_accounts), dim_accounts[duns_missing_flag] = FALSE),
    COUNTROWS(dim_accounts)
)
```

**4. Completed dashboard pages**
- **Executive Pipeline Summary** — cards for Open Pipeline Value / Win Rate / Stale Opportunities / Avg Deal Age; bar chart of pipeline value by stage; line chart of opportunities created by month.
- **Pipeline Hygiene** — table of stale opportunities (account, rep, days since activity, amount) sorted descending; stale % trend by month.
- **Rep / Regional Performance** — win rate by rep, pipeline value by region, deals closed by team.
- **Funnel & Stage Conversion** — historical, event-based stage progression mapping conversion rates through the pipeline.
- **Data Quality Scorecard** — DUNS completeness by industry, a callout of duplicate accounts merged, missing amounts isolated, and non-standard stage values normalized.

The Power BI report is built from the clean tables above and uses a star-schema model with `fact_opportunities` at its center. The dashboard is designed for sales operations reporting, pipeline inspection, rep performance analysis, and CRM data-quality follow-up.

## Verified dashboard results

The completed report was validated against the Python-generated quality report:

| KPI | Result |
|---|---:|
| Open pipeline value | $11,277,500 |
| Win rate | 47.1% |
| Stale opportunities | 183 |
| Stale percent of open pipeline | 33.3% |
| Average deal age | 213.95 days |
| Accounts before cleaning | 162 |
| Duplicate accounts merged | 22 |
| Deduplication precision | 100.0% |
| Deduplication recall | 100.0% |
| Accounts after cleaning | 140 |
| Missing amounts imputed | 34 |

## v2 Analytical Upgrades

The upgraded pipeline separates open opportunity age from closed-deal sales cycle, makes the as-of date and stale threshold configurable, and reports stale pipeline by value as well as by count. It also preserves imputation-aware pipeline value and writes an account merge map plus row-level validation issues. The validation summary reports zero-count rules as explicit `PASS` results and flags issues requiring operational review.

On the v2 branch, duplicate records retain the original company's country and industry. Country-blocked matching now achieves 100.0% pair precision and 100.0% pair recall, merging the 22 injected duplicate records into 140 clean accounts. The signal-aware v2 seeded outputs currently contain 183 stale opportunities, a 47.1% closed-deal win rate, and $11,277,500 of open pipeline. Product, team, and lead-source effects are planted simulation parameters, not real-world evidence.

The `sql/` layer uses DuckDB to answer business questions about stage funnel conversion, rep performance, monthly pipeline trends, aging buckets, stale deal prioritization, and event-based stage transitions. These queries run directly against the clean CSV outputs. Run `python run_sql.py` to export the six query results to `clean/sql_marts/` for downstream analysis or Power BI ingestion.

The descriptive findings and operating recommendations are documented in `analysis/business_analysis.md`. Because the current data is synthetic and does not plant causal win-rate drivers, that report deliberately avoids claiming that any rep, region, product, or lead source causes performance.

## Reproduce from scratch
```bash
pip install pandas numpy faker duckdb
python generate_data.py
python clean_data.py
python run_sql.py
```