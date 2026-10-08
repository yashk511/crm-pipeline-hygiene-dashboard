# Metric Dictionary

| Metric | Definition | Grain | Caveat |
|---|---|---|---|
| Open Pipeline Value | Sum of amount for opportunities that are not closed | Opportunity | Includes imputed amounts unless the excluding-imputed metric is used |
| Stale Opportunities | Open opportunities with more than 30 days since last activity | Opportunity | As-of date is configurable with `CRM_AS_OF_DATE` |
| Stale Pipeline Value | Amount represented by stale open opportunities | Opportunity | Includes imputed amounts |
| Win Rate | Closed-won opportunities divided by all closed opportunities | Opportunity | Synthetic data; not a forecast |
| Open Age | As-of date minus created date for open opportunities | Opportunity | Applies only to open opportunities |
| Sales Cycle | Close date minus created date for closed opportunities | Opportunity | Applies only to closed opportunities |
| DUNS Completeness | Accounts with a DUNS number divided by cleaned accounts | Account | Missing DUNS values remain unresolved and flagged |
