"""CRM Pipeline Intelligence: Streamlit dashboard over the cleaned CRM tables.

Run locally:  streamlit run app.py
Data comes from clean/ (built by `python run_all.py`), so nothing here is hand-typed.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard import metrics as m  # noqa: E402
from dashboard import theme as t  # noqa: E402
from dashboard.data import AS_OF, GITHUB_URL, load_all  # noqa: E402

st.set_page_config(
    page_title="CRM Pipeline Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(t.CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load() -> dict:
    return load_all()


data = load()
full = data["fact"]
history = data["history"]
quality = data["quality"]
longest_cycle = int(full.loc[full["is_closed"], "sales_cycle_days"].max())


# ---------- small UI helpers ----------
def kpi(label: str, value: str, sub: str = "", tone: str = "") -> str:
    return (
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-sub {tone}">{sub}</div></div>'
    )


def section(title: str, sub: str = "") -> None:
    html = f'<div class="sec">{title}</div>'
    if sub:
        html += f'<div class="sec-sub">{sub}</div>'
    st.markdown(html, unsafe_allow_html=True)


def insight(text: str, tone: str = "") -> None:
    st.markdown(f'<div class="insight {tone}">{text}</div>', unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=key)


def days(x: float) -> str:
    return "-" if pd.isna(x) else f"{x:.0f} d"


def cards(items: list[tuple]) -> None:
    cols = st.columns(len(items), gap="small")
    for col, (label, value, sub, tone) in zip(cols, items):
        col.markdown(kpi(label, value, sub, tone), unsafe_allow_html=True)


def winrate_chart(df: pd.DataFrame, label_col: str, key: str, overall: float, height: int) -> None:
    if df.empty:
        st.info("No closed deals for the current filters.")
        return
    d = df.sort_values("win_rate")
    labels = [f"{a}  (n={n})" for a, n in zip(d[label_col], d["closed_deals"])]
    colors = [
        t.AMBER if str(a) == "Unknown" else (t.TEAL if w >= overall else t.BLUE)
        for a, w in zip(d[label_col], d["win_rate"])
    ]
    fig = go.Figure(
        go.Bar(
            x=(d["win_rate"] * 100).tolist(),
            y=labels,
            orientation="h",
            marker_color=colors,
            error_x=dict(
                type="data",
                symmetric=False,
                array=((d["ci_high"] - d["win_rate"]) * 100).tolist(),
                arrayminus=((d["win_rate"] - d["ci_low"]) * 100).tolist(),
                color=t.MUTED,
                thickness=1.2,
                width=3,
            ),
            hovertemplate="%{y}<br>win rate %{x:.1f}%<extra></extra>",
        )
    )
    if pd.notna(overall):
        fig.add_vline(
            x=overall * 100, line_dash="dot", line_color=t.AMBER,
            annotation_text=f"overall {overall * 100:.1f}%", annotation_position="top",
            annotation_font_color=t.AMBER,
        )
    fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=True, gridcolor=t.GRID)
    fig.update_yaxes(showgrid=False)
    t.style(fig, height)
    fig.update_layout(margin=dict(l=4, r=8, t=34, b=4))
    show(fig, key)


# ---------- sidebar filters ----------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-badge">📈</div><div>'
        '<div class="brand-text">CRM Pipeline<br>Intelligence</div>'
        '<div class="brand-sub">Sales operations analytics</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("**Filters**")

    def pick(label: str, col: str) -> list:
        return st.multiselect(label, sorted(full[col].dropna().unique()), placeholder="All")

    sel_region = pick("Region", "region")
    sel_team = pick("Team", "team")
    sel_product = pick("Product", "product")
    sel_source = pick("Lead source", "lead_source")
    note("Filters apply to every tab except the account-level cleaning statistics.")

mask = pd.Series(True, index=full.index)
for column, chosen in (
    ("region", sel_region), ("team", sel_team),
    ("product", sel_product), ("lead_source", sel_source),
):
    if chosen:
        mask &= full[column].isin(chosen)
f = full[mask]

if f.empty:
    st.warning("No opportunities match these filters. Clear a filter to continue.")
    st.stop()

k = m.kpis(f)

# ---------- hero ----------
st.markdown(
    f"""
