"""Pure pandas metric functions for the dashboard (no Streamlit imports, fully testable)."""
from __future__ import annotations

import math

import pandas as pd

STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
OPEN_STAGES = STAGES[:4]
AGING_LABELS = ["0-29 days", "30-59 days", "60-89 days", "90-179 days", "180+ days"]
AGING_BINS = [0, 30, 60, 90, 180, float("inf")]
PROGRESSION_PAIRS = [
    ("Prospecting", "Qualification"),
    ("Qualification", "Proposal"),
    ("Proposal", "Negotiation"),
    ("Negotiation", "Closed Won"),
    ("Negotiation", "Closed Lost"),
]


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return float("nan"), float("nan")
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def kpis(f: pd.DataFrame) -> dict:
    open_ = f[~f["is_closed"]]
    closed = f[f["is_closed"]]
    stale = f[f["is_stale"]]
    open_value = float(open_["amount"].sum())
    return {
        "open_count": len(open_),
        "open_value": open_value,
        "open_value_excl_imputed": float(open_.loc[~open_["amount_missing_flag"], "amount"].sum()),
        "stale_count": len(stale),
        "stale_value": float(stale["amount"].sum()),
        "stale_value_pct": float(stale["amount"].sum()) / open_value if open_value else 0.0,
        "stale_count_pct": len(stale) / len(open_) if len(open_) else 0.0,
        "closed_count": len(closed),
        "won_count": int(closed["is_won"].sum()),
        "win_rate": float(closed["is_won"].mean()) if len(closed) else float("nan"),
        "avg_open_age": float(open_["open_age_days"].mean()) if len(open_) else float("nan"),
        "avg_sales_cycle": float(closed["sales_cycle_days"].mean()) if len(closed) else float("nan"),
        "missing_amount": int(f["amount_missing_flag"].sum()),
        "missing_lead_source": int(f["lead_source_missing_flag"].sum()),
        "beyond_cycle": int(f["beyond_max_cycle_flag"].sum()),
        "beyond_cycle_not_stale": int((f["beyond_max_cycle_flag"] & ~f["is_stale"]).sum()),
        "beyond_cycle_value": float(f.loc[f["beyond_max_cycle_flag"], "amount"].sum()),
    }


def win_rate_table(f: pd.DataFrame, by: str) -> pd.DataFrame:
    closed = f[f["is_closed"]]
    g = (
        closed.groupby(by)
        .agg(closed_deals=("is_won", "size"), won_deals=("is_won", "sum"))
        .reset_index()
    )
    g["won_deals"] = g["won_deals"].astype(int)
    g["win_rate"] = g["won_deals"] / g["closed_deals"]
    ci = [wilson(k, n) for k, n in zip(g["won_deals"], g["closed_deals"])]
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    return g.sort_values("win_rate", ascending=False).reset_index(drop=True)


def stage_progression(history: pd.DataFrame, opp_ids) -> pd.DataFrame:
    """Share of deals that reached a stage and later reached the next (progressed to date)."""
    h = history[history["opp_id"].isin(set(opp_ids))]
    reach = h.groupby("stage")["opp_id"].nunique()
    rows = []
    for a, b in PROGRESSION_PAIRS:
        start, done = int(reach.get(a, 0)), int(reach.get(b, 0))
        rows.append({
            "from_stage": a,
            "to_stage": b,
            "at_start": start,
            "progressed": done,
            "progressed_pct": 100.0 * done / start if start else float("nan"),
        })
    return pd.DataFrame(rows)


def stage_reach(history: pd.DataFrame, opp_ids) -> pd.DataFrame:
    h = history[history["opp_id"].isin(set(opp_ids))]
    reach = h.groupby("stage")["opp_id"].nunique()
    return pd.DataFrame({"stage": OPEN_STAGES, "deals": [int(reach.get(s, 0)) for s in OPEN_STAGES]})


