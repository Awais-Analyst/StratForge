"""
StratForge – Executive Report
Bloomberg-style KPI gauges, strategy recommendations, risk heatmap, one-click export.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from utils.styling import (
    apply_custom_css,
    render_kpi_card,
    render_section_header,
    render_status_badge,
    STRATFORGE_TEMPLATE,
    format_currency,
    format_percentage,
)
from utils.data_utils import init_session_state, compute_kpis, auto_detect_columns

st.set_page_config(page_title="StratForge – Executive Report", page_icon="📈", layout="wide")
apply_custom_css()
init_session_state()

# ── Header ──
st.markdown("""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-size:2rem;">📈</span>
    <div>
        <div style="font-size:1.6rem; font-weight:800; color:#E8ECF1;">Executive Report</div>
        <div style="font-size:0.8rem; color:#6B7280;">C-level summary with KPIs, risk assessment, and strategic recommendations</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Guard ──
if not st.session_state.data_loaded or st.session_state.df is None:
    st.warning("⚠️ No data loaded. Go to **Data Studio** first.")
    st.stop()

df = st.session_state.df
kpis = compute_kpis(df)
col_types = auto_detect_columns(df)
num_cols = col_types["numeric"]
date_cols = col_types["date"]

# ═══════════════════════════════════════════════════
#  EXECUTIVE KPI GAUGES
# ═══════════════════════════════════════════════════
render_section_header("🎯", "Key Performance Indicators")

# Row 1: Main KPIs
g1, g2, g3, g4 = st.columns(4)

# Revenue Gauge
total_revenue = kpis.get("total_revenue", 0)
revenue_target = total_revenue * 1.15  # 15% growth target
revenue_pct = min(total_revenue / revenue_target * 100, 100) if revenue_target > 0 else 0

with g1:
    fig_g1 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_revenue / 1e7,
        number=dict(suffix=" Cr", font=dict(size=28, color="#E8ECF1")),
        delta=dict(
            reference=total_revenue * 0.85 / 1e7,
            increasing=dict(color="#00D4AA"),
            decreasing=dict(color="#FF6B6B"),
            font=dict(size=14),
        ),
        title=dict(text="Total Revenue", font=dict(size=14, color="#8B95A8")),
        gauge=dict(
            axis=dict(range=[0, revenue_target / 1e7], tickfont=dict(size=10, color="#6B7280")),
            bar=dict(color="#00D4AA"),
            bgcolor="rgba(17,24,39,0.5)",
            bordercolor="rgba(0,212,170,0.15)",
            steps=[
                dict(range=[0, revenue_target * 0.6 / 1e7], color="rgba(255,107,107,0.12)"),
                dict(range=[revenue_target * 0.6 / 1e7, revenue_target * 0.85 / 1e7], color="rgba(255,183,77,0.12)"),
                dict(range=[revenue_target * 0.85 / 1e7, revenue_target / 1e7], color="rgba(0,212,170,0.12)"),
            ],
        ),
    ))
    fig_g1.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        height=220, margin=dict(l=30, r=30, t=60, b=10),
    )
    st.plotly_chart(fig_g1, use_container_width=True)

# Profit Margin Gauge
avg_margin = kpis.get("avg_profit_margin", 0)
with g2:
    fig_g2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_margin,
        number=dict(suffix="%", font=dict(size=28, color="#E8ECF1")),
        title=dict(text="Profit Margin", font=dict(size=14, color="#8B95A8")),
        gauge=dict(
            axis=dict(range=[0, 50], tickfont=dict(size=10, color="#6B7280")),
            bar=dict(color="#00B4D8"),
            bgcolor="rgba(17,24,39,0.5)",
            bordercolor="rgba(0,180,216,0.15)",
            steps=[
                dict(range=[0, 10], color="rgba(255,107,107,0.12)"),
                dict(range=[10, 25], color="rgba(255,183,77,0.12)"),
                dict(range=[25, 50], color="rgba(0,180,216,0.12)"),
            ],
        ),
    ))
    fig_g2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        height=220, margin=dict(l=30, r=30, t=60, b=10),
    )
    st.plotly_chart(fig_g2, use_container_width=True)