<div class="hero">
  <div>
    <div class="eyebrow">Sales operations</div>
    <h1>CRM Pipeline Intelligence</h1>
    <p>Pipeline health, stale-deal follow-up and CRM data quality, audited end to end.</p>
  </div>
  <div class="chips">
    <span class="chip warn">Synthetic data</span>
    <span class="chip">As of {AS_OF}</span>
    <span class="chip">{len(f):,} of {len(full):,} opportunities</span>
    <span class="chip"><a href="{GITHUB_URL}" target="_blank">GitHub repo</a></span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tabs = st.tabs(["Executive", "Pipeline hygiene", "Reps & regions", "Funnel & segments", "Data quality", "About"])

# =====================================================================
# 1. EXECUTIVE
# =====================================================================
with tabs[0]:
    imputed_gap = k["open_value"] - k["open_value_excl_imputed"]
    cards([
        ("Open pipeline", m.money(k["open_value"]), f"{k['open_count']:,} open deals", ""),
        ("Excl. imputed", m.money(k["open_value_excl_imputed"]),
         f"{m.money(imputed_gap)} rests on imputed amounts", "warn"),
        ("Stale value", m.money(k["stale_value"]),
         f"{m.pct(k['stale_value_pct'])} of open · {k['stale_count']} deals", "bad"),
        ("Win rate", m.pct(k["win_rate"]), f"{k['won_count']} won of {k['closed_count']} closed", "good"),
        ("Avg open age", days(k["avg_open_age"]), "open deals only", ""),
        ("Avg sales cycle", days(k["avg_sales_cycle"]), "closed deals only", ""),
    ])
    insight(
        f"<b>{k['stale_count']} open deals ({m.money(k['stale_value'])})</b> have been quiet for 30+ days, "
        f"and <b>{k['beyond_cycle']}</b> open deals are older than the longest deal ever closed "
        f"({longest_cycle} days)."
    )

    left, right = st.columns(2, gap="medium")
    open_f = f[~f["is_closed"]]
    with left, st.container(border=True):
        section("Open pipeline by stage", "Chronological order, current snapshot")
        stage = (
            open_f.groupby("stage")["amount"].sum().reindex(m.OPEN_STAGES).fillna(0).reset_index()
        )
        fig = px.bar(
            stage, x="amount", y="stage", orientation="h", color="stage",
            color_discrete_map=t.STAGE_COLORS, text=stage["amount"].map(m.money),
        )
        fig.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="%{y}: %{text}<extra></extra>")
        fig.update_yaxes(categoryorder="array", categoryarray=m.OPEN_STAGES[::-1])
        fig.update_xaxes(visible=False, range=[0, float(stage["amount"].max()) * 1.3])
        show(t.style(fig, 300), "exec_stage")
    with right, st.container(border=True):
        section("Open pipeline by month created", "Years kept separate")
        mo = m.monthly_created(f)
        fig = px.bar(
            mo, x="label", y="open_value", color="year",
            color_discrete_map={"2025": t.SLATE, "2026": t.BLUE},
            category_orders={"label": mo["label"].tolist()},
        )
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        fig.update_xaxes(tickangle=-40)
        show(t.style(fig, 300, legend=True), "exec_month")

    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("Open pipeline by region")
        reg = open_f.groupby("region", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        fig = px.bar(reg, x="region", y="amount", text=reg["amount"].map(m.money))
        fig.update_traces(marker_color=t.BLUE, textposition="outside", cliponaxis=False,
                          hovertemplate="%{x}: %{text}<extra></extra>")
        fig.update_yaxes(visible=False)
        show(t.style(fig, 300), "exec_region")
    with right, st.container(border=True):
        section("Pipeline mix by team and stage")
        mix = open_f.groupby(["team", "stage"], as_index=False)["amount"].sum()
        fig = px.bar(
            mix, x="team", y="amount", color="stage", color_discrete_map=t.STAGE_COLORS,
            category_orders={"stage": m.OPEN_STAGES},
        )
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show(t.style(fig, 300, legend=True), "exec_team")

# =====================================================================
# 2. PIPELINE HYGIENE
# =====================================================================
with tabs[1]:
    cards([
        ("Stale deals", f"{k['stale_count']}", f"{m.pct(k['stale_count_pct'])} of open deals", "bad"),
        ("Stale value", m.money(k["stale_value"]), f"{m.pct(k['stale_value_pct'])} of open value", "bad"),
        ("Beyond longest cycle", f"{k['beyond_cycle']}",
         f"{k['beyond_cycle_not_stale']} still log activity", "warn"),
        ("Imputed amounts", f"{k['missing_amount']}", "median-imputed, reported separately", ""),
    ])
    insight(
        f"<b>{k['beyond_cycle']} open deals ({m.money(k['beyond_cycle_value'])})</b> are older than any deal "
        f"has ever taken to close ({longest_cycle} days). <b>{k['beyond_cycle_not_stale']}</b> of them are missed "
        "by the 30-day stale rule because they still log activity, so they need a close-out decision.",
        "warn",
    )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("Where open pipeline is aging", "Open value by age bucket")
        ag = m.aging_buckets(f)
        fig = go.Figure(
            go.Bar(
                x=ag["aging_bucket"].astype(str), y=ag["open_value"],
                marker_color=[t.BLUE] * 4 + [t.AMBER],
                text=ag["open_value"].map(m.money), textposition="outside", cliponaxis=False,
                customdata=ag["open_opportunities"],
                hovertemplate="%{x}<br>%{text} · %{customdata} deals<extra></extra>",
            )
        )
        fig.update_yaxes(visible=False)
        show(t.style(fig, 320), "hyg_aging")
    with right, st.container(border=True):
        section("Stale value by region", "Open deals quiet for 30+ days")
        stale_f = f[f["is_stale"]]
        if stale_f.empty:
            st.info("No stale deals for the current filters.")
        else:
            sr = (
                stale_f.groupby("region", as_index=False)
                .agg(value=("amount", "sum"), deals=("opp_id", "size"))
                .sort_values("value", ascending=False)
            )
            fig = px.bar(sr, x="region", y="value", text=sr["value"].map(m.money), custom_data=["deals"])
            fig.update_traces(marker_color=t.RED, textposition="outside", cliponaxis=False,
                              hovertemplate="%{x}: %{text} · %{customdata[0]} deals<extra></extra>")
            fig.update_yaxes(visible=False)
            show(t.style(fig, 320), "hyg_region")

    with st.container(border=True):
        section("Stale-deal follow-up queue", "Ranked by amount × days since activity (a triage heuristic, not a recovery probability)")
        queue = m.stale_queue(f)
        if queue.empty:
            st.info("No stale deals for the current filters.")
        else:
            st.dataframe(
                queue.head(50), hide_index=True, width="stretch", height=380,
                column_config={
                    "opp_id": "Opp",
                    "account_name": "Account",
                    "rep_name": "Rep",
                    "region": "Region",
                    "product": "Product",
                    "stage": "Stage",
                    "amount": st.column_config.NumberColumn("Amount (USD)", format="localized"),
                    "days_since_activity": st.column_config.ProgressColumn(
                        "Days quiet", format="%d", min_value=0,
                        max_value=int(queue["days_since_activity"].max()),
                    ),
                    "priority_score": st.column_config.NumberColumn("Priority score", format="localized"),
                },
            )
            st.download_button(
                f"Download all {len(queue)} stale deals (CSV)",
                queue.to_csv(index=False).encode("utf-8"),
                file_name="stale_deal_queue.csv", mime="text/csv",
            )

# =====================================================================
# 3. REPS & REGIONS
# =====================================================================
with tabs[2]:
    rt = m.rep_table(f)
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("Win rate by rep", "Bars show 95% Wilson intervals; n = closed deals; dotted line = overall")
        winrate_chart(rt[rt["closed_deals"] > 0], "rep_name", "rep_winrate", k["win_rate"], 560)
    with right, st.container(border=True):
        section("Open pipeline by region, team and rep", "Tile size = open pipeline; click a block to zoom in")
        tm = open_f.groupby(["region", "team", "rep_name"], as_index=False)["amount"].sum()
        fig = px.treemap(
            tm, path=[px.Constant("All regions"), "region", "team", "rep_name"], values="amount",
            color="amount", color_continuous_scale=["#14284F", "#2B5BC4", "#1BA58F"],
        )
        fig.update_traces(root_color="rgba(0,0,0,0)", marker_line_color=t.BG, marker_line_width=2,
                          textfont=dict(color="#FFFFFF"),
                          hovertemplate="%{label}<br>%{value:$,.0f}<extra></extra>")
        fig.update_coloraxes(showscale=False)
        show(t.style(fig, 560), "rep_tree")

    note("Each rep has a small sample, so wide intervals are normal. Treat gaps as review signals, not rankings.")

    with st.container(border=True):
        section("Rep scorecard")
        disp = rt.assign(win_rate_pct=(rt["win_rate"] * 100).round(1))[
            ["rep_name", "region", "team", "open_pipeline", "stale_deals", "closed_deals",
             "win_rate_pct", "missing_amounts", "missing_lead_source"]
        ]
        st.dataframe(
            disp, hide_index=True, width="stretch", height=360,
            column_config={
                "rep_name": "Rep", "region": "Region", "team": "Team",
                "open_pipeline": st.column_config.ProgressColumn(
                    "Open pipeline (USD)", format="localized", min_value=0,
                    max_value=float(max(rt["open_pipeline"].max(), 1)),
                ),
                "stale_deals": st.column_config.NumberColumn("Stale deals"),
                "closed_deals": st.column_config.NumberColumn("Closed deals"),
                "win_rate_pct": st.column_config.NumberColumn("Win rate", format="%.1f%%"),
                "missing_amounts": st.column_config.NumberColumn("Missing amounts"),
                "missing_lead_source": st.column_config.NumberColumn("Missing lead source"),
            },
        )

# =====================================================================
# 4. FUNNEL & SEGMENTS
# =====================================================================
with tabs[3]:
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True, height=590):
        section("Stage funnel", "Deals that ever reached each stage (from stage history)")
        reach = m.stage_reach(history, f["opp_id"])
        fig = go.Figure(
            go.Funnel(
                y=reach["stage"], x=reach["deals"], textinfo="value+percent initial",
                marker=dict(color=[t.STAGE_COLORS[s] for s in reach["stage"]]),
                connector=dict(line=dict(color=t.BORDER, width=1)),
            )
        )
        show(t.style(fig, 470), "funnel")
    with right, st.container(border=True, height=590):
        section("Stage progression to date", "Share of deals that reached a stage and later reached the next")
        prog = m.stage_progression(history, f["opp_id"])
        prog["Step"] = prog["from_stage"] + "  →  " + prog["to_stage"]
        st.dataframe(
            prog[["Step", "at_start", "progressed", "progressed_pct"]],
            hide_index=True, width="stretch",
            column_config={
                "at_start": st.column_config.NumberColumn("Reached stage"),
                "progressed": st.column_config.NumberColumn("Progressed"),
                "progressed_pct": st.column_config.ProgressColumn(
                    "Progressed to date", format="%.1f%%", min_value=0, max_value=100),
            },
        )
        neg_ids = set(history.loc[history["stage"] == "Negotiation", "opp_id"]) & set(f["opp_id"])
        final = f[f["opp_id"].isin(neg_ids)]["stage"].value_counts()
        c1, c2, c3 = st.columns(3, gap="small")
        total_neg = max(len(neg_ids), 1)
        c1.markdown(kpi("Won", f"{int(final.get('Closed Won', 0))}",
                        m.pct(final.get("Closed Won", 0) / total_neg) + " of negotiated", "good"), unsafe_allow_html=True)
        c2.markdown(kpi("Lost", f"{int(final.get('Closed Lost', 0))}",
                        m.pct(final.get("Closed Lost", 0) / total_neg) + " of negotiated", "bad"), unsafe_allow_html=True)
        c3.markdown(kpi("Still open", f"{int(final.get('Negotiation', 0))}",
                        m.pct(final.get("Negotiation", 0) / total_neg) + " of negotiated", "warn"), unsafe_allow_html=True)
        note("Open deals that have not moved yet count as not progressed, so later-stage rates are understated until they resolve.")

    ls = m.win_rate_table(f, "lead_source")
    pr = m.win_rate_table(f, "product")
    known = ls[ls["lead_source"] != "Unknown"]
    if len(known) >= 2:
        hi, lo = known.iloc[0], known.iloc[-1]
        verdict = (
            "The intervals do not overlap, so the gap is larger than sampling noise (in this simulation)."
            if hi["ci_low"] > lo["ci_high"] else "The intervals overlap, so the gap is not distinguishable from noise."
        )
        insight(
            f"<b>{hi['lead_source']}</b> wins {m.pct(hi['win_rate'])} vs <b>{lo['lead_source']}</b> "
            f"{m.pct(lo['win_rate'])}. {verdict} Lead-source and product effects are planted simulation "
            "parameters, shown here to demonstrate the method, not as business evidence."
        )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("Win rate by lead source", "'Unknown' = lead source missing in the CRM")
        winrate_chart(ls, "lead_source", "wr_source", k["win_rate"], 360)
    with right, st.container(border=True):
        section("Win rate by product", "n = closed deals; bars show 95% intervals")
        winrate_chart(pr, "product", "wr_product", k["win_rate"], 360)

