# CRM Pipeline Analysis

## Scope and caveat

This analysis uses the v2 synthetic CRM dataset as of September 1, 2026. The
results are descriptive operational findings, not causal claims or a forecast.
The generator does not yet plant realistic win-rate drivers, so segment
comparisons should not be interpreted as evidence that a product, rep, team, or
region causes higher conversion.

## Findings

### 1. Aging is the largest immediate pipeline risk

Open opportunities aged 180+ days represent **395 opportunities** and
**$6,273,000** of pipeline, approximately **61.8%** of total open pipeline
value ($10,141,700). The 90+ day population represents $8,435,600, or about
83.1% of open pipeline value.

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

August 2025 had the highest creation volume at **71 opportunities** and
$762,500 of open pipeline. April and May 2026 also show elevated creation
volume at 63 and 64 opportunities. This supports a monthly pipeline review
cadence, but does not establish a seasonal sales pattern.

## Recommended operating actions

1. Create a weekly aging review for all opportunities older than 180 days,
   starting with the highest-value deals.
2. Use the stale-priority mart as a seller follow-up queue, but require a
   status confirmation before forecasting recovery.
3. Review rep performance with closed-deal volume, pipeline mix, and deal age
   together; do not rank reps on win rate alone.
4. Resolve the 33 amount issues, 39 missing-DUNS issues, and one
   close-before-create issue through CRM hygiene workflows.
5. Treat the current funnel chart as stage distribution, not true
   stage-to-stage conversion, until the generator includes opportunity-stage
   history or transition events.

## Next analytical upgrade

Add realistic planted effects and opportunity history before claiming drivers
of win rate, forecasting pipeline movement, or estimating conversion by stage.
Then extend this report with confidence intervals, cohort analysis, and a
forecasting section.