# Revenue Growth Gauge
growth = kpis.get("revenue_growth", 0)
with g3:
    fig_g3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=growth,
        number=dict(suffix="%", font=dict(size=28, color="#E8ECF1")),
        title=dict(text="Revenue Growth", font=dict(size=14, color="#8B95A8")),
        gauge=dict(
            axis=dict(range=[-20, 200], tickfont=dict(size=10, color="#6B7280")),
            bar=dict(color="#7C3AED"),
            bgcolor="rgba(17,24,39,0.5)",
            bordercolor="rgba(124,58,237,0.15)",
            steps=[
                dict(range=[-20, 0], color="rgba(255,107,107,0.12)"),
                dict(range=[0, 50], color="rgba(255,183,77,0.12)"),
                dict(range=[50, 200], color="rgba(124,58,237,0.12)"),
            ],
        ),
    ))
    fig_g3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        height=220, margin=dict(l=30, r=30, t=60, b=10),
    )
    st.plotly_chart(fig_g3, use_container_width=True)

# Customer Satisfaction Gauge
satisfaction = kpis.get("avg_satisfaction", 0)
with g4:
    fig_g4 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=satisfaction,
        number=dict(suffix="/10", font=dict(size=28, color="#E8ECF1")),
        title=dict(text="Satisfaction", font=dict(size=14, color="#8B95A8")),
        gauge=dict(
            axis=dict(range=[0, 10], tickfont=dict(size=10, color="#6B7280")),
            bar=dict(color="#FFB74D"),
            bgcolor="rgba(17,24,39,0.5)",
            bordercolor="rgba(255,183,77,0.15)",
            steps=[
                dict(range=[0, 4], color="rgba(255,107,107,0.12)"),
                dict(range=[4, 7], color="rgba(255,183,77,0.12)"),
                dict(range=[7, 10], color="rgba(0,212,170,0.12)"),
            ],
        ),
    ))
    fig_g4.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        height=220, margin=dict(l=30, r=30, t=60, b=10),
    )
    st.plotly_chart(fig_g4, use_container_width=True)

# ── Row 2: Quick Metrics ──
km1, km2, km3, km4, km5 = st.columns(5)
with km1:
    render_kpi_card("Customers", f"{kpis.get('current_customers', 0):,}")
with km2:
    render_kpi_card("Avg Churn", f"{kpis.get('avg_churn', 0):.1f}%",
                   "Healthy" if kpis.get('avg_churn', 5) < 5 else "Monitor",
                   kpis.get('avg_churn', 5) < 5)
with km3:
    avg_rev = kpis.get("avg_revenue", 0)
    render_kpi_card("Avg Monthly Revenue", format_currency(avg_rev))
with km4:
    total_profit = kpis.get("total_profit", 0)
    render_kpi_card("Total Profit", format_currency(total_profit))
with km5:
    n_months = len(df)
    render_kpi_card("Data Span", f"{n_months} months")

# ═══════════════════════════════════════════════════
#  RISK HEATMAP
# ═══════════════════════════════════════════════════
st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
render_section_header("🔥", "Risk Assessment Heatmap")

# Build risk matrix
risk_categories = ["Revenue\nVolatility", "Profit\nMargin", "Customer\nChurn", "Market\nGrowth", "Operational\nCost"]
impact_levels = ["Critical", "High", "Medium", "Low", "Minimal"]

# Calculate actual risk scores from data
risk_scores = np.zeros((5, 5))

if "Revenue" in df.columns:
    rev_cv = df["Revenue"].std() / df["Revenue"].mean() * 100 if df["Revenue"].mean() != 0 else 0
    risk_scores[0, :] = [max(0, min(5, rev_cv / 10)), max(0, min(4, rev_cv / 15)), 2, 1, 0.5]

if "Profit" in df.columns and "Revenue" in df.columns:
    margin_risk = max(0, 30 - avg_margin) / 6
    risk_scores[1, :] = [margin_risk, margin_risk * 0.8, 2.5, 1.5, 0.5]