# =====================================================================
# 5. DATA QUALITY
# =====================================================================
with tabs[4]:
    cards([
        ("Accounts", f"{int(quality['Accounts Before Cleaning'])} → {int(quality['Accounts After Cleaning'])}",
         f"{int(quality['Duplicate Accounts Merged'])} duplicate records merged", "good"),
        ("Dedup precision / recall", f"{quality['Dedup Precision Pct']:.0f}% / {quality['Dedup Recall Pct']:.0f}%",
         "vs generator ground truth", "good"),
        ("DUNS missing", f"{quality['Pct Missing DUNS Before']:.1f}% → {quality['Pct Missing DUNS After']:.1f}%",
         "flagged for follow-up, never invented", "warn"),
        ("Stage spellings", f"{int(quality['Raw Stage Values Found'])} → {int(quality['Canonical Stages After Cleaning'])}",
         "standardized to canonical stages", "good"),
    ])
    note(
        "The synthetic duplicates are easy variants (case, suffixes, spacing), so 100% means correct on the "
        "injected defects, not a general guarantee. Account-level figures ignore the sidebar filters."
    )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("Validation rules", "Row-level checks run on every build")
        v = data["validation"].copy()
        v["Status"] = v["status"].map({"PASS": "✅ PASS", "REVIEW": "⚠️ REVIEW"})
        v["Rule"] = (v["issue_type"].str.replace("_", " ").str.capitalize()
                     .str.replace(r"\bid\b", "ID", regex=True).str.replace("duns", "DUNS"))
        st.dataframe(
            v[["Rule", "severity", "issue_count", "Status"]], hide_index=True, width="stretch", height=390,
            column_config={"severity": "Severity", "issue_count": st.column_config.NumberColumn("Issues")},
        )
    with right, st.container(border=True):
        section("Data issues by rep", "Stale deals, missing amounts, missing lead source")
        long = rt.melt(
            id_vars="rep_name",
            value_vars=["stale_deals", "missing_amounts", "missing_lead_source"],
            var_name="issue", value_name="count",
        )
        long["issue"] = long["issue"].map({
            "stale_deals": "Stale deals", "missing_amounts": "Missing amount",
            "missing_lead_source": "Missing lead source",
        })
        order = rt.assign(total=rt["stale_deals"] + rt["missing_amounts"] + rt["missing_lead_source"]) \
            .sort_values("total")["rep_name"].tolist()
        fig = px.bar(
            long, x="count", y="rep_name", color="issue", orientation="h",
            color_discrete_map={"Stale deals": t.RED, "Missing amount": t.AMBER, "Missing lead source": t.VIOLET},
            category_orders={"rep_name": order},
        )
        show(t.style(fig, 390, legend=True), "dq_rep")

    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        section("DUNS completeness by industry", "Accounts after cleaning; missing values are flagged, never invented")
        duns = m.duns_by_industry(data["accounts"])
        duns["axis"] = [f"{i}  ({p:.0f}% missing)" for i, p in zip(duns["industry"], duns["missing_pct"])]
        fig = go.Figure()
        fig.add_bar(y=duns["axis"], x=duns["present"], name="Has DUNS", orientation="h",
                    marker_color=t.BLUE, hovertemplate="%{y}: %{x} accounts with DUNS<extra></extra>")
        fig.add_bar(y=duns["axis"], x=duns["missing"], name="Missing DUNS", orientation="h",
                    marker_color=t.AMBER, hovertemplate="%{y}: %{x} accounts missing DUNS<extra></extra>")
        fig.update_layout(barmode="stack")
        fig.update_yaxes(categoryorder="array", categoryarray=duns["axis"].tolist()[::-1], showgrid=False)
        show(t.style(fig, 340, legend=True), "dq_duns")
    with right, st.container(border=True):
        dups = m.merged_duplicates(data["merge_map"], data["accounts"])
        section("Merged duplicate accounts", f"Audit trail: every merge is logged ({int(dups['needs_review'].sum())} flagged for review)")
        st.dataframe(
            dups[["duplicate_record", "merged_into", "match_type"]], hide_index=True, width="stretch", height=340,
            column_config={
                "duplicate_record": "Duplicate record", "merged_into": "Merged into",
                "match_type": "How matched",
            },
        )

    d1, d2 = st.columns(2, gap="small")
    d1.download_button("Download row-level issue log (CSV)", data["issues"].to_csv(index=False).encode("utf-8"),
                       file_name="data_quality_issues.csv", mime="text/csv")
    d2.download_button("Download account merge audit map (CSV)", data["merge_map"].to_csv(index=False).encode("utf-8"),
                       file_name="account_merge_map.csv", mime="text/csv")

