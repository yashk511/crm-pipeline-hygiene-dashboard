-- Business question: which stale opportunities should sales operations prioritize?
SELECT
    o.opp_id,
    a.account_name,
    r.rep_name,
    r.region,
    o.stage,
    o.amount,
    o.days_since_activity,
    ROUND(o.amount * o.days_since_activity, 0) AS stale_priority_score
FROM read_csv_auto('clean/fact_opportunities.csv') o
JOIN read_csv_auto('clean/dim_accounts.csv') a USING (account_id)
JOIN read_csv_auto('clean/dim_reps.csv') r USING (rep_id)
WHERE o.is_stale = TRUE
ORDER BY stale_priority_score DESC;