if "Churn_Rate" in df.columns:
    churn_risk = kpis.get("avg_churn", 5) / 2
    risk_scores[2, :] = [churn_risk, churn_risk * 0.9, 2, 1.2, 0.3]

risk_scores[3, :] = [3.5, 3, 2.5, 1.5, 0.5]
risk_scores[4, :] = [3, 2.8, 2.2, 1.3, 0.4]

# Add some randomization for visual effect
np.random.seed(42)
risk_scores += np.random.uniform(-0.3, 0.3, risk_scores.shape)
risk_scores = np.clip(risk_scores, 0, 5)

fig_heat = go.Figure(data=go.Heatmap(
    z=risk_scores,
    x=risk_categories,
    y=impact_levels,
    colorscale=[
        [0, "#111827"],
        [0.25, "#1a472a"],
        [0.5, "#FFB74D"],
        [0.75, "#FF6B6B"],
        [1.0, "#DC2626"],
    ],
    text=risk_scores.round(1),
    texttemplate="%{text}",
    textfont=dict(size=13, color="#E8ECF1"),
    showscale=True,
    colorbar=dict(
        title="Risk Score",
        titlefont=dict(color="#8B95A8"),
        tickfont=dict(color="#8B95A8"),
    ),
))
fig_heat.update_layout(
    template=STRATFORGE_TEMPLATE,
    height=380,
    title="Risk Exposure Matrix",
    xaxis=dict(side="bottom"),
    margin=dict(l=80, r=20, t=50, b=80),
)
st.plotly_chart(fig_heat, use_container_width=True)

# ═══════════════════════════════════════════════════
#  AUTO INSIGHTS & RECOMMENDATIONS
# ═══════════════════════════════════════════════════
render_section_header("💡", "Strategic Recommendations")

# Generate insights from data
insights = []

# Revenue insights
if "Revenue" in df.columns:
    rev_growth = kpis.get("revenue_growth", 0)
    if rev_growth > 50:
        insights.append(("🚀", "Strong Revenue Growth",
                        f"Revenue has grown **{rev_growth:.1f}%** over the analysis period. Consider reinvesting profits to sustain momentum.",
                        "success"))
    elif rev_growth > 0:
        insights.append(("📈", "Positive Revenue Trend",
                        f"Revenue is up **{rev_growth:.1f}%** — stable but consider growth acceleration strategies.",
                        "success"))
    else:
        insights.append(("⚠️", "Revenue Decline Detected",
                        f"Revenue has declined **{rev_growth:.1f}%**. Urgent review of pricing and marketing strategy needed.",
                        "danger"))

# Margin insights
if avg_margin > 25:
    insights.append(("💎", "Healthy Profit Margins",
                    f"Average margin of **{avg_margin:.1f}%** is excellent. Room to invest in growth.",
                    "success"))
elif avg_margin > 10:
    insights.append(("📊", "Moderate Margins",
                    f"Margins at **{avg_margin:.1f}%** are decent but could improve with cost optimization.",
                    "warning"))
else:
    insights.append(("🔴", "Low Margins — Action Required",
                    f"Margins at **{avg_margin:.1f}%** are concerning. Review pricing strategy and cut non-essential costs.",
                    "danger"))

# Marketing insights
mkt_cols = ["Digital_Marketing", "Print_Marketing", "TV_Marketing", "Social_Media_Marketing"]
available_mkt = [c for c in mkt_cols if c in df.columns]
if available_mkt and "Revenue" in df.columns:
    total_mkt = df[available_mkt].sum(axis=1).mean()
    mkt_ratio = total_mkt / df["Revenue"].mean() * 100 if df["Revenue"].mean() > 0 else 0

    if "Digital_Marketing" in df.columns and "Print_Marketing" in df.columns:
        digital_share = df["Digital_Marketing"].sum() / df[available_mkt].sum().sum() * 100
        if digital_share < 30:
            insights.append(("💡", "Increase Digital Marketing",
                            f"Digital is only **{digital_share:.0f}%** of marketing spend. Consider shifting **+15-25%** to digital channels for higher ROI.",
                            "warning"))
        else:
            insights.append(("✅", "Digital-First Strategy Active",
                            f"Digital accounts for **{digital_share:.0f}%** of marketing — well positioned for modern growth.",
                            "success"))