# =====================================================================
# 6. ABOUT
# =====================================================================
with tabs[5]:
    with st.container(border=True):
        section("About this project")
        st.markdown(
            "An **audit-first** sales-operations project. A deliberately messy, **synthetic** CRM export "
            "is deduplicated, validated and modeled before any chart is drawn, and every number in this "
            "app is computed from the cleaned tables in the repository.\n\n"
            "**Pipeline:** `generate_data.py` → `clean_data.py` → star schema → DuckDB SQL marts → "
            "tests → this dashboard (and a Power BI report).\n\n"
            "**Deduplication:** names are normalized (case, spacing, punctuation, legal suffixes) and matched "
            "within a country, with a fuzzy fallback and a review band for near-matches. In this synthetic data "
            "all 22 merges were exact after normalization.\n\n"
            "**Synthetic data:** lead-source, product and team effects are planted simulation parameters. "
            "Findings demonstrate the method and are not real-world evidence."
        )
        st.markdown(f"[Source code and README on GitHub]({GITHUB_URL})")
    with st.container(border=True):
        section("Metric definitions")
        dictionary = data["metric_dictionary"].split("\n", 1)[1].lstrip()  # drop the file's H1 title
        st.markdown(dictionary)

st.markdown(
    f'<div class="footer">Synthetic data · Python · pandas · DuckDB · Plotly · Streamlit · '
    f'<a href="{GITHUB_URL}" target="_blank">Source on GitHub</a></div>',
    unsafe_allow_html=True,
)
