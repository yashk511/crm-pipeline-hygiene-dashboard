# CRM Pipeline Intelligence
**[Live dashboard](https://crm-pipeline-intelligence.streamlit.app)**

An audit-first sales-operations project. A deliberately messy, **synthetic** CRM export
(Dynamics / Salesforce style) is cleaned, validated and modeled in Python and SQL before any
chart is drawn. The dashboard reports pipeline with and without dirty records, so every
number traces back to a rule in this repo.

> **Data is synthetic and seeded** (`generate_data.py`). Lead-source, product and team effects
> are planted simulation parameters, not real-world evidence. The project demonstrates the
> method: cleaning, validation, SQL analysis, testing and reporting.

## What was cleaned and audited

| Problem | Approach | Result |
|---|---|---|
| Duplicate accounts | Name normalization (case, spacing, punctuation, legal suffixes) + country-blocked matching, fuzzy fallback and review band | 162 -> 140 accounts; 100% pair precision and recall vs ground truth |
| Non-standard stage values | Rule-based mapping | 21 raw spellings -> 6 stages, in chronological order |
| Missing deal amounts | Flagged, median-imputed, reported separately | 34 flagged; open pipeline $10.96M excluding imputed vs $11.28M |
| Missing DUNS numbers | Flagged, never invented | 37.7% -> 27.9% missing after cleanup; remainder routed for follow-up |
| Missing lead source | Flagged, shown as "Unknown" | 171 of 900 opportunities |
| Stale pipeline | Open, no activity in 30+ days | 183 deals, $3.76M (33.3% of open value) |
| Over-aged pipeline | Open deals older than the longest closed cycle (180 days) | 378 of 590 open deals; 242 are not caught by the stale rule |
| Validation | 10 row-level rules with a PASS/REVIEW summary | 7 PASS, 3 REVIEW |

**On deduplication:** an earlier name-only matcher reached 84.6% pair precision (false merges
across countries). Blocking by country raised it to 100%. All 22 duplicates in the synthetic data
are easy variants, and every merge was exact after normalization, so the fuzzy fallback was not
needed. Treat 100% as "correct on the injected defects", not a general guarantee.

## Dashboard

A Streamlit app (`app.py`) reads the cleaned tables and recomputes every figure; tests check it
against the SQL marts.

- **Executive:** KPI cards, open pipeline by stage (chronological), by month created, by region, team mix
- **Pipeline hygiene:** aging buckets, stale value by region, ranked stale-deal follow-up queue (CSV download)
- **Reps & regions:** win rate with 95% Wilson intervals and sample sizes, pipeline treemap, rep scorecard
- **Funnel & segments:** stage funnel and progression to date, win rate by lead source and product
- **Data quality:** dedup results, 10 validation rules, issues by rep, DUNS completeness by industry, merge audit trail
- **About:** method notes and the metric dictionary

Sidebar filters: region, team, product, lead source.

## Pipeline

```
generate_data.py -> raw/ -> clean_data.py -> clean/ (star schema) -> run_sql.py -> clean/sql_marts/
                                                  |                                    |
                                            app.py (Streamlit)                build_analysis.py -> analysis/
```

## Repository layout

```
raw/           messy source export (+ generator-only ground-truth labels, never used by the analysis)
clean/         star schema, merge audit map, issue log, validation summary, stage history
clean/sql_marts/   8 DuckDB result tables
sql/           8 DuckDB queries (window functions, CTEs, Wilson intervals)
analysis/      business_analysis.md, generated from the marts
dashboard/     data loading, pure-pandas metric functions, theme
tests/         22 tests (pipeline logic + dashboard-vs-SQL checks)
docs/          Power BI and Streamlit deployment notes
app.py         Streamlit dashboard
```

A Power BI version of the report (`.pbix`) is included and is being refreshed to match the
Streamlit app. Metric definitions are in `metric_dictionary.md`.

## Run it

```bash
pip install -r requirements.txt
python run_all.py        # generate -> clean -> SQL marts -> analysis -> tests (22 expected)
streamlit run app.py     # http://localhost:8501
```

## Limitations
- Synthetic data and generated stage history; findings demonstrate method, not business truth.
- Stage progression is right-censored: open deals that have not moved count as not progressed yet.
- Win-rate gaps by lead source are planted; the product gap is within sampling noise.
- Rep-level samples are small (12-26 closed deals each), so wide intervals are expected.
