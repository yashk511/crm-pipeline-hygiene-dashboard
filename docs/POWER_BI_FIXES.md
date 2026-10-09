# Power BI fixes for the CRM dashboard (do in this order)

Back up your `.pbix` first and save the edited copy as `..._v3.pbix`.
**Do not click Refresh until Step 1 is done**, because two fields are removed from the data.

## What each fix repairs
| # | Problem found in v2 | Fix |
|---|---|---|
| 1 | Funnel and stage visuals are not chronological (final `Stage_Order` step maps Qualification=1 ... Negotiation=6) | Data now ships a correct `stage_order`; sort `stage` by it |
| 2 | Data Quality matrix "Stale Deals" column is a copy of Missing Amounts (34/34; true stale total is 183) | Replace with measures |
| 3 | "Average Open Age Days" showed 269 because closed deals were included; true value is 264 | `open_age_days` is now blank for closed deals |
| 4 | Funnel page sums amount by current stage and ignores `opportunity_stage_history` | Use stage history + the stage-progression mart |
| 5 | Bar chart uses the retired blended `deal_age_days` | Replace with open age by stage |
| 6 | Hard-coded `D:\chrome downloads\...` paths | One `DataFolder` parameter |
| 7 | Mixed boolean/integer filters in DAX (`= FALSE()` vs `= 1`) | All measures use `TRUE()/FALSE()` |
| 8 | Auto date/time on (5 hidden date tables) | Turn off, mark `dim_date` as date table |
| 9 | `$` with Indian digit grouping; PDF shows Power BI toolbar | Format strings + File > Export > PDF |

## Step 1: Replace data and fix visuals that use removed columns
1. Copy the new `clean/` folder over your old one (it now includes `sql_marts/`).
2. Page "Funnel & Stage Conversions": delete the bar chart "Sum of deal age days" (uses removed `deal_age_days`). You will rebuild it in Step 5.

## Step 2: Power Query
**Home > Transform data > Manage parameters > New**: Name `DataFolder`, Type Text,
Current value = full path to your `clean` folder **ending with a backslash**, e.g. `C:\Users\you\crm\clean\`.

For `dim_accounts`, `dim_reps`, `dim_date`, `quality_metrics`, `validation_summary`: open Advanced Editor and change only the Source line, e.g.
```
Source = Csv.Document(File.Contents(DataFolder & "dim_accounts.csv"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
```
(`Encoding=65001` is UTF-8; keep the other steps and the column counts: accounts 9, reps 4, date 5, quality_metrics 2, validation_summary 4.)

**fact_opportunities**: replace the whole query (this deletes every `Stage_Order`/`Custom` step):
```
let
    Source = Csv.Document(File.Contents(DataFolder & "fact_opportunities.csv"),[Delimiter=",", Columns=20, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Promoted,{
        {"opp_id", type text}, {"account_id", type text}, {"rep_id", type text},
        {"product", type text}, {"lead_source", type text}, {"stage", type text},
        {"amount", type number}, {"created_date", type date}, {"close_date", type date},
        {"last_activity_date", type date}, {"days_since_activity", Int64.Type},
        {"open_age_days", Int64.Type}, {"sales_cycle_days", Int64.Type},
        {"is_closed", type logical}, {"is_won", type logical}, {"is_stale", type logical},
        {"amount_missing_flag", type logical}, {"lead_source_missing_flag", type logical},
        {"beyond_max_cycle_flag", type logical}, {"stage_order", Int64.Type}})
in
    Typed
```
**opportunity_stage_history**: same pattern, `Columns=5`, types: `opp_id` text, `stage` text, `stage_order` Int64, `stage_sequence` Int64, `stage_date` date.

**Two new queries** (Get Data > Text/CSV, then edit Source the same way):
- `stage_progression` from `DataFolder & "sql_marts\06_stage_progression.csv"` (7 columns; `from_order`, `to_order`, `opportunities_progressed`, `opportunities_at_start` Int64, `progressed_to_date_pct` number)
- `segment_win_rate` from `DataFolder & "sql_marts\07_win_rate_by_segment.csv"` (7 columns; `closed_deals`, `won_deals` Int64; the three percentage columns number)

Close & Apply.

## Step 3: Model view
- **Sort by column** (Column tools): `fact_opportunities[stage]` by `stage_order`; `opportunity_stage_history[stage]` by `stage_order`; `stage_progression[from_stage]` by `from_order`; `stage_progression[to_stage]` by `to_order`.
- Hide the `*_order` columns.
- Relationships stay as they are. `stage_progression` and `segment_win_rate` stay unrelated (they are pre-aggregated marts).
- **File > Options > Current File > Data Load**: untick *Auto date/time*. Then select `dim_date` > Table tools > *Mark as date table* using `date`.

## Step 4: Measures (replace or create; use these exact definitions)
```
Open Opportunities = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_closed] = FALSE())
Open Pipeline Value = CALCULATE(SUM(fact_opportunities[amount]), fact_opportunities[is_closed] = FALSE())
Open Pipeline Excluding Imputed =
    CALCULATE(SUM(fact_opportunities[amount]), fact_opportunities[is_closed] = FALSE(),
              fact_opportunities[amount_missing_flag] = FALSE())
Imputed Pipeline Value = [Open Pipeline Value] - [Open Pipeline Excluding Imputed]
Stale Opportunities = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_stale] = TRUE())
Stale Pipeline Value = CALCULATE(SUM(fact_opportunities[amount]), fact_opportunities[is_stale] = TRUE())
Stale Value Percent = DIVIDE([Stale Pipeline Value], [Open Pipeline Value])
Stale Count Percent = DIVIDE([Stale Opportunities], [Open Opportunities])
Closed Deals = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_closed] = TRUE())
Won Deals = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[is_won] = TRUE())
Win Rate = DIVIDE([Won Deals], [Closed Deals])
Average Open Age Days = AVERAGE(fact_opportunities[open_age_days])
Average Sales Cycle Days = AVERAGE(fact_opportunities[sales_cycle_days])
Missing Amount Deals = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[amount_missing_flag] = TRUE())
Missing Lead Source Deals = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[lead_source_missing_flag] = TRUE())
Beyond Longest Cycle = CALCULATE(COUNTROWS(fact_opportunities), fact_opportunities[beyond_max_cycle_flag] = TRUE())
Opps Reaching Stage = DISTINCTCOUNT(opportunity_stage_history[opp_id])
```
Format strings (Measure tools > Format > Custom): currency measures `$#,0`; percent measures `0.0%`; day measures `0`.
This also fixes the Indian digit grouping.