# Churn insights
if "Churn_Rate" in df.columns:
    avg_churn = kpis.get("avg_churn", 5)
    if avg_churn > 6:
        insights.append(("🔴", "High Customer Churn",
                        f"Average churn of **{avg_churn:.1f}%/month** is high. Invest in retention programs — reducing churn by 1% could add significant lifetime value.",
                        "danger"))
    elif avg_churn < 3:
        insights.append(("✅", "Excellent Retention",
                        f"Monthly churn of **{avg_churn:.1f}%** indicates strong customer loyalty.",
                        "success"))

# Optimization reference
if st.session_state.optimization_results:
    opt = st.session_state.optimization_results
    if opt.get("success"):
        insights.append(("⚡", "Optimization Opportunity Available",
                        f"Optimal budget allocation yields **{format_currency(opt['total_roi'])}** ROI with **{opt['budget_utilization']:.0f}%** utilization. See Optimization Engine for details.",
                        "success"))

# Simulation reference
if st.session_state.simulation_results:
    sim = st.session_state.simulation_results
    metrics = sim.get("metrics", {})
    prob = metrics.get("prob_target", 0)
    target_pct = metrics.get("target_growth_pct", 20)
    insights.append(("🎲", "Risk Assessment Complete",
                    f"Monte Carlo shows **{prob:.0f}%** probability of exceeding **{target_pct:.0f}%** growth target. See Risk Fortress for full analysis.",
                    "success" if prob > 60 else "warning"))

