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
- Open opportunities: **590**
- Stale opportunities (open, no activity in 30+ days): **183**
  (31.0% of open pipeline — flagged for rep follow-up)
- Total open pipeline value: **$11,277,500**
- Open pipeline value excluding imputed amounts: **$10,964,300**
- Stale pipeline value: **$3,756,350** (33.3% of open pipeline value)
- Overall win rate (closed deals): **47.1%**

## Over-aged pipeline
- Longest sales cycle among closed deals: **180 days**
- Open opportunities older than that: **378** (candidates for close-out review)

## Missing lead source
- Opportunities with no lead source (reported as "Unknown"): **171**

## Missing amounts
- Opportunities with missing deal amount, imputed with product-level median: **34**