## Step 5: Page fixes
**Executive Pipeline Summary**: re-point cards to the measures above. Stage bar chart: use open stages only (visual filter `is_closed` = False), axis sorted by `stage_order` ascending (Prospecting first).

**Pipeline Hygiene**: replace the collapsed table with a flat table: `account_name`, `rep_name`, `region`, `stage`, `days_since_activity`, `amount`; visual filter `is_stale` = True; sort `days_since_activity` descending. Keep the two cards and the team slicer.

**Rep & Regional Performance**: on the win-rate bar chart add `Closed Deals` to Tooltips and a visual filter `Closed Deals` >= 10; title it "Win rate (reps with 10+ closed deals)".

**Funnel & Stage Progression** (rename the page):
1. Funnel: `opportunity_stage_history[stage]` by `Opps Reaching Stage`; filter `stage_order` <= 4 (Closed Won and Closed Lost are branches, not funnel steps).
2. Table or bar: `stage_progression` with `from_stage`, `to_stage`, `progressed_to_date_pct` (sorted by from_order). Add a text note: "Progressed to date; open deals count as not progressed yet."
3. Replace the deleted chart: `fact_opportunities[stage]` by `Average Open Age Days` (open stages only), title "Average age of open deals by stage".
4. Replace the donut with a clustered bar: `segment_win_rate[segment]` by `win_rate_pct`, filter `dimension` = lead_source, tooltips `closed_deals`, `ci95_low_pct`, `ci95_high_pct`. (Optional: Analytics pane > Error bars using the two CI columns.)

**Data Quality Scorecard**: matrix rows `rep_name`; values `Missing Amount Deals`, `Stale Opportunities`, `Missing Lead Source Deals`; **remove the visual-level filter** on `amount_missing_flag`. Add a table from `validation_summary` (`issue_type`, `severity`, `issue_count`, `status`) with conditional formatting on `status` (PASS green, REVIEW amber). Add cards from `quality_metrics` for dedup precision and recall.

## Step 6: Check these totals after refresh
| Visual | Expected |
|---|---|
| Open Pipeline Value / Excluding Imputed | $11,277,500 / $10,964,300 |
| Stale Opportunities / Stale Pipeline Value | 183 / $3,756,350 (33.3%) |
| Win Rate / Closed Deals | 47.1% / 310 |
| Average Open Age / Average Sales Cycle | 264 / 87.5 days |
| Missing Amount Deals / Missing Lead Source Deals | 34 / 171 |
| Beyond Longest Cycle | 378 |
| Funnel order | Prospecting, Qualification, Proposal, Negotiation |
| DQ matrix totals | 34, 183, 171 (no longer identical) |

## Step 7: Export
**File > Export > Export to PDF** (not Print or screenshot) so the Power BI toolbar is not captured.
Put the PDF in `docs/` and update the README link.
