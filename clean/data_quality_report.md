# CRM Data Quality & Cleaning Report

## De-duplication
- Accounts before cleaning: **162**
- Duplicate account records merged: **25**
- Accounts after cleaning: **137**

## Missing required fields (DUNS number)
- Missing before cleanup: **37.7%** of accounts
- Missing after cleanup (still unresolved, flagged for outreach): **28.5%** of accounts
  → `duns_missing_flag = True` in `dim_accounts.csv` for seller follow-up.

## Non-standard field values
- Raw stage values found: **21** distinct strings
  (e.g. "closed-won", "Won", "CLOSED WON" all mapped to one canonical stage)
- Standardized down to **6** canonical stages

## Pipeline hygiene
- Open opportunities: **603**
- Stale opportunities (open, no activity in 30+ days): **201**
  (33.3% of open pipeline — flagged for rep follow-up)
- Total open pipeline value: **$10,241,900**
- Open pipeline value excluding imputed amounts: **$9,934,500**
- Stale pipeline value: **$3,566,900** (34.8% of open pipeline value)
- Overall win rate (closed deals): **66.7%**

## Missing amounts
- Opportunities with missing deal amount, imputed with product-level median: **33**
