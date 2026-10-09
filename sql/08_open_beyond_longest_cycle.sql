-- Business question: how many open deals are already older than the longest time
-- any deal has ever taken to close? Those need a close-out decision, and many of
-- them are NOT caught by the 30-day "stale" rule because they still log activity.
WITH ref AS (
    SELECT MAX(sales_cycle_days) AS longest_closed_cycle_days
    FROM read_csv_auto('clean/fact_opportunities.csv')
    WHERE is_closed
),
open_deals AS (
    SELECT f.*, ref.longest_closed_cycle_days
    FROM read_csv_auto('clean/fact_opportunities.csv') f, ref
    WHERE NOT f.is_closed
)
SELECT
    MAX(longest_closed_cycle_days) AS longest_closed_cycle_days,
    COUNT(*) AS total_open_opportunities,
    COUNT(*) FILTER (WHERE open_age_days > longest_closed_cycle_days) AS open_beyond_cycle,
    ROUND(100.0 * COUNT(*) FILTER (WHERE open_age_days > longest_closed_cycle_days) / COUNT(*), 1) AS open_beyond_cycle_pct,
    ROUND(SUM(CASE WHEN open_age_days > longest_closed_cycle_days THEN amount ELSE 0 END), 0) AS value_beyond_cycle,
    COUNT(*) FILTER (WHERE open_age_days > longest_closed_cycle_days AND NOT is_stale) AS beyond_cycle_but_not_stale
FROM open_deals;
