"""
StratForge – Intelligent Business Strategy Simulator
Main entry point & home dashboard.
"""

import streamlit as st
from utils.styling import (
    apply_custom_css,
    render_kpi_card,
    render_section_header,
    render_feature_tile,
    format_currency,
    format_percentage,
)
from utils.data_utils import generate_synthetic_data, init_session_state, compute_kpis, get_col, auto_map_columns

# ── Page Config ──
st.set_page_config(
    page_title="StratForge – Strategy Simulator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()
init_session_state()

# ── Auto-load synthetic data on first run ──
if st.session_state.df is None:
    st.session_state.df = generate_synthetic_data()
    st.session_state.data_loaded = True
    st.session_state.data_source = "synthetic"

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.8rem 0 1.2rem 0;">
        <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">🏛️</div>
        <div style="font-size: 1.3rem; font-weight: 800;
                    background: linear-gradient(135deg, #00D4AA, #00B4D8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    letter-spacing: 1px;">
            STRATFORGE
        </div>
        <div style="font-size: 0.68rem; color: #6B7280; letter-spacing: 2px;
                    text-transform: uppercase; margin-top: 0.15rem;">
            Strategy Simulator
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Data source indicator
    if st.session_state.data_loaded:
        source_label = "Built-in Dataset" if st.session_state.data_source == "synthetic" else "Uploaded File"
        st.markdown(f"""
        <div style="background: rgba(0,212,170,0.06); border: 1px solid rgba(0,212,170,0.15);
                    border-radius: 10px; padding: 0.6rem 0.8rem; margin-bottom: 1rem;">
            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;
                        letter-spacing: 1px; margin-bottom: 0.2rem;">Active Data</div>
            <div style="font-size: 0.85rem; color: #00D4AA; font-weight: 600;">
                📊 {source_label}
            </div>
            <div style="font-size: 0.72rem; color: #8B95A8; margin-top: 0.15rem;">
                {len(st.session_state.df)} rows × {len(st.session_state.df.columns)} columns
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.72rem; color: #4B5563; padding: 0.5rem 0;">
        <strong style="color: #6B7280;">Navigate</strong> using the pages above ↑<br/>
        Upload your own data in <strong style="color:#00D4AA;">Data Studio</strong>
    </div>
    """, unsafe_allow_html=True)

# ── Main Content ──
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0 0.5rem 0;">
    <div style="font-size: 2.8rem; font-weight: 900;
                background: linear-gradient(135deg, #00D4AA 0%, #00B4D8 50%, #7C3AED 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 0.5px;">
        StratForge
    </div>
    <div style="font-size: 1.05rem; color: #8B95A8; margin-top: 0.3rem; font-weight: 400;">
        Intelligent Business Strategy Simulator
    </div>
    <div style="font-size: 0.78rem; color: #4B5563; margin-top: 0.5rem; max-width: 600px; margin-left: auto; margin-right: auto;">
        Predict the future, simulate every scenario, quantify risk with Monte Carlo,
        and find optimal decisions — all in one premium dashboard.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── KPI Overview ──
df = st.session_state.df

# Auto-map on first load
if not st.session_state.column_mapping:
    auto_mapping, auto_mkt = auto_map_columns(df)
    st.session_state.column_mapping = auto_mapping
    st.session_state.marketing_columns = auto_mkt

kpis = compute_kpis(df)

# Only show KPI cards for mapped fields
kpi_cards = []
if get_col("revenue"):
    kpi_cards.append(("Total Revenue", format_currency(kpis.get("total_revenue", 0)),
                     f"{kpis.get('revenue_growth', 0):.1f}% growth" if "revenue_growth" in kpis else None,
                     kpis.get("revenue_growth", 0) > 0))
if get_col("profit"):
    kpi_cards.append(("Total Profit", format_currency(kpis.get("total_profit", 0)),
                     f"{kpis.get('avg_profit_margin', 0):.1f}% margin",
                     kpis.get("avg_profit_margin", 0) > 10))
if get_col("customers"):
    kpi_cards.append(("Customer Base", f"{kpis.get('current_customers', 0):,}", None, True))
if get_col("churn"):
    kpi_cards.append(("Avg Churn", f"{kpis.get('avg_churn', 0):.1f}%", "Monthly rate",
                     kpis.get("avg_churn", 5) < 5))
if get_col("satisfaction"):
    kpi_cards.append(("Satisfaction", f"{kpis.get('avg_satisfaction', 0):.1f}/10", None,
                     kpis.get("avg_satisfaction", 0) > 7.5))

if kpi_cards:
    cols = st.columns(len(kpi_cards))
    for col, (title, value, delta, positive) in zip(cols, kpi_cards):
        with col:
            render_kpi_card(title, value, delta, positive)
else:
    st.info("📌 Map your columns in **Data Studio** to see KPI cards here.")

st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

# ── Quick Trend Chart ──
date_col = get_col("date")
rev_col = get_col("revenue")
profit_col = get_col("profit")

if date_col and (rev_col or profit_col):
    render_section_header("📈", "Key Metrics Trend")

    import plotly.graph_objects as go
    from utils.styling import STRATFORGE_TEMPLATE

    fig = go.Figure()
    if rev_col:
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[rev_col],
            name=rev_col.replace("_", " "),
            line=dict(color="#00D4AA", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.08)",
        ))
    if profit_col:
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[profit_col],
            name=profit_col.replace("_", " "),
            line=dict(color="#00B4D8", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(0, 180, 216, 0.06)",
        ))
    fig.update_layout(
        template=STRATFORGE_TEMPLATE,
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="",
        yaxis_title="Amount (₹)",
        margin=dict(l=50, r=20, t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Feature Navigation Tiles ──
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_section_header("🧭", "Explore Modules")

col1, col2, col3, col4, col5 = st.columns(5)

tiles = [
    ("📊", "Data Studio", "Upload data & explore 50+ interactive charts"),
    ("🔮", "Forecasting", "SARIMA & Holt-Winters with What-If scenarios"),
    ("🎲", "Risk Simulation", "Monte Carlo with VaR, fan charts & stress tests"),
    ("⚡", "Optimization", "Budget allocation via linear programming"),
    ("📈", "Executive Report", "Bloomberg-style KPIs & one-click export"),
]

for col, (icon, title, desc) in zip([col1, col2, col3, col4, col5], tiles):
    with col:
        st.markdown(render_feature_tile(icon, title, desc), unsafe_allow_html=True)

# ── Marketing Channel Breakdown ──
mkt_cols = st.session_state.get("marketing_columns", [])
available_mkt = [c for c in mkt_cols if c in df.columns]

if available_mkt and date_col:
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    render_section_header("💰", "Marketing Channel Spend")

    import plotly.graph_objects as go
    from utils.styling import STRATFORGE_TEMPLATE

    fig_mkt = go.Figure()
    colors = ["#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D", "#FF6B6B"]
    for i, col_name in enumerate(available_mkt):
        fig_mkt.add_trace(go.Bar(
            x=df[date_col], y=df[col_name],
            name=col_name.replace("_", " "),
            marker_color=colors[i % len(colors)],
            opacity=0.85,
        ))
    fig_mkt.update_layout(
        template=STRATFORGE_TEMPLATE,
        barmode="stack",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="",
        yaxis_title="Spend (₹)",
        margin=dict(l=50, r=20, t=30, b=30),
    )
    st.plotly_chart(fig_mkt, use_container_width=True)

# ── Footer ──
st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0; border-top: 1px solid rgba(0,212,170,0.08); margin-top: 2rem;">
    <div style="font-size: 0.72rem; color: #4B5563;">
        <strong style="color: #6B7280;">StratForge</strong> · Intelligent Strategy Simulator ·
        100% Free · Zero API Keys · Runs Offline
    </div>
</div>
""", unsafe_allow_html=True)