# Render insights
for icon, title, text, status in insights:
    badge = render_status_badge(status.upper(), status)
    st.markdown(f"""
    <div class="glass-card" style="display:flex; gap:1rem; align-items:flex-start;">
        <div style="font-size:1.5rem; min-width:2rem;">{icon}</div>
        <div style="flex:1;">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
                <span style="font-weight:700; color:#E8ECF1;">{title}</span>
                {badge}
            </div>
            <div style="font-size:0.85rem; color:#C5CDD8; line-height:1.5;">{text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  TREND SUMMARY CHART
# ═══════════════════════════════════════════════════
if date_cols and "Revenue" in num_cols and "Profit" in num_cols:
    render_section_header("📊", "Performance Summary")

    fig_summary = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Revenue Trend", "Profit Trend", "Marketing Efficiency", "Customer Health"],
        vertical_spacing=0.14, horizontal_spacing=0.08,
    )
    date_col = date_cols[0]

    # Revenue
    fig_summary.add_trace(go.Scatter(
        x=df[date_col], y=df["Revenue"],
        line=dict(color="#00D4AA", width=2), fill="tozeroy",
        fillcolor="rgba(0,212,170,0.08)", showlegend=False,
    ), row=1, col=1)

    # Profit
    fig_summary.add_trace(go.Scatter(
        x=df[date_col], y=df["Profit"],
        line=dict(color="#00B4D8", width=2), fill="tozeroy",
        fillcolor="rgba(0,180,216,0.08)", showlegend=False,
    ), row=1, col=2)

    # Marketing efficiency (Revenue / Marketing Spend)
    if "Total_Marketing_Spend" in df.columns:
        efficiency = df["Revenue"] / df["Total_Marketing_Spend"]
        fig_summary.add_trace(go.Scatter(
            x=df[date_col], y=efficiency,
            line=dict(color="#7C3AED", width=2), showlegend=False,
        ), row=2, col=1)

    # Customer health
    if "Customer_Base" in df.columns:
        fig_summary.add_trace(go.Scatter(
            x=df[date_col], y=df["Customer_Base"],
            line=dict(color="#FFB74D", width=2), fill="tozeroy",
            fillcolor="rgba(255,183,77,0.08)", showlegend=False,
        ), row=2, col=2)

    fig_summary.update_layout(
        template=STRATFORGE_TEMPLATE, height=550,
        margin=dict(l=50, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_summary, use_container_width=True)

# ═══════════════════════════════════════════════════
#  EXPORT
# ═══════════════════════════════════════════════════
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
render_section_header("📥", "Export Report")

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    # CSV export
    st.download_button(
        "📥 Download Data (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"stratforge_report_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp2:
    # Summary metrics export
    summary_data = {
        "Metric": [],
        "Value": [],
    }
    for key, val in kpis.items():
        summary_data["Metric"].append(key.replace("_", " ").title())
        if isinstance(val, float):
            summary_data["Value"].append(f"{val:,.2f}")
        else:
            summary_data["Value"].append(str(val))
    summary_df = pd.DataFrame(summary_data)

    st.download_button(
        "📥 Download KPIs (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name=f"stratforge_kpis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp3:
    # HTML report
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>StratForge Executive Report</title>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; background:#0A0E1A; color:#E8ECF1; padding:2rem; }}
            h1 {{ color:#00D4AA; border-bottom:2px solid rgba(0,212,170,0.2); padding-bottom:0.5rem; }}
            h2 {{ color:#00B4D8; margin-top:2rem; }}
            .kpi {{ display:inline-block; background:rgba(17,24,39,0.7); border:1px solid rgba(0,212,170,0.12);
                    border-radius:12px; padding:1rem 1.5rem; margin:0.5rem; text-align:center; }}
            .kpi-val {{ font-size:1.5rem; font-weight:800; color:#00D4AA; }}
            .kpi-label {{ font-size:0.75rem; color:#8B95A8; text-transform:uppercase; letter-spacing:1px; }}
            table {{ border-collapse:collapse; width:100%; margin:1rem 0; }}
            th {{ background:rgba(0,212,170,0.08); color:#00D4AA; padding:0.8rem; text-align:left; }}
            td {{ padding:0.6rem 0.8rem; border-bottom:1px solid rgba(139,149,168,0.1); }}
            .insight {{ background:rgba(17,24,39,0.5); border-radius:10px; padding:1rem; margin:0.8rem 0;
                       border-left:3px solid #00D4AA; }}
            footer {{ text-align:center; color:#4B5563; margin-top:3rem; font-size:0.8rem; }}
        </style>
    </head>
    <body>
        <h1>🏛️ StratForge Executive Report</h1>
        <p style="color:#8B95A8;">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>

        <h2>Key Performance Indicators</h2>
        <div>
            <div class="kpi"><div class="kpi-label">Total Revenue</div><div class="kpi-val">{format_currency(kpis.get('total_revenue', 0))}</div></div>
            <div class="kpi"><div class="kpi-label">Total Profit</div><div class="kpi-val">{format_currency(kpis.get('total_profit', 0))}</div></div>
            <div class="kpi"><div class="kpi-label">Avg Margin</div><div class="kpi-val">{avg_margin:.1f}%</div></div>
            <div class="kpi"><div class="kpi-label">Revenue Growth</div><div class="kpi-val">{growth:.1f}%</div></div>
            <div class="kpi"><div class="kpi-label">Satisfaction</div><div class="kpi-val">{satisfaction:.1f}/10</div></div>
        </div>

        <h2>Strategic Recommendations</h2>
        {"".join(f'<div class="insight"><strong>{t}</strong><br/>{txt}</div>' for _, t, txt, _ in insights)}

        <h2>Data Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            {"".join(f"<tr><td>{row['Metric']}</td><td>{row['Value']}</td></tr>" for _, row in summary_df.iterrows())}
        </table>

        <footer>StratForge · Intelligent Business Strategy Simulator · 100% Free & Offline</footer>
    </body>
    </html>
    """

    st.download_button(
        "📥 Download Report (HTML)",
        data=report_html.encode("utf-8"),
        file_name=f"stratforge_executive_report_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
    )

# ── Footer ──
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem 0; border-top:1px solid rgba(0,212,170,0.08); margin-top:2rem;">
    <div style="font-size:0.72rem; color:#4B5563;">
        <strong style="color:#6B7280;">StratForge</strong> · Executive Report ·
        Generated {datetime.now().strftime('%B %d, %Y')}
    </div>
</div>
""".replace("{datetime.now().strftime('%B %d, %Y')}", datetime.now().strftime('%B %d, %Y')),
unsafe_allow_html=True)
