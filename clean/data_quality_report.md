# CRM Data Quality & Cleaning Report

## De-duplication
- Accounts before cleaning: **162**
- Duplicate account records merged: **22**
- Accounts after cleaning: **140**
- Duplicate pair precision against generator ground truth: **100.0%**
- Duplicate pair recall against generator ground truth: **100.0%**

## Missing required fields (DUNS number)
- Missing before cleanup: **37.7%** of accounts
- Missing after cleanup (still unresolved, flagged for outreach): **27.9%** of accounts
  → `duns_missing_flag = True` in `dim_accounts.csv` for seller follow-up.

## Non-standard field values
- Raw stage values found: **21** distinct strings
  (e.g. "closed-won", "Won", "CLOSED WON" all mapped to one canonical stage)
- Standardized down to **6** canonical stages

## Pipeline hygiene
- Open opportunities: **605**
- Stale opportunities (open, no activity in 30+ days): **200**
  (33.1% of open pipeline — flagged for rep follow-up)
- Total open pipeline value: **$10,141,700**
- Open pipeline value excluding imputed amounts: **$9,833,800**
- Stale pipeline value: **$3,327,550** (32.8% of open pipeline value)
- Overall win rate (closed deals): **67.5%**

## Missing amounts
- Opportunities with missing deal amount, imputed with product-level median: **33**
