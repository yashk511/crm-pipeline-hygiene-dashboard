-- Business question: do win rates differ by lead source or product, and is the gap
-- larger than sampling noise? Wilson 95% interval shown for each segment.
-- (Synthetic data: gaps reflect planted simulation parameters, not business evidence.)
WITH base AS (
    SELECT 'lead_source' AS dimension, lead_source AS segment,
           COUNT(*) AS closed_deals,
           SUM(CASE WHEN is_won THEN 1 ELSE 0 END) AS won_deals
    FROM read_csv_auto('clean/fact_opportunities.csv')
    WHERE is_closed
    GROUP BY lead_source
    UNION ALL
    SELECT 'product', product, COUNT(*), SUM(CASE WHEN is_won THEN 1 ELSE 0 END)
    FROM read_csv_auto('clean/fact_opportunities.csv')
    WHERE is_closed
    GROUP BY product
),
calc AS (
    SELECT *, won_deals * 1.0 / closed_deals AS p, 1.96 AS z FROM base
)
SELECT
    dimension,
    segment,
    closed_deals,
    won_deals,
    ROUND(100 * p, 1) AS win_rate_pct,
    ROUND(100 * (p + z*z/(2*closed_deals) - z*SQRT(p*(1-p)/closed_deals + z*z/(4.0*closed_deals*closed_deals)))
          / (1 + z*z/closed_deals), 1) AS ci95_low_pct,
    ROUND(100 * (p + z*z/(2*closed_deals) + z*SQRT(p*(1-p)/closed_deals + z*z/(4.0*closed_deals*closed_deals)))
          / (1 + z*z/closed_deals), 1) AS ci95_high_pct
FROM calc
ORDER BY dimension, win_rate_pct DESC;