def aging_buckets(f: pd.DataFrame) -> pd.DataFrame:
    o = f[~f["is_closed"]].copy()
    o["aging_bucket"] = pd.cut(
        o["open_age_days"], bins=AGING_BINS, labels=AGING_LABELS, right=False
    )
    g = (
        o.groupby("aging_bucket", observed=False)
        .agg(open_opportunities=("opp_id", "size"), open_value=("amount", "sum"))
        .reset_index()
    )
    return g


def monthly_created(f: pd.DataFrame) -> pd.DataFrame:
    o = f[~f["is_closed"]].copy()
    o["month"] = o["created_date"].dt.to_period("M").dt.to_timestamp()
    g = o.groupby("month", as_index=False).agg(open_value=("amount", "sum"), deals=("opp_id", "size"))
    g["label"] = g["month"].dt.strftime("%b %Y")
    g["year"] = g["month"].dt.year.astype(str)
    return g


def stale_queue(f: pd.DataFrame) -> pd.DataFrame:
    s = f[f["is_stale"]].copy()
    s["priority_score"] = s["amount"] * s["days_since_activity"]
    cols = ["opp_id", "account_name", "rep_name", "region", "product", "stage",
            "amount", "days_since_activity", "priority_score"]
    return s.sort_values("priority_score", ascending=False)[cols].reset_index(drop=True)


def rep_table(f: pd.DataFrame) -> pd.DataFrame:
    d = f.assign(
        open_amount=f["amount"].where(~f["is_closed"], 0.0),
        closed=f["is_closed"].astype(int),
        won=f["is_won"].astype(int),
        stale=f["is_stale"].astype(int),
        miss_amt=f["amount_missing_flag"].astype(int),
        miss_ls=f["lead_source_missing_flag"].astype(int),
    )
    g = d.groupby(["rep_name", "region", "team"], as_index=False).agg(
        opportunities=("opp_id", "size"),
        closed_deals=("closed", "sum"),
        won_deals=("won", "sum"),
        open_pipeline=("open_amount", "sum"),
        stale_deals=("stale", "sum"),
        missing_amounts=("miss_amt", "sum"),
        missing_lead_source=("miss_ls", "sum"),
    )
    g["win_rate"] = g["won_deals"] / g["closed_deals"].where(g["closed_deals"] > 0)
    ci = [wilson(int(k), int(n)) for k, n in zip(g["won_deals"], g["closed_deals"])]
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    return g.sort_values("open_pipeline", ascending=False).reset_index(drop=True)


def duns_by_industry(accounts: pd.DataFrame) -> pd.DataFrame:
    g = (
        accounts.groupby("industry")
        .agg(accounts=("account_id", "size"), missing=("duns_missing_flag", "sum"))
        .reset_index()
    )
    g["missing"] = g["missing"].astype(int)
    g["present"] = g["accounts"] - g["missing"]
    g["missing_pct"] = 100.0 * g["missing"] / g["accounts"]
    return g.sort_values("missing_pct", ascending=False).reset_index(drop=True)


def normalize_name(name: str) -> str:
    """Mirror of clean_data.normalize_name (kept in sync by a test)."""
    import re
    name = str(name).strip().lower()
    name = re.sub(r"[.,]", "", name)
    name = re.sub(r"\s+", " ", name)
    for suffix in [" incorporated", " inc", " llc", " corp", " corporation", " ltd"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()


def merged_duplicates(merge_map: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    """Duplicate records that were merged, with the surviving account and how they matched."""
    dup = merge_map[~merge_map["is_survivor"]]
    names = accounts.set_index("account_id")["account_name"]
    survivor = dup["canonical_account_id"].map(names)
    exact = [normalize_name(a) == normalize_name(b) for a, b in zip(dup["account_name"], survivor)]
    out = pd.DataFrame({
        "duplicate_record": dup["account_name"].values,
        "merged_into": survivor.values,
        "match_type": ["Exact (normalized)" if e else "Fuzzy" for e in exact],
        "needs_review": dup["review_required"].values,
    })
    return out.sort_values(["match_type", "duplicate_record"]).reset_index(drop=True)


def money(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:.2f}M"
    if abs(x) >= 1_000:
        return f"${x / 1_000:.0f}K"
    return f"${x:,.0f}"


def pct(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{100 * x:.{digits}f}%"
