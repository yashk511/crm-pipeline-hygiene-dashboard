# CRM Pipeline & Data Quality Dashboard

An audit-first sales-ops project. A deliberately messy, **synthetic** CRM export (Dynamics /
Salesforce style) is deduplicated, validated, and modeled in Python and SQL before any
visual is built. The Power BI report shows pipeline with and without dirty records, so every
number traces to a rule in this repo.

> **Data is synthetic and seeded** (`generate_data.py`). Lead-source, product, and team
> effects are planted simulation parameters, not real-world evidence.


## What was cleaned and audited

| Problem | Approach | Result |
|---|---|---|
| Duplicate accounts | Name normalization + fuzzy match, blocked by country | 162 -> 140 accounts; 100% pair precision and recall vs ground truth |
| Non-standard stage values | Rule-based mapping | 21 raw spellings -> 6 stages, in chronological order |
| Missing deal amounts | Flagged, median-imputed, reported separately | 34 flagged; open pipeline $10.96M excluding imputed vs $11.28M |
| Missing DUNS numbers | Flagged, never invented | 39 accounts routed for follow-up |
| Missing lead source | Flagged, shown as "Unknown" | 171 of 900 opportunities |
| Stale pipeline | Open, no activity in 30+ days | 183 deals, $3.76M (33.3% of open value) |
| Over-aged pipeline | Open deals older than the longest closed cycle (180 days) | 378 of 590 open deals; 242 are not caught by the stale rule |
| Validation | 10 row-level rules with a PASS/REVIEW summary | 7 PASS, 3 REVIEW |

The first matcher compared names only and reached 84.6% pair precision (false merges across
countries). Blocking by country raised it to 100%. Variants in the synthetic data are easy
(case, suffixes, spacing), so treat 100% as "correct on injected defects", not a general claim.

## Pipeline

```
generate_data.py -> raw/ -> clean_data.py -> clean/ (star schema) -> run_sql.py -> clean/sql_marts/
                                                   |                        |
                                              Power BI model        build_analysis.py -> analysis/
```

## Repository layout

```
raw/        messy source export (+ generator-only ground-truth labels, never used by analysis)
clean/      star schema, merge audit map, issue log, validation summary, stage history
sql/        8 DuckDB queries (window functions, CTEs, Wilson intervals)
analysis/   business_analysis.md, generated from the marts
tests/      11 logic tests
docs/       dashboard PDF and screenshots
```

## Dashboard (5 pages)
Executive Pipeline Summary - Pipeline Hygiene - Rep & Regional Performance -
Funnel & Stage Progression - Data Quality Scorecard. Metric definitions are in
`metric_dictionary.md`.

## Run it

```bash
pip install -r requirements.txt
python run_all.py     # generate -> clean -> SQL marts -> analysis -> tests
```

Power BI: open the `.pbix`, set the `DataFolder` parameter to your local `clean/` path, refresh.

## Limitations
- Synthetic data and generated stage history; findings demonstrate method, not business truth.
- Stage progression is right-censored (open deals count as not progressed yet).
- Win-rate gaps by lead source are planted; the product gap is within sampling noise.
