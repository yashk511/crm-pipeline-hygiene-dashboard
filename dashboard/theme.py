"""Visual theme: palette, Plotly styling and the custom CSS for the Streamlit app."""
import plotly.graph_objects as go

BG = "#0B1220"
CARD = "#111A2E"
BORDER = "#1F2A44"
TEXT = "#E6EDF7"
MUTED = "#8A99B5"
GRID = "rgba(138,153,181,0.14)"

BLUE = "#4F8CFF"
TEAL = "#22D3B6"
AMBER = "#F5B942"
RED = "#FF6B6B"
VIOLET = "#9B7BFF"
SLATE = "#5B6B8A"

STAGE_COLORS = {
    "Prospecting": "#2B4C8C",
    "Qualification": "#3B6FD4",
    "Proposal": "#4F8CFF",
    "Negotiation": "#22D3B6",
    "Closed Won": "#22C55E",
    "Closed Lost": "#FF6B6B",
}
COLORWAY = [BLUE, TEAL, AMBER, VIOLET, RED, SLATE]


def style(fig: go.Figure, height: int = 340, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=8, t=44 if legend else 8, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT, size=12),
        colorway=COLORWAY,
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(color=MUTED), title_text=""),
        hoverlabel=dict(bgcolor="#16223B", bordercolor=BORDER, font=dict(color=TEXT)),
        bargap=0.32,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER,
                     tickfont=dict(color=MUTED), title_text="")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)",
                     tickfont=dict(color=MUTED), title_text="")
    return fig


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
.stApp {{
    background:
        radial-gradient(1100px 520px at 8% -8%, rgba(79,140,255,0.16), transparent 60%),
        radial-gradient(900px 480px at 100% 0%, rgba(34,211,182,0.10), transparent 55%),
        {BG};
}}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}

/* sidebar */
section[data-testid="stSidebar"] {{
    background: #0A101D;
    border-right: 1px solid {BORDER};
}}
.brand {{ display:flex; align-items:center; gap:10px; margin: 4px 0 18px 0; }}
.brand-badge {{
    width: 34px; height: 34px; border-radius: 10px; display:flex; align-items:center;
    justify-content:center; font-size: 18px;
    background: linear-gradient(135deg, {BLUE}, {TEAL});
}}
.brand-text {{ font-weight: 700; letter-spacing: .2px; line-height: 1.15; }}
.brand-sub {{ color: {MUTED}; font-size: 11px; font-weight: 500; }}

/* hero */
.hero {{
    display:flex; justify-content:space-between; align-items:flex-end; gap: 24px; flex-wrap: wrap;
    padding: 26px 30px; margin-bottom: 18px; border-radius: 18px;
    background: linear-gradient(135deg, rgba(79,140,255,0.18), rgba(34,211,182,0.07) 55%, rgba(17,26,46,0.9));
    border: 1px solid {BORDER};
}}
.eyebrow {{ color: {TEAL}; font-size: 11px; font-weight: 700; letter-spacing: 1.6px; text-transform: uppercase; }}
.hero h1 {{ margin: 4px 0 2px 0; font-size: 2.05rem; font-weight: 800; letter-spacing: -.5px; padding: 0; }}
.hero p {{ margin: 0; color: {MUTED}; font-size: .95rem; }}
.chips {{ display:flex; gap: 8px; flex-wrap: wrap; }}
.chip {{
    padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: rgba(17,26,46,0.85); border: 1px solid {BORDER}; color: {TEXT};
}}
.chip.warn {{ color: {AMBER}; border-color: rgba(245,185,66,0.45); }}
.chip a {{ color: {BLUE}; text-decoration: none; }}

/* KPI cards */
.kpi {{
    background: linear-gradient(180deg, rgba(23,34,58,0.95), {CARD});
    border: 1px solid {BORDER}; border-radius: 16px; padding: 16px 18px; min-height: 152px;
    transition: transform .15s ease, border-color .15s ease;
}}
.kpi:hover {{ transform: translateY(-2px); border-color: rgba(79,140,255,0.55); }}
.kpi-label {{ color: {MUTED}; font-size: 11px; font-weight: 600; letter-spacing: .9px; text-transform: uppercase; }}
.kpi-value {{ font-size: 1.85rem; font-weight: 800; letter-spacing: -.6px; margin: 4px 0 2px 0; }}
.kpi-sub {{ font-size: 12px; font-weight: 500; color: {MUTED}; }}
.kpi-sub.good {{ color: #4ADE80; }}
.kpi-sub.bad {{ color: {RED}; }}
.kpi-sub.warn {{ color: {AMBER}; }}

/* sections */
.sec {{ display:flex; align-items:center; gap:10px; margin: 6px 0 2px 0; font-weight: 700; font-size: 1.02rem; }}
.sec::before {{ content:""; width: 4px; height: 18px; border-radius: 4px; background: linear-gradient({BLUE}, {TEAL}); }}
.sec-sub {{ color: {MUTED}; font-size: 12.5px; margin: 0 0 6px 14px; }}
.insight {{
    border-left: 3px solid {BLUE}; background: rgba(79,140,255,0.08);
    padding: 12px 16px; border-radius: 0 12px 12px 0; margin: 14px 0 18px 0; font-size: .95rem;
}}
.insight.warn {{ border-left-color: {AMBER}; background: rgba(245,185,66,0.08); }}
.note {{ color: {MUTED}; font-size: 12px; margin-top: 6px; }}

/* tabs */
div[data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {BORDER}; }}
button[data-baseweb="tab"] {{
    background: transparent; border-radius: 10px 10px 0 0; padding: 10px 16px;
    font-weight: 600; color: {MUTED};
}}
button[data-baseweb="tab"][aria-selected="true"] {{ color: {TEXT}; background: rgba(79,140,255,0.10); }}
div[data-baseweb="tab-highlight"] {{ background: linear-gradient(90deg, {BLUE}, {TEAL}); height: 3px; }}

/* remove the browser focus ring Streamlit draws around the active tab panel */
div[data-baseweb="tab-panel"], [role="tabpanel"] {{ outline: none !important; box-shadow: none !important; }}
[role="tabpanel"]:focus, [role="tabpanel"]:focus-visible {{ outline: none !important; }}
button[data-baseweb="tab"]:focus, button[data-baseweb="tab"]:focus-visible {{ outline: none !important; box-shadow: none !important; }}

/* markdown tables (metric dictionary) */
.stMarkdown table {{ width: 100%; font-size: 13px; border-collapse: collapse; }}
.stMarkdown th {{ color: {MUTED}; font-size: 11px; letter-spacing: .8px; text-transform: uppercase; text-align: left; }}
.stMarkdown th, .stMarkdown td {{ padding: 9px 12px; border-bottom: 1px solid {BORDER}; vertical-align: top; }}

/* bordered containers act as chart cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 16px; border-color: {BORDER}; background: rgba(17,26,46,0.55);
}}
div[data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
.stDownloadButton button {{
    border-radius: 10px; border: 1px solid {BORDER}; background: {CARD}; font-weight: 600;
}}
.stDownloadButton button:hover {{ border-color: {BLUE}; color: {BLUE}; }}
.footer {{ color: {MUTED}; font-size: 12px; text-align:center; margin-top: 28px; }}
.footer a {{ color: {BLUE}; text-decoration: none; }}
</style>
"""
