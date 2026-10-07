# CRM Pipeline & Data Hygiene Dashboard

A sales-ops style project: takes a deliberately messy CRM export (the kind
an analyst actually inherits from Dynamics/Salesforce) and turns it into a
clean, modeled dataset powering a Power BI dashboard — covering data
de-duplication, field standardization, missing-field flagging, and pipeline
hygiene monitoring.

## What's in here
```
raw/                     ← messy source export (as "received" from CRM)
  accounts.csv           duplicate company records, missing DUNS numbers
  account_ground_truth.csv generator-only duplicate labels, not an analysis input
  reps.csv
  opportunities.csv      inconsistent stage naming, some missing amounts

clean/                   ← output of clean_data.py — Power BI-ready
  dim_accounts.csv        deduped, DUNS-missing flag added
  dim_reps.csv
  dim_date.csv            calendar table for time intelligence
  fact_opportunities.csv  standardized stages, stale-deal flag, deal age
  quality_metrics.csv     dashboard-ready data quality scorecard metrics
  account_merge_map.csv   account survivor and merge audit trail
  data_quality_issues.csv row-level validation issues for follow-up
  validation_summary.csv  pass/review status for every validation rule
  data_quality_report.md  before/after metrics

generate_data.py         builds the raw/ files (synthetic, seeded/reproducible)
clean_data.py            the actual cleaning + modeling pipeline
sql/                     DuckDB business-question queries
metric_dictionary.md     KPI definitions, grain, and caveats
requirements.txt         reproducible Python dependencies
```

## The data problems this fixes (mirrors real Sales Ops work)
- **Duplicate accounts**: same company entered multiple times with name
  variants ("Acme Corp" / "ACME CORPORATION" / "Acme Corp.") — matched with
  a normalization + fuzzy-similarity pass and merged to one canonical record.
- **Missing required fields**: ~38% of raw accounts have no DUNS number.
  Cleaning doesn't invent one — it flags it (`duns_missing_flag`) for
  seller follow-up, which is the real remediation workflow.
- **Non-standard field values**: 21 raw spellings of deal stage
  ("closed-won", "Won", "CLOSED WON"...) standardized to 6 canonical stages.
- **Pipeline hygiene**: open opportunities with no activity in 30+ days are
  flagged `is_stale` — in this dataset, ~33% of open pipeline.

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
- **Pipeline Overview** — cards for Open Pipeline Value / Win Rate / Stale
  Opportunities / Avg Deal Age; bar chart of pipeline value by stage; line
  chart of opportunities created by month (from `dim_date`).
- **Pipeline Hygiene** — table of stale opportunities (account, rep, days
  since activity, amount) sorted descending; stale % trend by month.
- **Rep / Region Performance** — win rate by rep, pipeline value by region,
  deals closed by team.
- **Data Quality Scorecard** — DUNS completeness by industry, a callout of
  duplicate accounts merged, non-standard stage values normalized.

The Power BI report is built from the five clean tables above and uses a
star-schema model with `fact_opportunities` at its center. The dashboard is
designed for sales operations reporting, pipeline inspection, rep performance
analysis, and CRM data-quality follow-up.

## Verified dashboard results

The completed report was validated against the Python-generated quality report:

| KPI | Result |
|---|---:|
| Open pipeline value | $10,241,900 |
| Win rate | 66.7% |
| Stale opportunities | 201 |
| Stale percent of open pipeline | 33.3% |
| Average deal age | 213.95 days |
| Accounts before cleaning | 162 |
| Duplicate accounts merged | 25 |
| Deduplication precision | 84.6% |
| Deduplication recall | 100.0% |
| Accounts after cleaning | 137 |
| Missing amounts imputed | 33 |

The CRM data is synthetic and seeded for reproducibility. It is modeled after
typical Dynamics or Salesforce exports and does not represent real company or
client data.

The generator includes a ground-truth account-company key solely for evaluating
the cleaner. The original v1 name-only matcher recovered all injected
duplicate pairs but also produced false-positive merges, yielding 84.6% pair
precision. That baseline result remains documented for comparison.

On the v2 branch, duplicate records retain the original company's country and
industry. Country-blocked matching now achieves 100.0% pair precision and
100.0% pair recall, merging the 22 injected duplicate records into 140 clean
accounts. The v2 seeded outputs currently contain 605 open opportunities, 200
stale opportunities, a 67.5% closed-deal win rate, and $10,141,700 of open
pipeline. These v2 values intentionally differ from the original v1 dashboard
baseline because the generator is now more realistic and auditable.

## v2 analytical upgrades

The upgraded pipeline separates open opportunity age from closed-deal sales
cycle, makes the as-of date and stale threshold configurable, and reports
stale pipeline by value as well as by count. It also preserves imputation-aware
pipeline value and writes an account merge map plus row-level validation issues.
The validation summary reports zero-count rules as explicit `PASS` results and
flags issues requiring operational review.

The `sql/` layer uses DuckDB to answer business questions about stage funnel
conversion, rep performance, monthly pipeline trends, aging buckets, and stale
deal prioritization. These queries run directly against the clean CSV outputs.

**5. Publish / screenshot**
Export a couple of pages as images or PDF for your portfolio/GitHub README
once built — that's what you'll actually reference in the interview.

## Reproduce from scratch
```
pip install pandas numpy faker
python generate_data.py
python clean_data.py
```
