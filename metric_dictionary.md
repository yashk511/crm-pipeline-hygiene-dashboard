# Metric Dictionary

| Metric | Definition | Grain | Caveat |
|---|---|---|---|
| Open Pipeline Value | Sum of `amount` for open opportunities | Opportunity | Includes imputed amounts |
| Open Pipeline Excluding Imputed | Same, excluding deals whose amount was missing and imputed | Opportunity | Gap vs Open Pipeline Value = pipeline resting on imputed amounts |
| Stale Opportunities | Open deals with more than 30 days since last activity | Opportunity | As-of date set by `CRM_AS_OF_DATE`; threshold by `CRM_STALE_THRESHOLD_DAYS` |
| Stale Pipeline Value | `amount` of stale open deals | Opportunity | Includes imputed amounts |
| Stale Value Percent | Stale Pipeline Value / Open Pipeline Value | Portfolio | Value-based. The count-based share is reported separately |
| Win Rate | Closed-won / all closed | Opportunity | Synthetic data; not a forecast. Always read next to closed-deal count |
| Open Age (days) | As-of date minus created date | Open opportunities only | Blank for closed deals by design |
| Sales Cycle (days) | Close date minus created date | Closed opportunities only | Blank for open deals by design |
| Beyond Longest Cycle | Open deals older than the longest closed sales cycle | Open opportunities | Catches over-aged deals that still log activity and so escape the stale rule |
| Stage Progression (progressed to date) | Share of deals that reached a stage and later reached the next | Opportunity | Right-censored: open deals that have not moved count as not progressed |
| DUNS Completeness | Accounts with a DUNS number / cleaned accounts | Account | Missing values stay unresolved and flagged |
| Missing Lead Source | Opportunities with no lead source (shown as "Unknown") | Opportunity | Data-quality issue; those deals also win less often |

Retired: `deal_age_days` (blended open age and sales cycle) and `expected_win_probability`
(generator ground truth, kept out of the model to prevent leakage).
