# CRM Pipeline Analysis

## Scope and caveat

This analysis uses the signal-aware v2 synthetic CRM dataset as of September 1,
2026. The results are descriptive operational findings, not causal claims or a
forecast. The generator now plants modest effects by lead source, product, and
team so the analysis workflow can be demonstrated, but those effects are
simulation parameters rather than real-world evidence.

## Findings

### 1. Aging is the largest immediate pipeline risk

Open opportunities aged 180+ days represent the largest aging bucket and should
be the first operational review population. Use the current `04_aging_buckets`
mart for the exact v2 amount and count rather than treating age as a forecast.

### 2. Stale follow-up should be value-prioritized

The stale-deal priority mart ranks opportunities using the transparent triage
score `amount * days_since_activity`. The highest-ranked examples are:

- Brown Valdez and Lucas: $52,400, 508 days since activity
- Robinson-Brock: $67,500, 262 days since activity
- Simmons Meadows and Griffin: $43,400, 406 days since activity
- Powell LLC: $45,800, 375 days since activity
- Rodriguez Brennan and Garrison: $42,100, 392 days since activity

This score is a prioritization heuristic, not a probability of recovery. Sales
operations should confirm deal status before treating the value as recoverable.

### 3. Rep results should be reviewed with volume context

Michele Williams ranks first in open pipeline value at **$774,400** with a
47.4% observed win rate across 19 closed opportunities. Daniel Wagner has the
highest observed win rate at **86.7%**, based on 15 closed opportunities and
$681,900 open pipeline. These are useful review signals, not performance
causality; the sample sizes and synthetic assignment process limit conclusions.

### 4. Opportunity creation was highest in late summer 2025

Use the monthly trend mart to monitor creation volume and open pipeline over
time. This supports a monthly pipeline review cadence, but does not establish
a seasonal sales pattern from one synthetic period.

### 5. Simulated driver analysis is now possible, with labels

In the seeded simulation, observed closed-deal win rates differ by lead source
and product: Referral is 67.3% versus 22.2% for ZoomInfo List, while Platform
License is 54.9% versus 40.7% for Support Add-on. These are useful for testing
segmentation, confidence intervals, and regression code, but must be presented
as planted-signal demonstrations rather than business conclusions.

## Recommended operating actions

1. Create a weekly aging review for all opportunities older than 180 days,
   starting with the highest-value deals.
2. Use the stale-priority mart as a seller follow-up queue, but require a
   status confirmation before forecasting recovery.
3. Review rep performance with closed-deal volume, pipeline mix, and deal age
   together; do not rank reps on win rate alone.
4. Resolve the 33 amount issues, 39 missing-DUNS issues, and one
   close-before-create issue through CRM hygiene workflows.
5. Use the event-based stage transition mart for funnel reporting: the current
   v2 run shows 83.4% Prospecting-to-Qualification, 76.6%
   Qualification-to-Proposal, 71.5% Proposal-to-Negotiation, then 35.5% won
   and 39.9% lost from Negotiation.

## Next analytical upgrade

Add realistic planted effects and opportunity history before claiming drivers
of win rate, forecasting pipeline movement, or estimating conversion by stage.
Then extend this report with confidence intervals, cohort analysis, and a
forecasting section.
